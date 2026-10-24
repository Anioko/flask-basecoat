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

  const api = { register, init, initAll, setState, isOpen, ensureId, float, pushLayer, removeLayer, trapFocus, focusFirst, focusables, roving, lockScroll, unlockScroll, emit, qs, qsa };
  global.FlaskBasecoat = api;

  document.addEventListener('DOMContentLoaded', () => initAll(document));
  // Content added later (htmx, fetch, Turbo) is initialised on insertion.
  const mo = new MutationObserver((muts) => {
    muts.forEach((m) => m.addedNodes.forEach((n) => { if (n.nodeType === 1) initAll(n); }));
  });
  if (document.body) mo.observe(document.body, { childList: true, subtree: true });
  else document.addEventListener('DOMContentLoaded', () => mo.observe(document.body, { childList: true, subtree: true }));
})(window);


/* ---- carousel ---- */
/* Carousel: scroll-snap based slides with previous/next buttons, keyboard arrows and disabled state at the ends. */
(function (FB) {
  'use strict';

  FB.register('carousel', {
    init(root) {
      const content = FB.qs(root, '[data-slot="carousel-content"]');
      const track = content && (content.firstElementChild && content.firstElementChild.getAttribute('data-slot') !== 'carousel-item' ? content.firstElementChild : content);
      const items = () => FB.qsa(root, '[data-slot="carousel-item"]');
      const prev = FB.qs(root, '[data-slot="carousel-previous"]');
      const next = FB.qs(root, '[data-slot="carousel-next"]');
      if (!content || !items().length) return;
      const vertical = root.getAttribute('data-orientation') === 'vertical';
      const loop = root.hasAttribute('data-loop');
      let index = 0;
      const viewport = content;
      viewport.style.overflow = 'hidden';
      function go(i) {
        const n = items().length;
        if (loop) i = (i + n) % n; else i = Math.max(0, Math.min(n - 1, i));
        index = i;
        const el = items()[index];
        const offset = vertical ? el.offsetTop - track.offsetTop : el.offsetLeft - track.offsetLeft;
        track.style.transform = vertical ? `translate3d(0, -${offset}px, 0)` : `translate3d(-${offset}px, 0, 0)`;
        track.style.transition = 'transform 300ms ease';
        if (prev) prev.disabled = !loop && index === 0;
        if (next) next.disabled = !loop && index >= n - 1;
        items().forEach((it, k) => it.setAttribute('aria-hidden', String(k !== index)));
        FB.emit(root, 'change', { index });
      }
      if (prev) prev.addEventListener('click', (e) => { e.preventDefault(); go(index - 1); });
      if (next) next.addEventListener('click', (e) => { e.preventDefault(); go(index + 1); });
      root.addEventListener('keydown', (e) => {
        if (e.key === (vertical ? 'ArrowUp' : 'ArrowLeft')) { e.preventDefault(); go(index - 1); }
        if (e.key === (vertical ? 'ArrowDown' : 'ArrowRight')) { e.preventDefault(); go(index + 1); }
      });
      let startX = 0, startY = 0;
      viewport.addEventListener('pointerdown', (e) => { startX = e.clientX; startY = e.clientY; });
      viewport.addEventListener('pointerup', (e) => {
        const dx = e.clientX - startX, dy = e.clientY - startY;
        const d = vertical ? dy : dx;
        if (Math.abs(d) > 40) go(index + (d < 0 ? 1 : -1));
      });
      window.addEventListener('resize', () => go(index));
      go(0);
      root.fbGo = go;
    },
  });
})(window.FlaskBasecoat);


/* ---- dialog ---- */
/* Dialog, Alert Dialog, Sheet and Drawer: modal layers.
   Markup (server-rendered): a display:contents wrapper [data-fb="dialog"] holding the trigger, overlay and content.
   Behaviour mirrors Radix Dialog: aria-expanded/data-state on the trigger, scroll lock, focus trap, focus restore,
   Escape and overlay click dismiss (alert-dialog ignores overlay click), exit animation before hiding. */
(function (FB) {
  'use strict';

  function setup(kind, wrapper) {
    const trigger = FB.qs(wrapper, `[data-slot="${kind}-trigger"]`);
    const overlay = FB.qs(wrapper, `[data-slot="${kind}-overlay"]`);
    const content = FB.qs(wrapper, `[data-slot="${kind}-content"]`);
    if (!content) return;
    const id = FB.ensureId(content, kind);
    if (trigger) trigger.setAttribute('aria-controls', id);
    const title = FB.qs(content, `[data-slot="${kind}-title"]`);
    const desc = FB.qs(content, `[data-slot="${kind}-description"]`);
    if (title) content.setAttribute('aria-labelledby', FB.ensureId(title, `${kind}-title`));
    if (desc) content.setAttribute('aria-describedby', FB.ensureId(desc, `${kind}-description`));
    let layer = null, untrap = null, previouslyFocused = null, closing = null;

    function finishHide() {
      [overlay, content].forEach((el) => el && el.removeAttribute('data-fb-animating'));
      closing = null;
    }
    function open() {
      if (FB.isOpen(content)) return;
      if (closing) { clearTimeout(closing); finishHide(); }
      previouslyFocused = document.activeElement;
      // Portal to <body> so stacking is independent of the trigger's ancestors.
      if (overlay && overlay.parentNode !== document.body) document.body.appendChild(overlay);
      if (content.parentNode !== document.body) document.body.appendChild(content);
      [overlay, content].forEach((el) => el && FB.setState(el, 'open'));
      if (trigger) { FB.setState(trigger, 'open'); trigger.setAttribute('aria-expanded', 'true'); }
      FB.lockScroll();
      untrap = FB.trapFocus(content);
      FB.focusFirst(content, '[data-autofocus], [autofocus]');
      layer = {
        content, trigger, modal: true,
        onDismiss(reason, e) {
          if (reason === 'outside' && (kind === 'alert-dialog' || (e && content.contains(e.target)))) return;
          if (reason === 'outside' && e && overlay && !overlay.contains(e.target) && e.target !== overlay) {
            // clicks on other fixed layers (toasts) do not dismiss
            if (!e.target.closest || !e.target.closest('body')) return;
          }
          close();
        },
      };
      FB.pushLayer(layer);
      FB.emit(content, 'open', { kind });
    }
    function close() {
      if (!FB.isOpen(content)) return;
      [overlay, content].forEach((el) => el && (el.setAttribute('data-fb-animating', ''), FB.setState(el, 'closed')));
      if (trigger) { FB.setState(trigger, 'closed'); trigger.setAttribute('aria-expanded', 'false'); }
      FB.unlockScroll();
      if (untrap) { untrap(); untrap = null; }
      if (layer) { FB.removeLayer(layer); layer = null; }
      closing = setTimeout(finishHide, 220);
      if (previouslyFocused && previouslyFocused.focus) previouslyFocused.focus({ preventScroll: true });
      FB.emit(content, 'close', { kind });
    }
    if (trigger) trigger.addEventListener('click', (e) => { e.preventDefault(); open(); });
    content.addEventListener('click', (e) => {
      const btn = e.target.closest(`[data-slot="${kind}-close"], [data-slot="${kind}-cancel"], [data-slot="${kind}-action"], [data-fb-close]`);
      if (btn && content.contains(btn)) { e.preventDefault(); close(); }
    });
    if (overlay) overlay.addEventListener('click', (e) => { if (e.target === overlay && kind !== 'alert-dialog') close(); });
    wrapper.fbOpen = open; wrapper.fbClose = close;
    if (content.getAttribute('data-state') === 'open') { FB.setState(content, 'closed'); open(); }
    // Any element elsewhere may open this dialog through data-fb-open="<id>"
    document.addEventListener('click', (e) => {
      const opener = e.target.closest && e.target.closest(`[data-fb-open="${id}"]`);
      if (opener) { e.preventDefault(); open(); }
    });
  }

  ['dialog', 'alert-dialog', 'sheet', 'drawer'].forEach((kind) => {
    FB.register(kind, { selector: `[data-fb="${kind}"]`, init: (el) => setup(kind, el) });
  });
})(window.FlaskBasecoat);


