/* flask-basecoat runtime core.
   Server-rendered shadcn markup carries Radix's data-state contract; this core gives it behaviour:
   component registration and lazy init, open/close state with aria sync, floating positioning,
   dismiss-on-outside/escape layers, focus trapping and roving focus, and a tiny event bus.
   Component modules in ./components/*.js register themselves with FlaskBasecoat.register(). */
(function (global) {
  'use strict';

  const registry = new Map();
  const initialized = new WeakMap();
  const layers = []; // stack of open dismissable layers: {content, onDismiss, trigger, modal}

  function qs(root, sel) { return root.querySelector(sel); }
  function qsa(root, sel) { return Array.from(root.querySelectorAll(sel)); }

  /* ---- state ---- */
  function setState(el, state) {
    if (!el) return;
    el.setAttribute('data-state', state);
  }
  function isOpen(el) { return el && el.getAttribute('data-state') === 'open'; }

  /* ---- pairing: a content element belongs to the nearest unclaimed trigger before it in document order ---- */
  function pairWith(content, selector, opts) {
    opts = opts || {};
    if (opts.adjacent) {
      const prev = content.previousElementSibling;
      return prev && prev.matches(selector) ? prev : null;
    }
    const candidates = qsa(document, selector).filter((el) => !el.fbPaired && !content.contains(el) && (el.compareDocumentPosition(content) & Node.DOCUMENT_POSITION_FOLLOWING));
    const trigger = candidates[candidates.length - 1] || null;
    if (trigger) trigger.fbPaired = content;
    return trigger;
  }

  /* ---- ids ---- */
  let counter = 0;
  function ensureId(el, prefix) {
    if (!el.id) el.id = `${prefix || 'fb'}-${(++counter).toString(36)}`;
    return el.id;
  }

  /* ---- floating positioning (fixed coordinates, flip when overflowing) ---- */
  function float(anchor, content, opts) {
    opts = Object.assign({ side: 'bottom', align: 'start', sideOffset: 4, alignOffset: 0 }, opts || {});
    content.setAttribute('data-floating', '');
    const prevDisplay = content.style.display;
    content.style.display = 'block';
    content.style.visibility = 'hidden';
    const a = anchor.getBoundingClientRect();
    const c = content.getBoundingClientRect();
    const vw = document.documentElement.clientWidth;
    const vh = document.documentElement.clientHeight;
    let side = opts.side;
    const fits = {
      bottom: a.bottom + opts.sideOffset + c.height <= vh,
      top: a.top - opts.sideOffset - c.height >= 0,
      right: a.right + opts.sideOffset + c.width <= vw,
      left: a.left - opts.sideOffset - c.width >= 0,
    };
    const opposite = { bottom: 'top', top: 'bottom', left: 'right', right: 'left' };
    if (!fits[side] && fits[opposite[side]]) side = opposite[side];
    let x = 0, y = 0;
    if (side === 'bottom' || side === 'top') {
      y = side === 'bottom' ? a.bottom + opts.sideOffset : a.top - opts.sideOffset - c.height;
      if (opts.align === 'start') x = a.left + opts.alignOffset;
      else if (opts.align === 'end') x = a.right - c.width - opts.alignOffset;
      else x = a.left + a.width / 2 - c.width / 2;
    } else {
      x = side === 'right' ? a.right + opts.sideOffset : a.left - opts.sideOffset - c.width;
      if (opts.align === 'start') y = a.top + opts.alignOffset;
      else if (opts.align === 'end') y = a.bottom - c.height - opts.alignOffset;
      else y = a.top + a.height / 2 - c.height / 2;
    }
    x = Math.max(8, Math.min(x, vw - c.width - 8));
    y = Math.max(8, Math.min(y, vh - c.height - 8));
    content.style.transform = `translate(${Math.round(x)}px, ${Math.round(y)}px)`;
    content.style.setProperty('--radix-popper-transform-origin', side === 'bottom' ? 'top' : side === 'top' ? 'bottom' : side === 'left' ? 'right' : 'left');
    content.style.visibility = '';
    content.style.display = prevDisplay;
    content.setAttribute('data-side', side);
    content.setAttribute('data-align', opts.align);
    // Radix exposes the trigger width and available height as CSS variables; components use them.
    const varName = content.getAttribute('data-popper-var') || 'popper';
    content.style.setProperty(`--radix-${varName}-trigger-width`, `${a.width}px`);
    content.style.setProperty(`--radix-${varName}-content-available-height`, `${Math.max(0, (side === 'top' ? a.top : vh - a.bottom) - opts.sideOffset - 8)}px`);
    content.style.setProperty(`--radix-${varName}-content-transform-origin`, content.style.getPropertyValue('--radix-popper-transform-origin'));
    return side;
  }

  /* ---- dismissable layers ---- */
  function pushLayer(layer) {
    layers.push(layer);
    if (layers.length === 1) {
      document.addEventListener('pointerdown', onPointerDown, true);
      document.addEventListener('keydown', onKeyDown, true);
      window.addEventListener('resize', onReposition);
      window.addEventListener('scroll', onReposition, true);
    }
  }
  function removeLayer(layer) {
    const i = layers.indexOf(layer);
    if (i >= 0) layers.splice(i, 1);
    if (!layers.length) {
      document.removeEventListener('pointerdown', onPointerDown, true);
      document.removeEventListener('keydown', onKeyDown, true);
      window.removeEventListener('resize', onReposition);
      window.removeEventListener('scroll', onReposition, true);
    }
  }
  function onPointerDown(e) {
    const top = layers[layers.length - 1];
    if (!top) return;
    const inside = (top.content && top.content.contains(e.target)) || (top.trigger && top.trigger.contains(e.target)) || (top.extra && top.extra.some((n) => n.contains(e.target)));
    if (!inside) {
      if (top.modal && top.content && !top.content.contains(e.target)) { e.preventDefault(); }
      top.onDismiss('outside', e);
    }
  }
  function onKeyDown(e) {
    const top = layers[layers.length - 1];
    if (top && e.key === 'Escape') { e.stopPropagation(); top.onDismiss('escape', e); }
  }
  function onReposition() {
    layers.forEach((l) => l.reposition && l.reposition());
  }

  /* ---- focus ---- */
  const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]):not([type=hidden]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"]):not([disabled]),[contenteditable]';
  function focusables(root) { return qsa(root, FOCUSABLE).filter((el) => el.offsetParent !== null || el === document.activeElement); }
  function trapFocus(container) {
    function handler(e) {
      if (e.key !== 'Tab') return;
      const list = focusables(container);
      if (!list.length) { e.preventDefault(); container.focus(); return; }
      const first = list[0], last = list[list.length - 1];
      if (e.shiftKey && (document.activeElement === first || !container.contains(document.activeElement))) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
    container.addEventListener('keydown', handler);
    return () => container.removeEventListener('keydown', handler);
  }
  function focusFirst(container, preferSelector) {
    const target = (preferSelector && qs(container, preferSelector)) || focusables(container)[0] || container;
    if (target && !container.hasAttribute('tabindex') && target === container) container.setAttribute('tabindex', '-1');
    target && target.focus({ preventScroll: true });
  }

  /* roving focus for menus, tabs, radio groups, toggle groups */
  function roving(items, opts) {
    opts = Object.assign({ loop: true, orientation: 'vertical', typeahead: true }, opts || {});
    let typed = '', typedTimer = 0;
    return function onKey(e) {
      const enabled = items().filter((i) => !i.hasAttribute('disabled') && i.getAttribute('aria-disabled') !== 'true' && i.getAttribute('data-disabled') == null);
      if (!enabled.length) return false;
      const idx = enabled.indexOf(document.activeElement);
      const next = (opts.orientation === 'horizontal') ? ['ArrowRight'] : ['ArrowDown'];
      const prev = (opts.orientation === 'horizontal') ? ['ArrowLeft'] : ['ArrowUp'];
      if (opts.orientation === 'both') { next.push('ArrowRight', 'ArrowDown'); prev.push('ArrowLeft', 'ArrowUp'); }
      let target = null;
      if (next.includes(e.key)) target = enabled[idx < 0 ? 0 : (idx + 1 >= enabled.length ? (opts.loop ? 0 : idx) : idx + 1)];
      else if (prev.includes(e.key)) target = enabled[idx < 0 ? enabled.length - 1 : (idx - 1 < 0 ? (opts.loop ? enabled.length - 1 : 0) : idx - 1)];
      else if (e.key === 'Home') target = enabled[0];
      else if (e.key === 'End') target = enabled[enabled.length - 1];
      else if (opts.typeahead && e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey && e.key !== ' ') {
        typed += e.key.toLowerCase();
        clearTimeout(typedTimer);
        typedTimer = setTimeout(() => { typed = ''; }, 600);
        const start = idx + 1;
        const ordered = enabled.slice(start).concat(enabled.slice(0, start));
        target = ordered.find((i) => (i.textContent || '').trim().toLowerCase().startsWith(typed)) || null;
      }
      if (target) { e.preventDefault(); target.focus(); return true; }
      return false;
    };
  }

  /* ---- scroll lock for modals ---- */
  let lockCount = 0, savedOverflow = '', savedPadding = '';
  function lockScroll() {
    if (lockCount++ === 0) {
      const sb = window.innerWidth - document.documentElement.clientWidth;
      savedOverflow = document.body.style.overflow; savedPadding = document.body.style.paddingRight;
      document.body.style.overflow = 'hidden';
      if (sb > 0) document.body.style.paddingRight = `${sb}px`;
      document.body.setAttribute('data-scroll-locked', '1');
    }
  }
  function unlockScroll() {
    if (lockCount > 0 && --lockCount === 0) {
      document.body.style.overflow = savedOverflow; document.body.style.paddingRight = savedPadding;
      document.body.removeAttribute('data-scroll-locked');
    }
  }

  /* ---- registration ---- */
  function register(name, def) {
    registry.set(name, def);
    if (document.readyState !== 'loading') init(name);
  }
  function init(name, root) {
    root = root || document;
    const def = registry.get(name);
    if (!def) return;
    const selector = def.selector || `[data-slot="${name}"]`;
    const nodes = root.matches && root.matches(selector) ? [root] : [];
    nodes.push(...qsa(root, selector));
    nodes.forEach((node) => {
      let set = initialized.get(node);
      if (!set) { set = new Set(); initialized.set(node, set); }
      if (set.has(name)) return;
      set.add(name);
      try { def.init(node, api); } catch (err) { console.error(`[flask-basecoat] ${name} init failed`, err); }
    });
  }
  function initAll(root) { registry.forEach((_, name) => init(name, root)); }

  function emit(el, name, detail) {
    el.dispatchEvent(new CustomEvent(`basecoat:${name}`, { bubbles: true, detail }));
  }

  const api = { register, init, initAll, setState, isOpen, ensureId, float, pairWith, pushLayer, removeLayer, trapFocus, focusFirst, focusables, roving, lockScroll, unlockScroll, emit, qs, qsa };
  global.FlaskBasecoat = api;

  document.addEventListener('DOMContentLoaded', () => initAll(document));
  // Content added later (htmx, fetch, Turbo) is initialised on insertion.
  const mo = new MutationObserver((muts) => {
    muts.forEach((m) => m.addedNodes.forEach((n) => { if (n.nodeType === 1) initAll(n); }));
  });
  if (document.body) mo.observe(document.body, { childList: true, subtree: true });
  else document.addEventListener('DOMContentLoaded', () => mo.observe(document.body, { childList: true, subtree: true }));
})(window);