/* ---- disclosure ---- */
/* Accordion, Collapsible and Trace collapsible: expand/collapse regions with data-state and aria-expanded. */
(function (FB) {
  'use strict';

  function heightVar(content, name) {
    content.style.setProperty(name, `${content.scrollHeight}px`);
  }

  function toggleContent(trigger, content, open, varName) {
    const item = trigger.closest('[data-slot$="-item"], [data-slot="collapsible"], [data-slot="trace-collapsible"]');
    if (open) {
      content.removeAttribute('hidden');
      FB.setState(content, 'open');
      heightVar(content, varName);
    } else {
      heightVar(content, varName);
      FB.setState(content, 'closed');
      content.setAttribute('data-fb-animating', '');
      setTimeout(() => { if (content.getAttribute('data-state') === 'closed') { content.setAttribute('hidden', ''); content.removeAttribute('data-fb-animating'); } }, 220);
    }
    FB.setState(trigger, open ? 'open' : 'closed');
    trigger.setAttribute('aria-expanded', String(open));
    if (item) FB.setState(item, open ? 'open' : 'closed');
  }

  FB.register('accordion', {
    init(root) {
      const type = root.getAttribute('data-type') || 'single';
      const collapsible = root.getAttribute('data-collapsible') !== 'false';
      const items = FB.qsa(root, '[data-slot="accordion-item"]').filter((i) => i.closest('[data-slot="accordion"]') === root);
      const pairs = items.map((item) => {
        const trigger = FB.qs(item, '[data-slot="accordion-trigger"]');
        const content = FB.qs(item, '[data-slot="accordion-content"]');
        if (!trigger || !content) return null;
        trigger.setAttribute('aria-controls', FB.ensureId(content, 'accordion-content'));
        content.setAttribute('aria-labelledby', FB.ensureId(trigger, 'accordion-trigger'));
        return { item, trigger, content };
      }).filter(Boolean);
      const triggers = () => pairs.map((p) => p.trigger);
      const nav = FB.roving(triggers, { orientation: root.getAttribute('data-orientation') === 'horizontal' ? 'horizontal' : 'vertical', loop: true, typeahead: false });
      pairs.forEach((p) => {
        p.trigger.addEventListener('click', (e) => {
          e.preventDefault();
          const isOpen = p.trigger.getAttribute('aria-expanded') === 'true';
          if (type === 'single') {
            pairs.forEach((o) => { if (o !== p && o.trigger.getAttribute('aria-expanded') === 'true') toggleContent(o.trigger, o.content, false, '--radix-accordion-content-height'); });
            if (isOpen && !collapsible) return;
          }
          toggleContent(p.trigger, p.content, !isOpen, '--radix-accordion-content-height');
          FB.emit(root, 'change', { value: p.item.getAttribute('data-value'), open: !isOpen });
        });
        p.trigger.addEventListener('keydown', nav);
      });
    },
  });

  function collapsible(kind) {
    return {
      init(root) {
        const trigger = FB.qs(root, `[data-slot="${kind}-trigger"]`);
        const content = FB.qs(root, `[data-slot="${kind}-content"]`);
        if (!trigger || !content) return;
        trigger.setAttribute('aria-controls', FB.ensureId(content, `${kind}-content`));
        trigger.addEventListener('click', (e) => {
          e.preventDefault();
          const isOpen = trigger.getAttribute('aria-expanded') === 'true';
          toggleContent(trigger, content, !isOpen, '--radix-collapsible-content-height');
          FB.emit(root, 'change', { open: !isOpen });
        });
      },
    };
  }
  FB.register('collapsible', collapsible('collapsible'));
  FB.register('trace-collapsible', collapsible('trace-collapsible'));
})(window.FlaskBasecoat);


/* ---- input-otp ---- */
/* Input OTP: a visually hidden input drives the slot cells; typing, paste, Backspace and arrow keys update the
   active slot (data-active) and the rendered characters, with a fake caret in the active empty slot. */
(function (FB) {
  'use strict';

  FB.register('input-otp', {
    init(input) {
      const container = input.closest('[data-input-otp-container]') || input.parentElement;
      const slots = () => FB.qsa(container, '[data-slot="input-otp-slot"]');
      const maxLength = Number(input.getAttribute('maxlength') || slots().length || 6);
      input.setAttribute('maxlength', String(maxLength));
      const pattern = input.getAttribute('pattern') ? new RegExp(input.getAttribute('pattern')) : null;
      function render() {
        const value = input.value;
        const focused = document.activeElement === input;
        const caret = Math.min(value.length, maxLength - 1);
        slots().forEach((s, i) => {
          const ch = value[i] || '';
          let text = FB.qs(s, '[data-fb-otp-char]');
          if (!text) { text = document.createElement('span'); text.setAttribute('data-fb-otp-char', ''); s.insertBefore(text, s.firstChild); }
          text.textContent = ch;
          const active = focused && (i === caret || (value.length === maxLength && i === maxLength - 1));
          s.setAttribute('data-active', String(active));
          let fake = FB.qs(s, '[data-fb-otp-caret]');
          if (active && !ch) {
            if (!fake) { fake = document.createElement('div'); fake.setAttribute('data-fb-otp-caret', ''); fake.className = 'pointer-events-none absolute inset-0 flex items-center justify-center'; fake.innerHTML = '<div class="h-4 w-px bg-foreground animate-caret-blink duration-1000"></div>'; s.appendChild(fake); }
          } else if (fake) fake.remove();
        });
        input.setAttribute('data-input-otp-placeholder-shown', String(!value.length));
        if (value.length === maxLength) FB.emit(input, 'complete', { value });
      }
      input.addEventListener('input', () => {
        let v = input.value.replace(/\s+/g, '');
        if (pattern) v = v.split('').filter((c) => pattern.test(c)).join('');
        input.value = v.slice(0, maxLength);
        render();
        FB.emit(input, 'change', { value: input.value });
      });
      input.addEventListener('focus', render);
      input.addEventListener('blur', render);
      container.addEventListener('click', () => input.focus());
      render();
    },
  });
})(window.FlaskBasecoat);


/* ---- menu ---- */
/* Dropdown Menu, Context Menu and Menubar, with submenus, checkbox and radio items.
   Keyboard: arrows move between items (looping), Home/End, type-ahead, Enter/Space activates, ArrowRight opens a
   submenu, ArrowLeft closes it, Escape closes the menu and returns focus to the trigger. */
(function (FB) {
  'use strict';

  const ITEM_SEL = '[role="menuitem"], [role="menuitemcheckbox"], [role="menuitemradio"]';

  function setupMenu(kind, wrapper, opts) {
    const trigger = FB.qs(wrapper, `:scope > [data-slot="${kind}-trigger"], [data-slot="${kind}-trigger"]`);
    const content = FB.qs(wrapper, `:scope > [data-slot="${kind}-content"], [data-slot="${kind}-content"]`);
    if (!trigger || !content) return null;
    const id = FB.ensureId(content, kind);
    content.setAttribute('data-floating', '');
    content.setAttribute('data-popper-var', kind);
    trigger.setAttribute('aria-controls', id);
    content.setAttribute('aria-labelledby', FB.ensureId(trigger, `${kind}-trigger`));
    const side = content.getAttribute('data-side') || opts.side || 'bottom';
    const align = content.getAttribute('data-align') || opts.align || 'start';
    let layer = null, anchorPoint = null;

    const items = () => FB.qsa(content, ITEM_SEL).filter((i) => i.closest(`[data-slot$="-content"]`) === content);
    const onKey = FB.roving(items, { orientation: 'vertical', loop: true });

    function reposition() {
      if (anchorPoint) {
        content.style.transform = `translate(${anchorPoint.x}px, ${anchorPoint.y}px)`;
        content.setAttribute('data-side', 'right'); content.setAttribute('data-align', 'start');
      } else FB.float(trigger, content, { side, align, sideOffset: 4 });
    }
    function open(point) {
      anchorPoint = point || null;
      if (FB.isOpen(content)) { reposition(); return; }
      if (content.parentNode !== document.body) document.body.appendChild(content);
      FB.setState(content, 'open'); FB.setState(trigger, 'open');
      trigger.setAttribute('aria-expanded', 'true');
      reposition();
      layer = { content, trigger, modal: false, reposition, onDismiss: (reason) => close(reason !== 'outside') };
      FB.pushLayer(layer);
      const first = items()[0];
      (first || content).focus({ preventScroll: true });
      FB.emit(content, 'open', { kind });
    }
    function close(refocus) {
      if (!FB.isOpen(content)) return;
      closeSubmenus();
      FB.setState(content, 'closed'); FB.setState(trigger, 'closed');
      trigger.setAttribute('aria-expanded', 'false');
      if (layer) { FB.removeLayer(layer); layer = null; }
      if (refocus !== false && kind !== 'context-menu') trigger.focus({ preventScroll: true });
      FB.emit(content, 'close', { kind });
    }
    function activate(item) {
      if (item.getAttribute('aria-disabled') === 'true' || item.hasAttribute('data-disabled')) return;
      if (item.getAttribute('role') === 'menuitemcheckbox') {
        const checked = item.getAttribute('aria-checked') === 'true';
        item.setAttribute('aria-checked', String(!checked));
        FB.setState(item, checked ? 'unchecked' : 'checked');
        FB.emit(item, 'change', { checked: !checked, value: item.getAttribute('data-value') });
        return;
      }
      if (item.getAttribute('role') === 'menuitemradio') {
        const group = item.closest('[role="group"]') || content;
        FB.qsa(group, '[role="menuitemradio"]').forEach((r) => { r.setAttribute('aria-checked', 'false'); FB.setState(r, 'unchecked'); });
        item.setAttribute('aria-checked', 'true'); FB.setState(item, 'checked');
        FB.emit(item, 'change', { value: item.getAttribute('data-value') });
        close();
        return;
      }
      if (item.hasAttribute('aria-haspopup')) { openSub(item); return; }
      FB.emit(item, 'select', { value: item.getAttribute('data-value') });
      const link = item.matches('a[href]') ? item : item.querySelector('a[href]');
      close();
      if (link && link !== item) link.click();
    }

    /* submenus: [data-slot="kind-sub"] > sub-trigger + sub-content */
    const subs = FB.qsa(content, `[data-fb="${kind}-sub"]`).map((sub) => {
      const st = FB.qs(sub, `[data-slot="${kind}-sub-trigger"]`);
      const sc = FB.qs(sub, `[data-slot="${kind}-sub-content"]`);
      if (!st || !sc) return null;
      sc.setAttribute('data-floating', ''); sc.setAttribute('data-popper-var', kind);
      st.setAttribute('aria-controls', FB.ensureId(sc, `${kind}-sub`));
      let timer = 0;
      const subItems = () => FB.qsa(sc, ITEM_SEL);
      const subKey = FB.roving(subItems, { orientation: 'vertical', loop: true });
      const api = {
        trigger: st, content: sc,
        open() {
          if (FB.isOpen(sc)) return;
          if (sc.parentNode !== document.body) document.body.appendChild(sc);
          FB.setState(sc, 'open'); FB.setState(st, 'open'); st.setAttribute('aria-expanded', 'true');
          FB.float(st, sc, { side: 'right', align: 'start', sideOffset: 0 });
        },
        close() { if (!FB.isOpen(sc)) return; FB.setState(sc, 'closed'); FB.setState(st, 'closed'); st.setAttribute('aria-expanded', 'false'); },
      };
      st.addEventListener('pointerenter', () => { clearTimeout(timer); timer = setTimeout(api.open, 100); });
      st.addEventListener('pointerleave', (e) => { clearTimeout(timer); if (!sc.contains(e.relatedTarget)) timer = setTimeout(api.close, 200); });
      sc.addEventListener('pointerleave', (e) => { if (e.relatedTarget !== st && !sc.contains(e.relatedTarget)) timer = setTimeout(api.close, 200); });
      sc.addEventListener('pointerenter', () => clearTimeout(timer));
      st.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); api.open(); const f = subItems()[0]; f && f.focus(); });
      st.addEventListener('keydown', (e) => { if (e.key === 'ArrowRight' || e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); api.open(); const f = subItems()[0]; f && f.focus(); } });
      sc.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') { e.preventDefault(); e.stopPropagation(); api.close(); st.focus(); return; }
        if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); api.close(); close(); return; }
        if (subKey(e)) { e.stopPropagation(); return; }
        if (e.key === 'Enter' || e.key === ' ') { const it = e.target.closest(ITEM_SEL); if (it) { e.preventDefault(); e.stopPropagation(); activate(it); } }
      });
      sc.addEventListener('click', (e) => { const it = e.target.closest(ITEM_SEL); if (it && sc.contains(it)) { e.stopPropagation(); activate(it); } });
      sc.addEventListener('pointermove', (e) => { const it = e.target.closest(ITEM_SEL); if (it && document.activeElement !== it) it.focus(); });
      return api;
    }).filter(Boolean);
    function closeSubmenus() { subs.forEach((s) => s.close()); }

    content.addEventListener('keydown', (e) => {
      if (onKey(e)) return;
      if (e.key === 'Enter' || e.key === ' ') { const it = e.target.closest(ITEM_SEL); if (it) { e.preventDefault(); activate(it); } }
      if (e.key === 'Tab') { e.preventDefault(); close(); }
    });
    content.addEventListener('click', (e) => { const it = e.target.closest(ITEM_SEL); if (it && content.contains(it)) activate(it); });
    content.addEventListener('pointermove', (e) => { const it = e.target.closest(ITEM_SEL); if (it && it.closest('[data-slot$="-content"]') === content && document.activeElement !== it) it.focus(); });
    content.addEventListener('pointerleave', () => { if (document.activeElement && content.contains(document.activeElement) && !subs.some((s) => FB.isOpen(s.content))) content.focus(); });

    if (kind === 'context-menu') {
      trigger.addEventListener('contextmenu', (e) => { e.preventDefault(); open({ x: e.clientX, y: e.clientY }); });
    } else {
      trigger.addEventListener('click', (e) => { e.preventDefault(); FB.isOpen(content) ? close() : open(); });
      trigger.addEventListener('keydown', (e) => { if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } });
    }
    const api = { trigger, content, open, close, isOpen: () => FB.isOpen(content) };
    wrapper.fbOpen = open; wrapper.fbClose = close;
    return api;
  }

  FB.register('dropdown-menu', { selector: '[data-fb="dropdown-menu"]', init: (el) => setupMenu('dropdown-menu', el, {}) });
  FB.register('context-menu', { selector: '[data-fb="context-menu"]', init: (el) => setupMenu('context-menu', el, {}) });

  /* Menubar: a row of menus; hovering across triggers while one is open switches menus. */
  FB.register('menubar', {
    selector: '[data-slot="menubar"]',
    init(bar) {
      const menus = FB.qsa(bar, '[data-fb="menubar-menu"]').map((m) => setupMenu('menubar', m, { side: 'bottom', align: 'start' })).filter(Boolean);
      const triggers = () => menus.map((m) => m.trigger);
      const nav = FB.roving(triggers, { orientation: 'horizontal', loop: true, typeahead: false });
      menus.forEach((m, i) => {
        m.trigger.setAttribute('tabindex', i === 0 ? '0' : '-1');
        m.trigger.addEventListener('pointerenter', () => { if (menus.some((o) => o !== m && o.isOpen())) { menus.forEach((o) => o !== m && o.close(false)); m.open(); } });
        m.trigger.addEventListener('keydown', (e) => { if (nav(e)) { const wasOpen = m.isOpen(); if (wasOpen) { m.close(false); const t = document.activeElement; const next = menus.find((o) => o.trigger === t); next && next.open(); } } });
        m.content.addEventListener('keydown', (e) => {
          if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
            const sub = e.target.closest('[data-slot="menubar-sub-content"]');
            if (sub) return;
            const idx = menus.indexOf(m); const n = menus[(idx + (e.key === 'ArrowRight' ? 1 : -1) + menus.length) % menus.length];
            e.preventDefault(); m.close(false); n.trigger.focus(); n.open();
          }
        });
      });
    },
  });
})(window.FlaskBasecoat);


/* ---- misc ---- */
/* Smaller behaviours: theme toggle, code block copy, resizable panels, navigation menu, message scroller,
   progress animation, avatar image fallback, sonner compatibility alias. */
(function (FB) {
  'use strict';

  /* Theme toggle: any element with data-theme-toggle flips the .dark class and remembers the choice. */
  document.addEventListener('click', (e) => {
    const t = e.target.closest && e.target.closest('[data-theme-toggle]');
    if (!t) return;
    e.preventDefault();
    const dark = document.documentElement.classList.toggle('dark');
    try { localStorage.setItem('flask-basecoat-theme', dark ? 'dark' : 'light'); } catch (err) { /* ignore */ }
    FB.emit(document.documentElement, 'theme', { dark });
  });

  /* Code block copy button */
  FB.register('code-block-copy-button', {
    init(btn) {
      btn.addEventListener('click', async () => {
        const block = btn.closest('[data-slot="code-block"]');
        const code = block && FB.qs(block, '[data-slot="code-block-code"], pre');
        const text = code ? code.textContent : '';
        try { await navigator.clipboard.writeText(text); } catch (err) { /* clipboard unavailable */ }
        btn.setAttribute('data-copied', 'true');
        setTimeout(() => btn.removeAttribute('data-copied'), 2000);
      });
    },
  });

  /* Avatar: hide the image and show the fallback when the image fails to load (Radix behaviour). */
  FB.register('avatar', {
    init(root) {
      const img = FB.qs(root, '[data-slot="avatar-image"]');
      const fallback = FB.qs(root, '[data-slot="avatar-fallback"]');
      if (!img) return;
      const loaded = () => { if (fallback) fallback.style.display = 'none'; img.style.display = ''; };
      const failed = () => { img.style.display = 'none'; if (fallback) fallback.style.display = ''; };
      if (img.complete) (img.naturalWidth ? loaded : failed)();
      img.addEventListener('load', loaded);
      img.addEventListener('error', failed);
    },
  });

  /* Resizable panels: drag the handle to resize neighbouring panels (flex-basis percentages). */
  FB.register('resizable-panel-group', {
    init(group) {
      const vertical = group.getAttribute('data-orientation') === 'vertical' || group.getAttribute('aria-orientation') === 'vertical';
      const children = Array.from(group.children);
      children.forEach((c) => { if (c.getAttribute('data-slot') === 'resizable-panel' && !c.style.flex) c.style.flex = `${Number(c.getAttribute('data-default-size') || 50)} 1 0px`; });
      FB.qsa(group, ':scope > [data-slot="resizable-handle"]').forEach((handle) => {
        const prev = handle.previousElementSibling, next = handle.nextElementSibling;
        if (!prev || !next) return;
        handle.setAttribute('aria-orientation', vertical ? 'vertical' : 'horizontal');
        let start = 0, prevSize = 0, nextSize = 0, total = 0;
        function sizes() { const r1 = prev.getBoundingClientRect(), r2 = next.getBoundingClientRect(); return vertical ? [r1.height, r2.height] : [r1.width, r2.width]; }
        function applyPct(p1, p2) { prev.style.flex = `${p1} 1 0px`; next.style.flex = `${p2} 1 0px`; prev.setAttribute('data-size', p1.toFixed(1)); next.setAttribute('data-size', p2.toFixed(1)); }
        handle.addEventListener('pointerdown', (e) => {
          e.preventDefault(); handle.setPointerCapture(e.pointerId);
          handle.setAttribute('data-separator', 'active'); handle.setAttribute('data-resize-handle-state', 'drag');
          start = vertical ? e.clientY : e.clientX; [prevSize, nextSize] = sizes(); total = prevSize + nextSize;
        });
        handle.addEventListener('pointermove', (e) => {
          if (handle.getAttribute('data-separator') !== 'active') return;
          const d = (vertical ? e.clientY : e.clientX) - start;
          const p = Math.min(total, Math.max(0, prevSize + d));
          const groupSize = vertical ? group.getBoundingClientRect().height : group.getBoundingClientRect().width;
          applyPct((p / groupSize) * 100, ((total - p) / groupSize) * 100);
        });
        const end = () => { handle.setAttribute('data-separator', 'inactive'); handle.removeAttribute('data-resize-handle-state'); };
        handle.addEventListener('pointerup', end); handle.addEventListener('pointercancel', end);
        handle.addEventListener('keydown', (e) => {
          const step = e.shiftKey ? 10 : 1;
          const keys = vertical ? { ArrowUp: -step, ArrowDown: step } : { ArrowLeft: -step, ArrowRight: step };
          if (!(e.key in keys)) return;
          e.preventDefault();
          const [a, b] = sizes(); const g = vertical ? group.getBoundingClientRect().height : group.getBoundingClientRect().width;
          const pa = (a / g) * 100 + keys[e.key], pb = (b / g) * 100 - keys[e.key];
          if (pa >= 0 && pb >= 0) applyPct(pa, pb);
        });
      });
    },
  });

  /* Navigation menu: triggers open their content panel below; hover and focus switch between items. */
  FB.register('navigation-menu', {
    init(nav) {
      const items = FB.qsa(nav, '[data-slot="navigation-menu-item"]');
      const viewport = FB.qs(nav, '[data-slot="navigation-menu-viewport"]');
      let openItem = null, timer = 0;
      items.forEach((item) => {
        const trigger = FB.qs(item, '[data-slot="navigation-menu-trigger"]');
        const content = FB.qs(item, '[data-slot="navigation-menu-content"]');
        if (!trigger || !content) return;
        trigger.setAttribute('aria-controls', FB.ensureId(content, 'navigation-menu-content'));
        content.setAttribute('data-floating', '');
        content.setAttribute('data-popper-var', 'navigation-menu');
        const open = () => {
          clearTimeout(timer);
          if (openItem && openItem !== item) closeItem(openItem);
          openItem = item;
          FB.setState(trigger, 'open'); trigger.setAttribute('aria-expanded', 'true'); FB.setState(content, 'open');
          if (viewport) { FB.setState(viewport, 'open'); viewport.style.setProperty('--radix-navigation-menu-viewport-width', `${content.offsetWidth}px`); viewport.style.setProperty('--radix-navigation-menu-viewport-height', `${content.offsetHeight}px`); }
          FB.float(trigger, content, { side: 'bottom', align: 'start', sideOffset: 8 });
          nav.fbLayer = { content, trigger, modal: false, onDismiss: () => closeItem(item) };
          FB.pushLayer(nav.fbLayer);
        };
        const closeItem = (it) => {
          const t = FB.qs(it, '[data-slot="navigation-menu-trigger"]'), c = FB.qs(it, '[data-slot="navigation-menu-content"]');
          if (t) { FB.setState(t, 'closed'); t.setAttribute('aria-expanded', 'false'); }
          if (c) FB.setState(c, 'closed');
          if (viewport && openItem === it) FB.setState(viewport, 'closed');
          if (openItem === it) openItem = null;
          if (nav.fbLayer) { FB.removeLayer(nav.fbLayer); nav.fbLayer = null; }
        };
        const scheduleClose = () => { clearTimeout(timer); timer = setTimeout(() => openItem === item && closeItem(item), 150); };
        trigger.addEventListener('click', (e) => { e.preventDefault(); openItem === item ? closeItem(item) : open(); });
        trigger.addEventListener('pointerenter', () => { clearTimeout(timer); timer = setTimeout(open, 150); });
        trigger.addEventListener('pointerleave', scheduleClose);
        content.addEventListener('pointerenter', () => clearTimeout(timer));
        content.addEventListener('pointerleave', scheduleClose);
        trigger.addEventListener('keydown', (e) => { if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); FB.focusFirst(content); } });
        content.addEventListener('keydown', (e) => { if (e.key === 'Escape') { closeItem(item); trigger.focus(); } });
      });
      const links = () => FB.qsa(nav, '[data-slot="navigation-menu-trigger"], [data-slot="navigation-menu-link"]').filter((l) => !l.closest('[data-slot="navigation-menu-content"]'));
      const navKey = FB.roving(links, { orientation: 'horizontal', loop: false, typeahead: false });
      nav.addEventListener('keydown', (e) => { if (!e.target.closest('[data-slot="navigation-menu-content"]')) navKey(e); });
    },
  });

  /* Message scroller: keeps a chat log pinned to the bottom and shows a scroll-to-bottom button when scrolled up. */
  FB.register('message-scroller', {
    init(root) {
      const viewport = FB.qs(root, '[data-slot="message-scroller-viewport"]');
      const button = FB.qs(root, '[data-slot="message-scroller-button"]');
      if (!viewport) return;
      const atBottom = () => viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight < 8;
      const update = () => { const bottom = atBottom(); root.toggleAttribute('data-pending-scroll', !bottom); if (button) { button.setAttribute('data-active', String(!bottom)); button.toggleAttribute('inert', bottom); } };
      viewport.addEventListener('scroll', update);
      if (button) button.addEventListener('click', () => viewport.scrollTo({ top: viewport.scrollHeight, behavior: 'smooth' }));
      new MutationObserver(() => { if (!root.hasAttribute('data-pending-scroll')) viewport.scrollTop = viewport.scrollHeight; update(); }).observe(viewport, { childList: true, subtree: true });
      viewport.scrollTop = viewport.scrollHeight; update();
    },
  });

  /* Progress: set value via FlaskBasecoat.progress(el, value) or data-value changes. */
  FB.progress = function (el, value, max) {
    const indicator = FB.qs(el, '[data-slot="progress-indicator"]');
    max = max || Number(el.getAttribute('data-max') || 100);
    el.setAttribute('aria-valuenow', String(value)); el.setAttribute('data-value', String(value)); el.setAttribute('data-max', String(max));
    el.setAttribute('data-state', value >= max ? 'complete' : 'loading');
    if (indicator) { indicator.setAttribute('data-state', el.getAttribute('data-state')); indicator.setAttribute('data-value', String(value)); indicator.style.transform = `translateX(-${100 - (value / max) * 100}%)`; }
  };

  /* Sonner compatibility */
  window.sonner = window.sonner || { toast: (...a) => FB.toast(...a) };
})(window.FlaskBasecoat);


/* ---- popover ---- */
/* Popover, Hover Card and Tooltip: non-modal floating layers anchored to a trigger.
   Popover opens on click (dismiss on outside/Escape, focus moves into the content).
   Hover Card opens on pointer hover / focus with open and close delays.
   Tooltip opens on hover / focus with a delay, closes on pointer leave, blur or Escape. */
(function (FB) {
  'use strict';

  function setup(kind, wrapper) {
    const trigger = FB.qs(wrapper, `[data-slot="${kind}-trigger"]`) || FB.qs(wrapper, `[data-slot="${kind}-anchor"]`);
    const content = FB.qs(wrapper, `[data-slot="${kind}-content"]`);
    if (!trigger || !content) return;
    const id = FB.ensureId(content, kind);
    content.setAttribute('data-floating', '');
    content.setAttribute('data-popper-var', kind === 'popover' ? 'popover' : kind === 'hover-card' ? 'hover-card' : 'tooltip');
    const side = content.getAttribute('data-side') || wrapper.getAttribute('data-side') || (kind === 'tooltip' ? 'top' : 'bottom');
    const align = content.getAttribute('data-align') || wrapper.getAttribute('data-align') || 'center';
    const sideOffset = Number(content.getAttribute('data-side-offset') || (kind === 'tooltip' ? 0 : 4));
    if (kind === 'popover') trigger.setAttribute('aria-controls', id);
    if (kind === 'tooltip') trigger.setAttribute('aria-describedby', id);
    let layer = null, openTimer = 0, closeTimer = 0;

    function reposition() { FB.float(trigger, content, { side, align, sideOffset }); }
    function open() {
      clearTimeout(closeTimer);
      if (FB.isOpen(content)) return;
      if (content.parentNode !== document.body) document.body.appendChild(content);
      FB.setState(content, 'open');
      FB.setState(trigger, kind === 'tooltip' ? 'delayed-open' : 'open');
      if (kind === 'popover') trigger.setAttribute('aria-expanded', 'true');
      reposition();
      layer = { content, trigger, modal: false, reposition, onDismiss: () => close() };
      FB.pushLayer(layer);
      if (kind === 'popover') FB.focusFirst(content);
      FB.emit(content, 'open', { kind });
    }
    function close() {
      clearTimeout(openTimer);
      if (!FB.isOpen(content)) return;
      FB.setState(content, 'closed');
      FB.setState(trigger, 'closed');
      if (kind === 'popover') { trigger.setAttribute('aria-expanded', 'false'); if (content.contains(document.activeElement)) trigger.focus(); }
      if (layer) { FB.removeLayer(layer); layer = null; }
      FB.emit(content, 'close', { kind });
    }
    if (kind === 'popover') {
      trigger.addEventListener('click', (e) => { e.preventDefault(); FB.isOpen(content) ? close() : open(); });
      content.addEventListener('click', (e) => { if (e.target.closest('[data-fb-close]')) close(); });
    } else {
      const openDelay = Number(wrapper.getAttribute('data-open-delay') || (kind === 'tooltip' ? 0 : 700));
      const closeDelay = Number(wrapper.getAttribute('data-close-delay') || (kind === 'tooltip' ? 0 : 300));
      const scheduleOpen = () => { clearTimeout(closeTimer); openTimer = setTimeout(open, openDelay); };
      const scheduleClose = () => { clearTimeout(openTimer); closeTimer = setTimeout(close, closeDelay); };
      trigger.addEventListener('pointerenter', scheduleOpen);
      trigger.addEventListener('pointerleave', scheduleClose);
      trigger.addEventListener('focus', open);
      trigger.addEventListener('blur', close);
      content.addEventListener('pointerenter', () => clearTimeout(closeTimer));
      content.addEventListener('pointerleave', scheduleClose);
      if (kind === 'tooltip') trigger.addEventListener('pointerdown', close);
    }
    wrapper.fbOpen = open; wrapper.fbClose = close;
    if (content.getAttribute('data-state') === 'open') { FB.setState(content, 'closed'); open(); }
  }

  ['popover', 'hover-card', 'tooltip'].forEach((kind) => {
    FB.register(kind, { selector: `[data-fb="${kind}"]`, init: (el) => setup(kind, el) });
  });
})(window.FlaskBasecoat);


/* ---- select ---- */
/* Select: a button trigger (role=combobox) opening a listbox; keyboard navigation, type-ahead, Enter/Space selects,
   Escape closes. The selected item's label is copied into [data-slot="select-value"] and the value into a hidden
   input named by the wrapper's data-name (or `name`). Native Select needs no script. */
(function (FB) {
  'use strict';

  FB.register('select', {
    selector: '[data-fb="select"]',
    init(wrapper) {
      const trigger = FB.qs(wrapper, '[data-slot="select-trigger"]');
      const content = FB.qs(wrapper, '[data-slot="select-content"]');
      const valueEl = trigger && FB.qs(trigger, '[data-slot="select-value"]');
      if (!trigger || !content) return;
      const id = FB.ensureId(content, 'select');
      trigger.setAttribute('aria-controls', id);
      content.setAttribute('data-floating', '');
      content.setAttribute('data-popper-var', 'select');
      const name = wrapper.getAttribute('data-name') || wrapper.getAttribute('name');
      let input = null;
      if (name) { input = document.createElement('input'); input.type = 'hidden'; input.name = name; wrapper.appendChild(input); }
      const placeholder = valueEl ? valueEl.textContent : '';
      const items = () => FB.qsa(content, '[data-slot="select-item"]');
      const nav = FB.roving(items, { orientation: 'vertical', loop: false });
      let layer = null;

      function reposition() { FB.float(trigger, content, { side: content.getAttribute('data-side') || 'bottom', align: content.getAttribute('data-align') || 'start', sideOffset: 4 }); }
      function open() {
        if (FB.isOpen(content)) return;
        if (content.parentNode !== document.body) document.body.appendChild(content);
        FB.setState(content, 'open'); FB.setState(trigger, 'open'); trigger.setAttribute('aria-expanded', 'true');
        reposition();
        layer = { content, trigger, modal: false, reposition, onDismiss: () => close() };
        FB.pushLayer(layer);
        const selected = items().find((i) => i.getAttribute('data-state') === 'checked') || items()[0];
        (selected || content).focus({ preventScroll: true });
      }
      function close() {
        if (!FB.isOpen(content)) return;
        FB.setState(content, 'closed'); FB.setState(trigger, 'closed'); trigger.setAttribute('aria-expanded', 'false');
        if (layer) { FB.removeLayer(layer); layer = null; }
        trigger.focus({ preventScroll: true });
      }
      function select(item) {
        if (item.getAttribute('aria-disabled') === 'true' || item.hasAttribute('data-disabled')) return;
        items().forEach((i) => { const on = i === item; i.setAttribute('aria-selected', String(on)); FB.setState(i, on ? 'checked' : 'unchecked'); });
        const value = item.getAttribute('data-value') || item.textContent.trim();
        const label = (FB.qs(item, '[data-slot="select-item-text"]') || item).textContent.trim();
        if (valueEl) { valueEl.textContent = label; }
        trigger.removeAttribute('data-placeholder');
        if (input) input.value = value;
        wrapper.setAttribute('data-value', value);
        FB.emit(wrapper, 'change', { value, label });
        close();
      }
      const preselected = items().find((i) => i.getAttribute('data-state') === 'checked' || i.getAttribute('aria-selected') === 'true');
      if (preselected) { const label = preselected.textContent.trim(); if (valueEl && !valueEl.textContent.trim()) valueEl.textContent = label; if (input) input.value = preselected.getAttribute('data-value') || label; trigger.removeAttribute('data-placeholder'); }
      else if (valueEl && !valueEl.textContent.trim()) valueEl.textContent = placeholder;
      items().forEach((i) => { i.setAttribute('tabindex', '-1'); if (!i.hasAttribute('data-state')) FB.setState(i, 'unchecked'); });
      trigger.addEventListener('click', (e) => { e.preventDefault(); if (trigger.disabled) return; FB.isOpen(content) ? close() : open(); });
      trigger.addEventListener('keydown', (e) => { if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(e.key)) { e.preventDefault(); open(); } });
      content.addEventListener('keydown', (e) => {
        if (nav(e)) return;
        if (e.key === 'Enter' || e.key === ' ') { const it = e.target.closest('[data-slot="select-item"]'); if (it) { e.preventDefault(); select(it); } }
        if (e.key === 'Tab') { e.preventDefault(); close(); }
      });
      content.addEventListener('click', (e) => { const it = e.target.closest('[data-slot="select-item"]'); if (it) select(it); });
      content.addEventListener('pointermove', (e) => { const it = e.target.closest('[data-slot="select-item"]'); if (it && document.activeElement !== it) it.focus(); });
      wrapper.fbOpen = open; wrapper.fbClose = close; wrapper.fbSelect = select;
    },
  });
})(window.FlaskBasecoat);


/* ---- sidebar ---- */
/* Sidebar: expanded/collapsed state on the sidebar root (offcanvas or icon mode), trigger and rail toggles,
   keyboard shortcut Ctrl/Cmd+B, state remembered in a cookie like upstream, and a mobile sheet below 768px. */
(function (FB) {
  'use strict';

  const COOKIE = 'sidebar_state';
  const MOBILE = 768;

  FB.register('sidebar-wrapper', {
    init(wrapper) {
      const sidebars = FB.qsa(wrapper, '[data-slot="sidebar"]').filter((s) => s.closest('[data-slot="sidebar-wrapper"]') === wrapper);
      const sidebar = sidebars[0];
      if (!sidebar) return;
      const collapsible = sidebar.getAttribute('data-collapsible-mode') || (sidebar.hasAttribute('data-collapsible') ? 'offcanvas' : 'none');
      let open = sidebar.getAttribute('data-state') !== 'collapsed';
      const match = document.cookie.match(new RegExp(`(?:^|; )${COOKIE}=(true|false)`));
      if (match) open = match[1] === 'true';
      let mobileOpen = false;
      const isMobile = () => window.innerWidth < MOBILE;

      function apply() {
        if (collapsible === 'none') return;
        sidebar.setAttribute('data-state', open ? 'expanded' : 'collapsed');
        sidebar.setAttribute('data-collapsible', open ? '' : collapsible);
        FB.qsa(wrapper, '[data-slot="sidebar-trigger"]').forEach((t) => t.setAttribute('aria-expanded', String(open)));
        FB.emit(wrapper, 'sidebar', { open });
      }
      function toggle() {
        if (isMobile()) { mobileOpen = !mobileOpen; applyMobile(); return; }
        open = !open;
        document.cookie = `${COOKIE}=${open}; path=/; max-age=${60 * 60 * 24 * 7}`;
        apply();
      }
      // Mobile: the sidebar content is shown inside a sheet-like overlay on small screens.
      let mobileSheet = null;
      function applyMobile() {
        if (!mobileSheet) {
          mobileSheet = document.createElement('div');
          mobileSheet.setAttribute('data-fb-sidebar-mobile', '');
          mobileSheet.className = 'fixed inset-0 z-50 hidden';
          mobileSheet.innerHTML = '<div data-slot="sheet-overlay" data-state="open" class="cn-sheet-overlay fixed inset-0 z-50 bg-black/50"></div>' +
            '<div data-slot="sheet-content" data-state="open" data-side="left" role="dialog" aria-modal="true" data-sidebar="sidebar" data-mobile="true" class="cn-sheet-content fixed inset-y-0 left-0 z-50 flex h-full w-(--sidebar-width) flex-col bg-sidebar p-0 text-sidebar-foreground"><div class="flex h-full w-full flex-col" data-fb-mobile-slot></div></div>';
          mobileSheet.style.setProperty('--sidebar-width', '18rem');
          document.body.appendChild(mobileSheet);
          mobileSheet.firstElementChild.addEventListener('click', () => { mobileOpen = false; applyMobile(); });
        }
        const slot = FB.qs(mobileSheet, '[data-fb-mobile-slot]');
        const inner = FB.qs(sidebar, '[data-slot="sidebar-inner"]');
        if (mobileOpen) {
          mobileSheet.classList.remove('hidden');
          if (inner && inner.parentNode !== slot) { inner.fbHome = inner.parentNode; slot.appendChild(inner); }
          FB.lockScroll();
          FB.pushLayer(mobileSheet.fbLayer = { content: mobileSheet.lastElementChild, modal: true, onDismiss: () => { mobileOpen = false; applyMobile(); } });
        } else {
          mobileSheet.classList.add('hidden');
          if (inner && inner.fbHome) { inner.fbHome.appendChild(inner); }
          FB.unlockScroll();
          if (mobileSheet.fbLayer) { FB.removeLayer(mobileSheet.fbLayer); mobileSheet.fbLayer = null; }
        }
      }
      wrapper.addEventListener('click', (e) => {
        const t = e.target.closest('[data-slot="sidebar-trigger"], [data-slot="sidebar-rail"]');
        if (t && wrapper.contains(t)) { e.preventDefault(); toggle(); }
      });
      document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'b') { e.preventDefault(); toggle(); }
      });
      // Menu buttons marked data-active reflect the current page; links with the current path get it too.
      FB.qsa(wrapper, '[data-slot="sidebar-menu-button"][href], [data-slot="sidebar-menu-sub-button"][href]').forEach((a) => {
        try {
          const url = new URL(a.getAttribute('href'), location.href);
          if (url.pathname === location.pathname && a.getAttribute('data-active') === null) a.setAttribute('data-active', 'true');
        } catch (e) { /* ignore */ }
      });
      // Collapsible groups inside the sidebar use the generic collapsible module.
      apply();
      wrapper.fbToggle = toggle;
    },
  });
})(window.FlaskBasecoat);


/* ---- slider ---- */
/* Slider: pointer and keyboard control of one or more thumbs; range and thumb positions are written as inline
   styles the way Radix does (left/right or bottom/top percentages), and the value is mirrored into hidden inputs. */
(function (FB) {
  'use strict';

  FB.register('slider', {
    init(root) {
      const track = FB.qs(root, '[data-slot="slider-track"]');
      const range = FB.qs(root, '[data-slot="slider-range"]');
      const thumbs = FB.qsa(root, '[data-slot="slider-thumb"]');
      if (!track || !thumbs.length) return;
      const vertical = root.getAttribute('data-orientation') === 'vertical';
      const min = Number(thumbs[0].getAttribute('aria-valuemin') || root.getAttribute('data-min') || 0);
      const max = Number(thumbs[0].getAttribute('aria-valuemax') || root.getAttribute('data-max') || 100);
      const step = Number(root.getAttribute('data-step') || 1);
      const disabled = root.getAttribute('aria-disabled') === 'true' || root.hasAttribute('data-disabled');
      const name = root.getAttribute('data-name') || root.getAttribute('name');
      const values = thumbs.map((t, i) => {
        const v = t.getAttribute('aria-valuenow') ?? (root.getAttribute('data-value') || '').split(',')[i];
        return v !== null && v !== undefined && v !== '' ? Number(v) : min;
      });
      const inputs = name ? thumbs.map(() => { const i = document.createElement('input'); i.type = 'hidden'; i.name = name; root.appendChild(i); return i; }) : [];

      function pct(v) { return ((v - min) / (max - min)) * 100; }
      function render() {
        thumbs.forEach((t, i) => {
          t.setAttribute('aria-valuenow', String(values[i]));
          t.setAttribute('aria-valuemin', String(min));
          t.setAttribute('aria-valuemax', String(max));
          t.style.display = '';
          const p = pct(values[i]);
          t.parentElement.style.position = 'absolute';
          if (vertical) { t.parentElement.style.bottom = `calc(${p}% - var(--thumb-size, 0px))`; t.parentElement.style.left = ''; }
          else { t.parentElement.style.left = `calc(${p}% + var(--thumb-offset, 0px))`; t.parentElement.style.bottom = ''; }
          t.parentElement.style.transform = vertical ? 'translateY(50%)' : 'translateX(-50%)';
          if (inputs[i]) inputs[i].value = String(values[i]);
        });
        if (range) {
          const lo = values.length > 1 ? Math.min(...values) : min;
          const hi = Math.max(...values);
          if (vertical) { range.style.bottom = `${pct(lo)}%`; range.style.top = `${100 - pct(hi)}%`; }
          else { range.style.left = `${pct(lo)}%`; range.style.right = `${100 - pct(hi)}%`; }
        }
        root.setAttribute('data-value', values.join(','));
      }
      // Radix wraps each thumb in a positioned span; create it when the server did not.
      thumbs.forEach((t) => {
        if (!t.parentElement.hasAttribute('data-fb-thumb')) {
          const wrap = document.createElement('span');
          wrap.setAttribute('data-fb-thumb', '');
          wrap.style.transform = 'var(--radix-slider-thumb-transform)';
          wrap.style.position = 'absolute';
          t.parentNode.insertBefore(wrap, t);
          wrap.appendChild(t);
        }
      });
      function snap(v) { const s = Math.round((v - min) / step) * step + min; return Math.min(max, Math.max(min, Number(s.toFixed(6)))); }
      function valueFromPointer(e) {
        const r = track.getBoundingClientRect();
        const ratio = vertical ? 1 - (e.clientY - r.top) / r.height : (e.clientX - r.left) / r.width;
        return snap(min + Math.min(1, Math.max(0, ratio)) * (max - min));
      }
      function setValue(i, v) {
        v = snap(v);
        if (values.length > 1) {
          if (i > 0) v = Math.max(v, values[i - 1]);
          if (i < values.length - 1) v = Math.min(v, values[i + 1]);
        }
        if (values[i] === v) return;
        values[i] = v; render();
        FB.emit(root, 'change', { value: values.slice() });
      }
      let active = -1;
      root.addEventListener('pointerdown', (e) => {
        if (disabled || e.button !== 0) return;
        e.preventDefault();
        const v = valueFromPointer(e);
        let best = 0; thumbs.forEach((t, i) => { if (Math.abs(values[i] - v) < Math.abs(values[best] - v)) best = i; });
        active = best; setValue(active, v); thumbs[active].focus();
        root.setPointerCapture && root.setPointerCapture(e.pointerId);
      });
      root.addEventListener('pointermove', (e) => { if (active >= 0) setValue(active, valueFromPointer(e)); });
      root.addEventListener('pointerup', () => { active = -1; });
      root.addEventListener('pointercancel', () => { active = -1; });
      thumbs.forEach((t, i) => t.addEventListener('keydown', (e) => {
        if (disabled) return;
        const big = (max - min) / 10;
        const map = { ArrowRight: step, ArrowUp: step, ArrowLeft: -step, ArrowDown: -step, PageUp: big, PageDown: -big };
        if (e.key in map) { e.preventDefault(); setValue(i, values[i] + map[e.key] * (e.shiftKey ? 10 : 1)); }
        else if (e.key === 'Home') { e.preventDefault(); setValue(i, min); }
        else if (e.key === 'End') { e.preventDefault(); setValue(i, max); }
      }));
      render();
    },
  });
})(window.FlaskBasecoat);


/* ---- tabs ---- */
/* Tabs: role=tablist with arrow-key navigation (automatic activation), data-state active/inactive on triggers and panels. */
(function (FB) {
  'use strict';

  FB.register('tabs', {
    init(root) {
      const list = FB.qs(root, '[data-slot="tabs-list"]');
      if (!list) return;
      const triggers = () => FB.qsa(list, '[data-slot="tabs-trigger"]');
      const panels = () => FB.qsa(root, '[data-slot="tabs-content"]').filter((p) => p.closest('[data-slot="tabs"]') === root);
      const orientation = root.getAttribute('data-orientation') === 'vertical' ? 'vertical' : 'horizontal';
      triggers().forEach((t, i) => {
        const value = t.getAttribute('data-value') || String(i);
        t.setAttribute('data-value', value);
        const panel = panels().find((p) => (p.getAttribute('data-value') || String(panels().indexOf(p))) === value) || panels()[i];
        if (panel) {
          panel.setAttribute('data-value', value);
          t.setAttribute('aria-controls', FB.ensureId(panel, 'tabs-content'));
          panel.setAttribute('aria-labelledby', FB.ensureId(t, 'tabs-trigger'));
        }
      });
      function activate(trigger, focus) {
        triggers().forEach((t) => {
          const on = t === trigger;
          t.setAttribute('aria-selected', String(on));
          t.setAttribute('tabindex', on ? '0' : '-1');
          FB.setState(t, on ? 'active' : 'inactive');
        });
        const value = trigger.getAttribute('data-value');
        panels().forEach((p) => {
          const on = p.getAttribute('data-value') === value;
          FB.setState(p, on ? 'active' : 'inactive');
          if (on) p.removeAttribute('hidden'); else p.setAttribute('hidden', '');
        });
        if (focus) trigger.focus();
        FB.emit(root, 'change', { value });
      }
      const current = triggers().find((t) => t.getAttribute('data-state') === 'active') || triggers()[0];
      if (current) activate(current, false);
      const nav = FB.roving(triggers, { orientation, loop: true, typeahead: false });
      list.addEventListener('click', (e) => { const t = e.target.closest('[data-slot="tabs-trigger"]'); if (t && !t.disabled) activate(t, false); });
      list.addEventListener('keydown', (e) => { if (nav(e)) { const t = document.activeElement; if (t && t.matches('[data-slot="tabs-trigger"]')) activate(t, false); } });
    },
  });
})(window.FlaskBasecoat);


/* ---- toast ---- */
/* Toasts (Sonner-style): FlaskBasecoat.toast({title, description, variant, action, duration}) stacks toasts in a
   viewport in the bottom-right corner; flashes rendered server-side as [data-fb-flash] are promoted on load.
   Each toast is a data-slot="toast" element styled by the upstream cn-toast recipe. */
(function (FB) {
  'use strict';

  let viewport = null;
  function getViewport() {
    if (viewport) return viewport;
    viewport = document.querySelector('[data-slot="toast-viewport"]');
    if (!viewport) {
      viewport = document.createElement('div');
      viewport.setAttribute('data-slot', 'toast-viewport');
      viewport.setAttribute('tabindex', '-1');
      viewport.className = 'pointer-events-none fixed inset-x-4 bottom-4 z-50 mx-auto w-auto max-w-sm outline-none sm:right-4 sm:left-auto sm:mx-0 sm:w-full';
      document.body.appendChild(viewport);
    }
    return viewport;
  }
  const ICONS = {
    success: 'circle-check', info: 'info', warning: 'triangle-alert', error: 'octagon-x', loading: 'loader-circle',
  };
  function toast(opts) {
    opts = typeof opts === 'string' ? { title: opts } : (opts || {});
    const vp = getViewport();
    const el = document.createElement('div');
    el.setAttribute('data-slot', 'toast');
    el.setAttribute('role', opts.variant === 'error' ? 'alert' : 'status');
    el.setAttribute('aria-live', 'polite');
    el.setAttribute('data-type', opts.variant || 'default');
    el.setAttribute('data-state', 'open');
    el.className = 'cn-toast group/toast pointer-events-auto relative mt-3 flex w-full items-center gap-3 border bg-popover p-4 text-popover-foreground shadow-lg outline-none select-none data-[type=error]:text-destructive';
    const icon = opts.icon || (window.FlaskBasecoatIcons && window.FlaskBasecoatIcons[ICONS[opts.variant]]) || '';
    el.innerHTML =
      (icon ? `<div data-slot="toast-icon" class="cn-toast-icon flex shrink-0 items-center justify-center [&_svg]:size-4">${icon}</div>` : '') +
      `<div data-slot="toast-content" class="cn-toast-content flex flex-1 flex-col gap-0.5 text-sm">` +
      (opts.title ? `<div data-slot="toast-title" class="cn-toast-title font-medium"></div>` : '') +
      (opts.description ? `<div data-slot="toast-description" class="cn-toast-description text-muted-foreground"></div>` : '') +
      `</div>` +
      (opts.action ? `<button type="button" data-slot="toast-action" class="cn-button group/button inline-flex shrink-0 items-center justify-center whitespace-nowrap transition-all outline-none select-none cn-button-variant-outline cn-button-size-xs"></button>` : '') +
      (opts.dismissible === false ? '' : `<button type="button" data-slot="toast-close" aria-label="Close" class="cn-button group/button inline-flex shrink-0 items-center justify-center whitespace-nowrap transition-all outline-none select-none cn-button-variant-ghost cn-button-size-icon-xs absolute top-2 right-2 opacity-0 group-hover/toast:opacity-100">${(window.FlaskBasecoatIcons && window.FlaskBasecoatIcons.x) || '×'}</button>`);
    if (opts.title) FB.qs(el, '[data-slot="toast-title"]').textContent = opts.title;
    if (opts.description) FB.qs(el, '[data-slot="toast-description"]').textContent = opts.description;
    const actionBtn = FB.qs(el, '[data-slot="toast-action"]');
    if (actionBtn) { actionBtn.textContent = opts.action.label; actionBtn.addEventListener('click', () => { opts.action.onClick && opts.action.onClick(); dismiss(); }); }
    const closeBtn = FB.qs(el, '[data-slot="toast-close"]');
    if (closeBtn) closeBtn.addEventListener('click', dismiss);
    vp.appendChild(el);
    let timer = opts.duration === Infinity ? 0 : setTimeout(dismiss, opts.duration || 4000);
    el.addEventListener('pointerenter', () => { clearTimeout(timer); });
    el.addEventListener('pointerleave', () => { if (opts.duration !== Infinity) timer = setTimeout(dismiss, 2000); });
    function dismiss() {
      clearTimeout(timer);
      el.setAttribute('data-state', 'closed');
      el.setAttribute('data-fb-animating', '');
      setTimeout(() => el.remove(), 220);
      FB.emit(vp, 'toast-dismiss', { id: el.id });
    }
    return { element: el, dismiss };
  }
  FB.toast = toast;
  ['success', 'info', 'warning', 'error', 'loading'].forEach((v) => { toast[v] = (title, opts) => toast(Object.assign({ title, variant: v }, opts || {})); });

  // Server-rendered flash messages: <template data-fb-flash data-variant="success">text</template>
  document.addEventListener('DOMContentLoaded', () => {
    FB.qsa(document, '[data-fb-flash]').forEach((t) => {
      toast({ title: t.getAttribute('data-title') || (t.content ? t.content.textContent.trim() : t.textContent.trim()), description: t.getAttribute('data-description') || undefined, variant: t.getAttribute('data-variant') || 'default' });
      t.remove();
    });
  });
})(window.FlaskBasecoat);


/* ---- toggles ---- */
/* Checkbox, Switch, Radio Group, Toggle and Toggle Group.
   Each button-based control keeps aria-checked / aria-pressed and data-state in sync and mirrors its value into a
   hidden form input named by data-name (or the `name` attribute) so plain HTML forms submit it. */
(function (FB) {
  'use strict';

  function hiddenInput(control, name) {
    if (!name) return null;
    let input = control.fbInput;
    if (!input) {
      input = document.createElement('input');
      input.type = 'hidden';
      input.name = name;
      control.insertAdjacentElement('afterend', input);
      control.fbInput = input;
    }
    return input;
  }

  function setChecked(control, checked, indicatorSel) {
    control.setAttribute('aria-checked', checked === 'mixed' ? 'mixed' : String(checked));
    FB.setState(control, checked === 'mixed' ? 'indeterminate' : checked ? 'checked' : 'unchecked');
    const ind = indicatorSel && FB.qs(control, indicatorSel);
    if (ind) FB.setState(ind, checked ? 'checked' : 'unchecked');
    const name = control.getAttribute('name') || control.getAttribute('data-name');
    const input = hiddenInput(control, name);
    if (input) { input.value = control.getAttribute('value') || 'on'; input.disabled = !checked; }
    FB.emit(control, 'change', { checked });
  }

  ['checkbox', 'switch'].forEach((kind) => {
    FB.register(kind, {
      init(el) {
        const indicator = kind === 'checkbox' ? '[data-slot="checkbox-indicator"]' : '[data-slot="switch-thumb"]';
        if (kind === 'checkbox') {
          // The indicator exists in the DOM; Radix only renders it when checked. CSS hides it when unchecked.
          let ind = FB.qs(el, indicator);
          if (!ind) {
            ind = document.createElement('span');
            ind.setAttribute('data-slot', 'checkbox-indicator');
            ind.className = 'cn-checkbox-indicator grid place-content-center text-current transition-none';
            ind.style.pointerEvents = 'none';
            el.appendChild(ind);
          }
          if (!ind.firstElementChild && window.FlaskBasecoatIcons) ind.innerHTML = window.FlaskBasecoatIcons.check;
        }
        const name = el.getAttribute('name') || el.getAttribute('data-name');
        const initial = el.getAttribute('aria-checked') === 'mixed' ? 'mixed' : el.getAttribute('aria-checked') === 'true';
        if (name) { const input = hiddenInput(el, name); input.value = el.getAttribute('value') || 'on'; input.disabled = !initial; }
        el.addEventListener('click', (e) => {
          e.preventDefault();
          if (el.disabled || el.hasAttribute('data-disabled')) return;
          const checked = el.getAttribute('aria-checked') === 'true';
          setChecked(el, !checked, indicator);
        });
        el.addEventListener('keydown', (e) => { if (e.key === ' ') { e.preventDefault(); el.click(); } else if (e.key === 'Enter' && kind === 'switch') { e.preventDefault(); el.click(); } });
        // Click on the associated <label for=id> toggles the control (buttons are not labelable, so emulate it).
        if (el.id) FB.qsa(document, `label[for="${el.id}"]`).forEach((label) => label.addEventListener('click', (e) => { e.preventDefault(); el.click(); el.focus(); }));
      },
    });
  });

  FB.register('radio-group', {
    init(group) {
      const items = () => FB.qsa(group, '[data-slot="radio-group-item"]');
      const name = group.getAttribute('name') || group.getAttribute('data-name');
      let input = null;
      if (name) { input = document.createElement('input'); input.type = 'hidden'; input.name = name; group.appendChild(input); }
      function select(item, focus) {
        items().forEach((r) => {
          const on = r === item;
          r.setAttribute('aria-checked', String(on));
          FB.setState(r, on ? 'checked' : 'unchecked');
          r.setAttribute('tabindex', on ? '0' : '-1');
          let ind = FB.qs(r, '[data-slot="radio-group-indicator"]');
          if (on && !ind) {
            ind = document.createElement('span');
            ind.setAttribute('data-slot', 'radio-group-indicator');
            ind.className = 'cn-radio-group-indicator relative flex items-center justify-center';
            r.appendChild(ind);
          }
          if (ind) FB.setState(ind, on ? 'checked' : 'unchecked');
        });
        if (input) input.value = item.getAttribute('value') || '';
        if (focus) item.focus();
        FB.emit(group, 'change', { value: item.getAttribute('value') });
      }
      const checked = items().find((r) => r.getAttribute('aria-checked') === 'true');
      items().forEach((r, i) => r.setAttribute('tabindex', (checked ? r === checked : i === 0) ? '0' : '-1'));
      if (checked && input) input.value = checked.getAttribute('value') || '';
      const nav = FB.roving(items, { orientation: 'both', loop: true, typeahead: false });
      group.addEventListener('click', (e) => { const r = e.target.closest('[data-slot="radio-group-item"]'); if (r && !r.disabled) { e.preventDefault(); select(r, false); } });
      group.addEventListener('keydown', (e) => {
        const r = e.target.closest('[data-slot="radio-group-item"]');
        if (!r) return;
        if (nav(e)) { select(document.activeElement, false); return; }
        if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); select(r, false); }
      });
      items().forEach((r) => { if (r.id) FB.qsa(document, `label[for="${r.id}"]`).forEach((l) => l.addEventListener('click', (e) => { e.preventDefault(); select(r, true); })); });
    },
  });

  FB.register('toggle', {
    init(el) {
      if (el.closest('[data-slot="toggle-group"]')) return;
      el.addEventListener('click', (e) => {
        e.preventDefault();
        if (el.disabled) return;
        const on = el.getAttribute('aria-pressed') === 'true';
        el.setAttribute('aria-pressed', String(!on));
        FB.setState(el, on ? 'off' : 'on');
        FB.emit(el, 'change', { pressed: !on });
      });
    },
  });

  FB.register('toggle-group', {
    init(group) {
      const multiple = group.getAttribute('role') === 'toolbar' || group.getAttribute('data-type') === 'multiple';
      const items = () => FB.qsa(group, '[data-slot="toggle-group-item"]');
      items().forEach((it, i) => it.setAttribute('tabindex', i === 0 ? '0' : '-1'));
      function set(item, on) {
        FB.setState(item, on ? 'on' : 'off');
        if (item.getAttribute('role') === 'radio') item.setAttribute('aria-checked', String(on)); else item.setAttribute('aria-pressed', String(on));
      }
      group.addEventListener('click', (e) => {
        const it = e.target.closest('[data-slot="toggle-group-item"]');
        if (!it || it.disabled) return;
        e.preventDefault();
        const on = it.getAttribute('data-state') === 'on';
        if (multiple) set(it, !on);
        else items().forEach((o) => set(o, o === it ? !on : false));
        FB.emit(group, 'change', { value: items().filter((o) => o.getAttribute('data-state') === 'on').map((o) => o.getAttribute('data-value') || o.getAttribute('value')) });
      });
      const nav = FB.roving(items, { orientation: group.getAttribute('data-orientation') === 'vertical' ? 'vertical' : 'horizontal', loop: true, typeahead: false });
      group.addEventListener('keydown', (e) => { if (!nav(e) && (e.key === ' ' || e.key === 'Enter')) { const it = e.target.closest('[data-slot="toggle-group-item"]'); if (it) { e.preventDefault(); it.click(); } } });
    },
  });
})(window.FlaskBasecoat);
