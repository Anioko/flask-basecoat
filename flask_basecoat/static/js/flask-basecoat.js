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

/* ---- icons (generated from flask_basecoat/icons.py) ---- */
window.FlaskBasecoatIcons = {"check": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-check size-4\" aria-hidden=\"true\"><path d=\"M20 6 9 17l-5-5\" /></svg>", "circle": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-circle size-4\" aria-hidden=\"true\"><circle cx=\"12\" cy=\"12\" r=\"10\" /></svg>", "x": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-x size-4\" aria-hidden=\"true\"><path d=\"M18 6 6 18\" /><path d=\"m6 6 12 12\" /></svg>", "chevron-down": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-chevron-down size-4\" aria-hidden=\"true\"><path d=\"m6 9 6 6 6-6\" /></svg>", "chevron-up": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-chevron-up size-4\" aria-hidden=\"true\"><path d=\"m18 15-6-6-6 6\" /></svg>", "chevron-right": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-chevron-right size-4\" aria-hidden=\"true\"><path d=\"m9 18 6-6-6-6\" /></svg>", "chevron-left": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-chevron-left size-4\" aria-hidden=\"true\"><path d=\"m15 18-6-6 6-6\" /></svg>", "minus": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-minus size-4\" aria-hidden=\"true\"><path d=\"M5 12h14\" /></svg>", "loader-circle": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-loader-circle size-4\" aria-hidden=\"true\"><path d=\"M21 12a9 9 0 1 1-6.219-8.56\" /></svg>", "search": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-search size-4\" aria-hidden=\"true\"><path d=\"m21 21-4.34-4.34\" /><circle cx=\"11\" cy=\"11\" r=\"8\" /></svg>", "circle-check": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-circle-check size-4\" aria-hidden=\"true\"><circle cx=\"12\" cy=\"12\" r=\"10\" /><path d=\"m16 9-5.5 5.5L8 12\" /></svg>", "info": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-info size-4\" aria-hidden=\"true\"><circle cx=\"12\" cy=\"12\" r=\"10\" /><path d=\"M12 16v-4\" /><path d=\"M12 8h.01\" /></svg>", "triangle-alert": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-triangle-alert size-4\" aria-hidden=\"true\"><path d=\"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3\" /><path d=\"M12 9v4\" /><path d=\"M12 17h.01\" /></svg>", "octagon-x": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-octagon-x size-4\" aria-hidden=\"true\"><path d=\"m15 9-6 6\" /><path d=\"M2.586 16.726A2 2 0 0 1 2 15.312V8.688a2 2 0 0 1 .586-1.414l4.688-4.688A2 2 0 0 1 8.688 2h6.624a2 2 0 0 1 1.414.586l4.688 4.688A2 2 0 0 1 22 8.688v6.624a2 2 0 0 1-.586 1.414l-4.688 4.688a2 2 0 0 1-1.414.586H8.688a2 2 0 0 1-1.414-.586z\" /><path d=\"m9 9 6 6\" /></svg>", "ellipsis": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-ellipsis size-4\" aria-hidden=\"true\"><circle cx=\"12\" cy=\"12\" r=\"1\" /><circle cx=\"19\" cy=\"12\" r=\"1\" /><circle cx=\"5\" cy=\"12\" r=\"1\" /></svg>", "chevrons-up-down": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-chevrons-up-down size-4\" aria-hidden=\"true\"><path d=\"m7 15 5 5 5-5\" /><path d=\"m7 9 5-5 5 5\" /></svg>"};


/* ---- calendar ---- */
/* Calendar: renders the month grid the way react-day-picker renders it for shadcn (same classes and
   attributes as the upstream markup), with single, multiple and range selection, month navigation,
   month/year dropdowns when data-caption-layout="dropdown", week numbers and outside days.
   Configure through data attributes on [data-slot="calendar"]:
     data-mode="single|multiple|range" data-selected="2026-10-12" (comma separated / "start,end" for range)
     data-month="2026-10" data-number-of-months="2" data-week-starts-on="0" data-min / data-max (ISO dates)
     data-name="field" (hidden input name) data-caption-layout="label|dropdown" data-show-week-numbers
   A calendar rendered by the server already containing a grid is left alone until the user navigates. */
(function (FB) {
  'use strict';

  const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const pad = (n) => String(n).padStart(2, '0');
  const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const ddmmyyyy = (d) => `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
  const parse = (s) => { if (!s) return null; const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); };
  const same = (a, b) => a && b && a.getTime() === b.getTime();
  const ordinal = (n) => n + (n % 10 === 1 && n !== 11 ? 'st' : n % 10 === 2 && n !== 12 ? 'nd' : n % 10 === 3 && n !== 13 ? 'rd' : 'th');
  const CHEV = { left: '<path d="m15 18-6-6 6-6"/>', right: '<path d="m9 18 6-6-6-6"/>', down: '<path d="m6 9 6 6 6-6"/>' };
  const svg = (dir, cls, size) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size || 24}" height="${size || 24}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-${dir} ${cls}" aria-hidden="true">${CHEV[dir]}</svg>`;
  const BTN = 'cn-button group/button inline-flex shrink-0 items-center justify-center whitespace-nowrap transition-all outline-none select-none disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0';
  const DAY_BTN = `${BTN} cn-button-variant-ghost cn-button-size-icon cn-calendar-day-button relative isolate z-10 flex aspect-square size-auto w-full min-w-(--cell-size) flex-col gap-1 border-0 leading-none font-normal group-data-[focused=true]/day:relative group-data-[focused=true]/day:z-10 group-data-[focused=true]/day:border-ring group-data-[focused=true]/day:ring-[3px] group-data-[focused=true]/day:ring-ring/50 data-[range-end=true]:rounded-(--cell-radius) data-[range-end=true]:rounded-r-(--cell-radius) data-[range-end=true]:bg-primary data-[range-end=true]:text-primary-foreground data-[range-middle=true]:rounded-none data-[range-middle=true]:bg-muted data-[range-middle=true]:text-foreground data-[range-start=true]:rounded-(--cell-radius) data-[range-start=true]:rounded-l-(--cell-radius) data-[range-start=true]:bg-primary data-[range-start=true]:text-primary-foreground data-[selected-single=true]:bg-primary data-[selected-single=true]:text-primary-foreground dark:hover:text-foreground [&>span]:text-xs [&>span]:opacity-70`;
  const DAY_CELL = "group/day relative aspect-square h-full w-full rounded-(--cell-radius) p-0 text-center select-none [&:last-child[data-selected=true]_button]:rounded-r-(--cell-radius) [&:first-child[data-selected=true]_button]:rounded-l-(--cell-radius) rdp-day";

  FB.register('calendar', {
    init(root) {
      const mode = root.getAttribute('data-mode') || 'single';
      const months = Number(root.getAttribute('data-number-of-months') || 1);
      const weekStart = Number(root.getAttribute('data-week-starts-on') || 0);
      const showWeeks = root.hasAttribute('data-show-week-numbers') || root.getAttribute('data-week-numbers') === 'true';
      const dropdown = root.getAttribute('data-caption-layout') === 'dropdown';
      const min = parse(root.getAttribute('data-min')), max = parse(root.getAttribute('data-max'));
      const name = root.getAttribute('data-name');
      let selected = (root.getAttribute('data-selected') || '').split(',').filter(Boolean).map(parse);
      let range = mode === 'range' ? { from: selected[0] || null, to: selected[1] || null } : null;
      let view = parse((root.getAttribute('data-month') || '') + '-01') || selected[0] || new Date();
      view = new Date(view.getFullYear(), view.getMonth(), 1);
      let hidden = null;
      if (name) { hidden = document.createElement('input'); hidden.type = 'hidden'; hidden.name = name; root.appendChild(hidden); }
      const prerendered = !!FB.qs(root, '.rdp-months');
      if (prerendered && !root.hasAttribute('data-live')) {
        // Static server markup: only wire navigation and selection on top of it.
        root.setAttribute('data-live', '');
      }

      function isSelected(d) {
        if (mode === 'range') return range.from && (same(d, range.from) || same(d, range.to) || (range.to && d > range.from && d < range.to));
        return selected.some((s) => same(s, d));
      }
      function monthGrid(first) {
        const y = first.getFullYear(), m = first.getMonth();
        const start = new Date(y, m, 1);
        const offset = (start.getDay() - weekStart + 7) % 7;
        const gridStart = new Date(y, m, 1 - offset);
        const weeks = [];
        for (let w = 0; w < 6; w++) {
          const days = [];
          for (let i = 0; i < 7; i++) days.push(new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + w * 7 + i));
          if (w >= 4 && days[0].getMonth() !== m) break;
          weeks.push(days);
        }
        return weeks;
      }
      function weekNumber(d) {
        const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
        const day = t.getUTCDay() || 7; t.setUTCDate(t.getUTCDate() + 4 - day);
        const y0 = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
        return Math.ceil(((t - y0) / 86400000 + 1) / 7);
      }
      function render() {
        const today = new Date(); today.setHours(0, 0, 0, 0);
        const monthsHtml = [];
        for (let k = 0; k < months; k++) {
          const first = new Date(view.getFullYear(), view.getMonth() + k, 1);
          const label = `${MONTHS[first.getMonth()]} ${first.getFullYear()}`;
          const caption = dropdown
            ? `<div class="flex h-(--cell-size) w-full items-center justify-center gap-1.5 text-sm font-medium rdp-dropdowns">
                 <span data-disabled="false" class="cn-calendar-dropdown-root relative rounded-(--cell-radius) rdp-dropdown_root"><select aria-label="Choose the Month" data-fb-month class="absolute inset-0 bg-popover opacity-0 rdp-dropdown rdp-months_dropdown">${MONTHS.map((mn, i) => `<option value="${i}"${i === first.getMonth() ? ' selected' : ''}>${mn}</option>`).join('')}</select><span aria-hidden="true" class="font-medium select-none cn-calendar-caption-label flex items-center gap-1 rounded-(--cell-radius) text-sm [&>svg]:size-3.5 [&>svg]:text-muted-foreground rdp-caption_label">${MONTHS[first.getMonth()]}${svg('down', 'size-4 rdp-chevron', 18)}</span></span>
                 <span data-disabled="false" class="cn-calendar-dropdown-root relative rounded-(--cell-radius) rdp-dropdown_root"><select aria-label="Choose the Year" data-fb-year class="absolute inset-0 bg-popover opacity-0 rdp-dropdown rdp-years_dropdown">${Array.from({ length: 101 }, (_, i) => first.getFullYear() - 100 + i + 50).filter((yy) => yy >= 1926 && yy <= 2100).map((yy) => `<option value="${yy}"${yy === first.getFullYear() ? ' selected' : ''}>${yy}</option>`).join('')}</select><span aria-hidden="true" class="font-medium select-none cn-calendar-caption-label flex items-center gap-1 rounded-(--cell-radius) text-sm [&>svg]:size-3.5 [&>svg]:text-muted-foreground rdp-caption_label">${first.getFullYear()}${svg('down', 'size-4 rdp-chevron', 18)}</span></span>
               </div>`
            : `<span class="font-medium select-none cn-calendar-caption-label flex items-center gap-1 rounded-(--cell-radius) text-sm [&>svg]:size-3.5 [&>svg]:text-muted-foreground rdp-caption_label" role="status" aria-live="polite">${label}</span>`;
          const weekdays = Array.from({ length: 7 }, (_, i) => DAYS[(i + weekStart) % 7]);
          const rows = monthGrid(first).map((week) => {
            const cells = week.map((d) => {
              const outside = d.getMonth() !== first.getMonth();
              const disabled = (min && d < min) || (max && d > max);
              const sel = !!isSelected(d);
              const rs = mode === 'range' && range.from && same(d, range.from), re = mode === 'range' && range.to && same(d, range.to);
              const rm = mode === 'range' && range.from && range.to && d > range.from && d < range.to;
              const single = sel && mode !== 'range';
              const attrs = [`role="gridcell"`, `data-day="${iso(d)}"`, `data-month="${iso(first).slice(0, 7)}"`,
                outside ? 'data-outside="true"' : '', sel ? 'aria-selected="true" data-selected="true"' : '', same(d, today) ? 'data-today="true"' : '', disabled ? 'data-disabled="true" aria-disabled="true"' : ''];
              const btnAttrs = [`data-slot="button"`, `data-variant="ghost"`, `data-size="icon"`, `data-day="${ddmmyyyy(d)}"`, single ? 'data-selected-single="true"' : '',
                mode === 'range' ? `data-range-start="${!!rs}" data-range-end="${!!re}" data-range-middle="${!!rm}"` : '', 'type="button"', `tabindex="${sel ? 0 : -1}"`,
                `aria-label="${DAYS[d.getDay()]}, ${MONTHS[d.getMonth()]} ${ordinal(d.getDate())}, ${d.getFullYear()}${sel ? ', selected' : ''}"`, disabled ? 'disabled' : ''];
              return `<td ${attrs.join(' ')} class="${DAY_CELL}"><button ${btnAttrs.join(' ')} class="${DAY_BTN}">${d.getDate()}</button></td>`;
            }).join('');
            const wk = showWeeks ? `<td class="text-[0.8rem] text-muted-foreground select-none rdp-week_number"><div class="flex size-(--cell-size) items-center justify-center text-center">${weekNumber(week[0])}</div></td>` : '';
            return `<tr class="mt-2 flex w-full rdp-week">${wk}${cells}</tr>`;
          }).join('');
          monthsHtml.push(`<div class="flex w-full flex-col gap-4 rdp-month">
            <div class="flex h-(--cell-size) w-full items-center justify-center px-(--cell-size) rdp-month_caption">${caption}</div>
            <table role="grid" aria-multiselectable="${mode !== 'single'}" aria-label="${label}" class="w-full border-collapse rdp-month_grid">
              <thead aria-hidden="true"><tr class="flex rdp-weekdays">${showWeeks ? '<th class="w-(--cell-size) select-none rdp-week_number_header"></th>' : ''}${weekdays.map((wd) => `<th aria-label="${wd}" scope="col" class="flex-1 rounded-(--cell-radius) text-[0.8rem] font-normal text-muted-foreground select-none rdp-weekday">${wd.slice(0, 2)}</th>`).join('')}</tr></thead>
              <tbody class="rdp-weeks">${rows}</tbody>
            </table></div>`);
        }
        root.innerHTML = `<div class="relative flex flex-col gap-4 md:flex-row rdp-months">
          <nav aria-label="Navigation bar" class="absolute inset-x-0 top-0 flex w-full items-center justify-between gap-1 rdp-nav">
            <button type="button" data-fb-prev aria-label="Go to the Previous Month" class="${BTN} cn-button-variant-ghost cn-button-size-icon-sm cn-calendar-nav-button aria-disabled:opacity-50 rdp-button_previous">${svg('left', 'cn-rtl-flip size-4 rdp-chevron')}</button>
            <button type="button" data-fb-next aria-label="Go to the Next Month" class="${BTN} cn-button-variant-ghost cn-button-size-icon-sm cn-calendar-nav-button aria-disabled:opacity-50 rdp-button_next">${svg('right', 'cn-rtl-flip size-4 rdp-chevron')}</button>
          </nav>${monthsHtml.join('')}</div>`;
        if (hidden) {
          root.appendChild(hidden);
          hidden.value = mode === 'range' ? [range.from, range.to].filter(Boolean).map(iso).join(',') : selected.map(iso).join(',');
        }
        root.setAttribute('data-month', iso(view).slice(0, 7));
      }
      function select(d) {
        if (mode === 'single') selected = same(selected[0], d) && root.hasAttribute('data-deselectable') ? [] : [d];
        else if (mode === 'multiple') { const i = selected.findIndex((s) => same(s, d)); if (i >= 0) selected.splice(i, 1); else selected.push(d); }
        else {
          if (!range.from || (range.from && range.to)) range = { from: d, to: null };
          else if (d < range.from) range = { from: d, to: range.from };
          else range.to = d;
        }
        render();
        FB.emit(root, 'change', { value: mode === 'range' ? { from: range.from && iso(range.from), to: range.to && iso(range.to) } : selected.map(iso) });
      }
      root.addEventListener('click', (e) => {
        const prev = e.target.closest('[data-fb-prev], .rdp-button_previous'), next = e.target.closest('[data-fb-next], .rdp-button_next');
        if (prev) { view = new Date(view.getFullYear(), view.getMonth() - 1, 1); render(); return; }
        if (next) { view = new Date(view.getFullYear(), view.getMonth() + 1, 1); render(); return; }
        const cell = e.target.closest('td[data-day]');
        if (cell && !cell.hasAttribute('data-disabled')) select(parse(cell.getAttribute('data-day')));
      });
      root.addEventListener('change', (e) => {
        if (e.target.matches('[data-fb-month]')) { view = new Date(view.getFullYear(), Number(e.target.value), 1); render(); }
        if (e.target.matches('[data-fb-year]')) { view = new Date(Number(e.target.value), view.getMonth(), 1); render(); }
      });
      root.addEventListener('keydown', (e) => {
        const btn = e.target.closest('td[data-day] button');
        if (!btn) return;
        const d = parse(btn.closest('td').getAttribute('data-day'));
        const delta = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }[e.key];
        if (delta) {
          e.preventDefault();
          const n = new Date(d.getFullYear(), d.getMonth(), d.getDate() + delta);
          if (n.getMonth() !== view.getMonth() && months === 1) { view = new Date(n.getFullYear(), n.getMonth(), 1); render(); }
          const target = FB.qs(root, `td[data-day="${iso(n)}"] button`);
          if (target) { target.focus(); target.closest('td').setAttribute('data-focused', 'true'); }
        } else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(d); }
      });
      if (!prerendered || root.hasAttribute('data-render')) render();
      root.fbRender = render; root.fbSelect = select;
    },
  });
})(window.FlaskBasecoat);


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


/* ---- chart ---- */
/* Chart: an SVG renderer for the shadcn chart container.
   Upstream draws with Recharts; the style pack styles Recharts' class names (recharts-cartesian-grid lines,
   recharts-cartesian-axis-tick text, recharts-sector ...) and colours come from --color-<series> variables that
   the ChartContainer declares. This module reproduces that contract without React:
     <div data-slot="chart" data-chart="c1" data-chart-type="bar|stacked-bar|line|area|pie|donut|radial"
          data-chart-x="month" data-chart-data='[{"month":"Jan","desktop":186,"mobile":80}]'
          data-chart-series='[{"key":"desktop","label":"Desktop"},{"key":"mobile","label":"Mobile"}]'
          data-chart-legend data-chart-grid>
   Series colours default to --color-<key> (declared by the page) and then to --chart-1..5.
   Hover shows the ChartTooltipContent markup; a legend renders ChartLegendContent. */
(function (FB) {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';
  function el(tag, attrs, parent) {
    const n = document.createElementNS(NS, tag);
    Object.entries(attrs || {}).forEach(([k, v]) => n.setAttribute(k, String(v)));
    if (parent) parent.appendChild(n);
    return n;
  }
  function parse(root, name, fallback) {
    try { const v = root.getAttribute(name); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; }
  }
  function nice(max) {
    if (max <= 0) return 1;
    const p = Math.pow(10, Math.floor(Math.log10(max)));
    const n = max / p;
    const step = n <= 1 ? 0.25 : n <= 2 ? 0.5 : n <= 5 ? 1 : 2;
    return Math.ceil(n / step) * step * p;
  }
  function fmt(v) { return Number(v).toLocaleString(); }

  FB.register('chart', {
    init(root) {
      const data = parse(root, 'data-chart-data', null);
      if (!data || !Array.isArray(data) || !data.length) return; // static or externally rendered chart
      const type = root.getAttribute('data-chart-type') || 'bar';
      const xKey = root.getAttribute('data-chart-x') || Object.keys(data[0])[0];
      const series = parse(root, 'data-chart-series', Object.keys(data[0]).filter((k) => k !== xKey).map((k) => ({ key: k, label: k })));
      series.forEach((s, i) => { s.color = s.color || `var(--color-${s.key}, var(--chart-${(i % 5) + 1}))`; });
      const showGrid = root.hasAttribute('data-chart-grid') || !root.hasAttribute('data-chart-no-grid');
      const stacked = type === 'stacked-bar' || type === 'stacked-area';
      root.innerHTML = '';
      const container = document.createElement('div');
      container.className = 'recharts-responsive-container';
      container.style.cssText = 'width:100%;height:100%;min-width:0';
      const wrapper = document.createElement('div');
      wrapper.className = 'recharts-wrapper';
      wrapper.style.cssText = 'position:relative;cursor:default;width:100%;height:100%';
      container.appendChild(wrapper);
      root.appendChild(container);

      function draw() {
        wrapper.querySelectorAll('svg, .recharts-tooltip-wrapper, .recharts-legend-wrapper').forEach((n) => n.remove());
        const W = Math.max(200, root.clientWidth), H = Math.max(120, root.clientHeight);
        const svg = el('svg', { class: 'recharts-surface', width: W, height: H, viewBox: `0 0 ${W} ${H}` }, wrapper);
        const legendH = root.hasAttribute('data-chart-legend') ? 28 : 0;
        if (type === 'pie' || type === 'donut' || type === 'radial') return drawPie(svg, W, H - legendH);
        const m = { top: 12, right: 12, bottom: 28 + legendH, left: root.hasAttribute('data-chart-y-axis') ? 40 : 12 };
        const iw = W - m.left - m.right, ih = H - m.top - m.bottom;
        const totals = data.map((d) => stacked ? series.reduce((a, s) => a + (+d[s.key] || 0), 0) : Math.max(...series.map((s) => +d[s.key] || 0)));
        const maxV = nice(Math.max(...totals));
        const y = (v) => m.top + ih - (v / maxV) * ih;
        const n = data.length;
        const band = iw / n;
        // grid
        if (showGrid) {
          const grid = el('g', { class: 'recharts-cartesian-grid' }, svg);
          const gh = el('g', { class: 'recharts-cartesian-grid-horizontal' }, grid);
          for (let i = 0; i <= 4; i++) { const yy = m.top + (ih / 4) * i; el('line', { stroke: '#ccc', fill: 'none', x1: m.left, x2: m.left + iw, y1: yy, y2: yy }, gh); }
        }
        // x axis
        const axis = el('g', { class: 'recharts-cartesian-axis recharts-xAxis xAxis' }, svg);
        data.forEach((d, i) => {
          const tick = el('g', { class: 'recharts-cartesian-axis-tick' }, axis);
          const t = el('text', { x: m.left + band * i + band / 2, y: m.top + ih + 18, 'text-anchor': 'middle', class: 'recharts-text recharts-cartesian-axis-tick-value', fill: '#666' }, tick);
          const label = String(d[xKey] ?? '');
          el('tspan', {}, t).textContent = root.hasAttribute('data-chart-x-short') ? label.slice(0, 3) : label;
        });
        if (root.hasAttribute('data-chart-y-axis')) {
          const yaxis = el('g', { class: 'recharts-cartesian-axis recharts-yAxis yAxis' }, svg);
          for (let i = 0; i <= 4; i++) { const v = (maxV / 4) * i; const tick = el('g', { class: 'recharts-cartesian-axis-tick' }, yaxis); const t = el('text', { x: m.left - 8, y: y(v) + 4, 'text-anchor': 'end', class: 'recharts-text recharts-cartesian-axis-tick-value', fill: '#666' }, tick); el('tspan', {}, t).textContent = fmt(v); }
        }
        const hit = [];
        if (type === 'bar' || type === 'stacked-bar') {
          const gap = band * 0.2;
          const bw = stacked ? band - gap : (band - gap) / series.length;
          series.forEach((s, si) => {
            const layer = el('g', { class: 'recharts-layer recharts-bar' }, svg);
            data.forEach((d, i) => {
              const v = +d[s.key] || 0;
              const base = stacked ? series.slice(0, si).reduce((a, p) => a + (+d[p.key] || 0), 0) : 0;
              const x = m.left + band * i + gap / 2 + (stacked ? 0 : bw * si);
              const top = y(base + v), bottom = y(base);
              const r = Math.min(4, bw / 2);
              const path = stacked && si !== series.length - 1 ? `M${x},${bottom}h${bw}v${top - bottom}h${-bw}z` : `M${x},${bottom}v${-(bottom - top) + r}a${r},${r} 0 0 1 ${r},${-r}h${bw - 2 * r}a${r},${r} 0 0 1 ${r},${r}v${bottom - top - r}z`;
              el('path', { class: 'recharts-rectangle recharts-bar-rectangle', fill: s.color, d: path }, layer);
            });
          });
        } else {
          const points = (s) => data.map((d, i) => [m.left + band * i + band / 2, y(+d[s.key] || 0)]);
          series.forEach((s) => {
            const pts = points(s);
            const dLine = pts.map((p, i) => (i ? 'L' : 'M') + p[0] + ',' + p[1]).join('');
            if (type === 'area' || type === 'stacked-area') {
              el('path', { class: 'recharts-curve recharts-area-area', fill: s.color, 'fill-opacity': 0.4, stroke: 'none', d: dLine + `L${pts[pts.length - 1][0]},${y(0)}L${pts[0][0]},${y(0)}z` }, el('g', { class: 'recharts-layer recharts-area' }, svg));
            }
            el('path', { class: 'recharts-curve recharts-line-curve', fill: 'none', stroke: s.color, 'stroke-width': 2, d: dLine }, el('g', { class: 'recharts-layer recharts-line' }, svg));
            if (root.hasAttribute('data-chart-dots')) pts.forEach((p) => el('circle', { class: 'recharts-dot recharts-line-dot', r: 4, cx: p[0], cy: p[1], fill: s.color, stroke: '#fff', 'stroke-width': 2 }, svg));
          });
        }
        // hover regions and tooltip
        const cursor = el('path', { class: type.includes('bar') ? 'recharts-rectangle recharts-tooltip-cursor' : 'recharts-curve recharts-tooltip-cursor', fill: type.includes('bar') ? '#ccc' : 'none', stroke: '#ccc', 'fill-opacity': 0.3, style: 'display:none;pointer-events:none' }, svg);
        const tip = document.createElement('div');
        tip.className = 'recharts-tooltip-wrapper';
        tip.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;visibility:hidden;z-index:1';
        tip.innerHTML = '<div data-slot="chart-tooltip" class="cn-chart-tooltip grid min-w-32 items-start"><div class="cn-chart-tooltip-label font-medium"></div><div class="grid gap-1.5"></div></div>';
        wrapper.appendChild(tip);
        data.forEach((d, i) => {
          const zone = el('rect', { x: m.left + band * i, y: m.top, width: band, height: ih, fill: 'transparent' }, svg);
          zone.addEventListener('pointerenter', () => {
            cursor.setAttribute('d', type.includes('bar') ? `M${m.left + band * i},${m.top}h${band}v${ih}h${-band}z` : `M${m.left + band * i + band / 2},${m.top}v${ih}`);
            cursor.style.display = '';
            tip.querySelector('.cn-chart-tooltip-label').textContent = String(d[xKey] ?? '');
            tip.querySelector('.grid.gap-1\\.5').innerHTML = series.map((s) => `<div class="flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 [&>svg]:text-muted-foreground items-center"><div class="shrink-0 rounded-[2px] border-(--color-border) bg-(--color-bg) h-2.5 w-2.5" style="--color-bg:${s.color};--color-border:${s.color}"></div><div class="flex flex-1 justify-between leading-none items-center"><div class="grid gap-1.5"><span class="text-muted-foreground">${s.label}</span></div><span class="font-mono font-medium text-foreground tabular-nums">${fmt(d[s.key] || 0)}</span></div></div>`).join('');
            tip.style.visibility = 'visible';
            const x = m.left + band * i + band / 2;
            tip.style.transform = `translate(${Math.min(W - tip.offsetWidth - 4, Math.max(0, x + 12))}px, ${m.top}px)`;
          });
          zone.addEventListener('pointerleave', () => { cursor.style.display = 'none'; tip.style.visibility = 'hidden'; });
          hit.push(zone);
        });
        if (legendH) drawLegend(W, H);
      }
      function drawPie(svg, W, H) {
        const cx = W / 2, cy = H / 2, R = Math.min(W, H) / 2 - 8;
        const inner = type === 'donut' ? R * 0.6 : 0;
        const key = series[0].key;
        const total = data.reduce((a, d) => a + (+d[key] || 0), 0) || 1;
        let a0 = -Math.PI / 2;
        const g = el('g', { class: 'recharts-layer recharts-pie' }, svg);
        data.forEach((d, i) => {
          const v = +d[key] || 0, a1 = a0 + (v / total) * Math.PI * 2;
          const color = d.fill || `var(--color-${String(d[xKey]).toLowerCase().replace(/\s+/g, '-')}, var(--chart-${(i % 5) + 1}))`;
          const p = (r, a) => [cx + r * Math.cos(a), cy + r * Math.sin(a)];
          const [x0, y0] = p(R, a0), [x1, y1] = p(R, a1), [ix0, iy0] = p(inner, a0), [ix1, iy1] = p(inner, a1);
          const large = a1 - a0 > Math.PI ? 1 : 0;
          const dPath = inner ? `M${x0},${y0}A${R},${R} 0 ${large} 1 ${x1},${y1}L${ix1},${iy1}A${inner},${inner} 0 ${large} 0 ${ix0},${iy0}z` : `M${cx},${cy}L${x0},${y0}A${R},${R} 0 ${large} 1 ${x1},${y1}z`;
          const sector = el('path', { class: 'recharts-sector', fill: color, stroke: '#fff', d: dPath }, g);
          sector.setAttribute('role', 'img');
          sector.setAttribute('aria-label', `${d[xKey]}: ${fmt(v)}`);
          a0 = a1;
        });
        if (root.hasAttribute('data-chart-legend')) drawLegend(W, H + 28);
      }
      function drawLegend(W, H) {
        const legend = document.createElement('div');
        legend.className = 'recharts-legend-wrapper';
        legend.style.cssText = `position:absolute;width:${W}px;left:0;bottom:0`;
        const items = type === 'pie' || type === 'donut' ? data.map((d, i) => ({ label: d[xKey], color: d.fill || `var(--color-${String(d[xKey]).toLowerCase().replace(/\s+/g, '-')}, var(--chart-${(i % 5) + 1}))` })) : series.map((s) => ({ label: s.label, color: s.color }));
        legend.innerHTML = `<div data-slot="chart-legend" class="flex items-center justify-center gap-4 pt-3">${items.map((it) => `<div class="[&>svg]:text-muted-foreground flex items-center gap-1.5 [&>svg]:h-3 [&>svg]:w-3"><div class="h-2 w-2 shrink-0 rounded-[2px]" style="background-color:${it.color}"></div>${it.label}</div>`).join('')}</div>`;
        wrapper.appendChild(legend);
      }
      draw();
      new ResizeObserver(() => draw()).observe(root);
      root.fbRedraw = draw;
    },
  });
})(window.FlaskBasecoat);


/* ---- combobox ---- */
/* Combobox and Command: filterable lists.
   Combobox: a trigger button or an input opens a listbox; typing filters items; arrows move the highlight
   (data-highlighted / aria-selected), Enter selects, Escape closes. Multi-select variants keep chips.
   Command: the same filtering over an always-visible list (or inside a dialog), with groups hidden when empty. */
(function (FB) {
  'use strict';

  function norm(s) { return (s || '').toLowerCase().trim(); }

  function listController(list, opts) {
    const itemSel = opts.itemSel;
    const items = () => FB.qsa(list, itemSel);
    const visible = () => items().filter((i) => !i.hidden && i.getAttribute('data-disabled') !== 'true' && i.getAttribute('aria-disabled') !== 'true');
    let highlighted = null;
    function highlight(item) {
      items().forEach((i) => { i.removeAttribute('data-highlighted'); i.setAttribute('aria-selected', 'false'); i.setAttribute('data-selected', 'false'); });
      highlighted = item || null;
      if (item) {
        item.setAttribute('data-highlighted', ''); item.setAttribute('aria-selected', 'true'); item.setAttribute('data-selected', 'true');
        item.scrollIntoView({ block: 'nearest' });
        if (opts.input) opts.input.setAttribute('aria-activedescendant', FB.ensureId(item, 'option'));
      }
    }
    function filter(query) {
      const q = norm(query);
      let count = 0;
      items().forEach((i) => {
        const text = norm(i.getAttribute('data-value') || '') + ' ' + norm(i.textContent) + ' ' + norm(i.getAttribute('data-keywords') || '');
        const show = !q || text.includes(q);
        i.hidden = !show;
        if (show) count++;
      });
      FB.qsa(list, opts.groupSel || '[role="presentation"][cmdk-group], [data-slot$="-group"]').forEach((g) => {
        const any = FB.qsa(g, itemSel).some((i) => !i.hidden);
        g.hidden = !any;
      });
      FB.qsa(list, opts.separatorSel || '[role="separator"]').forEach((s) => { s.hidden = !!q; });
      const empty = FB.qs(list, opts.emptySel || '[data-slot$="-empty"]');
      if (empty) empty.hidden = count > 0;
      if (!highlighted || highlighted.hidden) highlight(visible()[0] || null);
      return count;
    }
    function move(delta) {
      const v = visible();
      if (!v.length) return;
      const idx = v.indexOf(highlighted);
      const next = idx < 0 ? (delta > 0 ? 0 : v.length - 1) : Math.max(0, Math.min(v.length - 1, idx + delta));
      highlight(v[next]);
    }
    list.addEventListener('pointermove', (e) => { const it = e.target.closest(itemSel); if (it && !it.hidden && it !== highlighted) highlight(it); });
    return { items, visible, highlight, filter, move, get highlighted() { return highlighted; } };
  }

  /* ---- Command ---- */
  FB.register('command', {
    init(root) {
      const input = FB.qs(root, '[data-slot="command-input"]');
      const list = FB.qs(root, '[data-slot="command-list"]');
      if (!list) return;
      const ctl = listController(list, { itemSel: '[data-slot="command-item"]', input, groupSel: '[data-slot="command-group"]', separatorSel: '[data-slot="command-separator"]', emptySel: '[data-slot="command-empty"]' });
      if (input) {
        input.setAttribute('aria-controls', FB.ensureId(list, 'command-list'));
        input.addEventListener('input', () => ctl.filter(input.value));
        input.addEventListener('keydown', (e) => {
          if (e.key === 'ArrowDown') { e.preventDefault(); ctl.move(1); }
          else if (e.key === 'ArrowUp') { e.preventDefault(); ctl.move(-1); }
          else if (e.key === 'Home') { e.preventDefault(); ctl.highlight(ctl.visible()[0]); }
          else if (e.key === 'End') { e.preventDefault(); const v = ctl.visible(); ctl.highlight(v[v.length - 1]); }
          else if (e.key === 'Enter') { e.preventDefault(); const h = ctl.highlighted; if (h) h.click(); }
        });
      }
      list.addEventListener('click', (e) => {
        const it = e.target.closest('[data-slot="command-item"]');
        if (!it || it.getAttribute('data-disabled') === 'true') return;
        FB.emit(root, 'select', { value: it.getAttribute('data-value') || it.textContent.trim(), item: it });
        const dialog = root.closest('[data-slot="dialog-content"]');
        if (dialog) { const w = dialog.closest('[data-fb="dialog"]'); if (w && w.fbClose) w.fbClose(); }
      });
      ctl.filter('');
      root.fbCommand = ctl;
    },
  });

  /* Command dialog keyboard shortcut: data-fb-shortcut="k" on the dialog wrapper opens it with Ctrl/Cmd+K. */
  document.addEventListener('keydown', (e) => {
    if (!(e.metaKey || e.ctrlKey)) return;
    FB.qsa(document, '[data-fb-shortcut]').forEach((w) => {
      if (e.key.toLowerCase() === w.getAttribute('data-fb-shortcut').toLowerCase()) { e.preventDefault(); w.fbOpen && w.fbOpen(); }
    });
  });

  /* ---- Combobox ---- */
  FB.register('combobox', {
    selector: '[data-slot="combobox-content"]',
    init(content) {
      const trigger = FB.pairWith(content, '[data-slot="combobox-trigger"], [data-slot="input-group-button"][role="combobox"]');
      const input = FB.pairWith(content, '[data-slot="combobox-input"], [data-slot="combobox-chip-input"], [data-slot="input-group-control"][role="combobox"]');
      if (!trigger && !input) return;
      // the host is the visible control group the content belongs to
      const host = (input || trigger).closest('[data-slot="combobox-chips"], [data-slot="input-group"]') || trigger || input;
      const valueEl = trigger && FB.qs(trigger, '[data-slot="combobox-value"]');
      const clear = FB.qs(host, '[data-slot="combobox-clear"]') || FB.pairWith(content, '[data-slot="combobox-clear"]');
      const chips = host.matches('[data-slot="combobox-chips"]') ? host : FB.qs(host, '[data-slot="combobox-chips"]');
      const list = FB.qs(content, '[data-slot="combobox-list"]') || content;
      const anchor = host;
      const multiple = !!chips || host.hasAttribute('data-multiple') || content.hasAttribute('data-multiple');
      const name = host.getAttribute('data-name') || content.getAttribute('data-name') || (trigger && trigger.getAttribute('data-name')) || (input && input.getAttribute('name'));
      content.setAttribute('data-floating', ''); content.setAttribute('data-popper-var', 'combobox');
      const id = FB.ensureId(content, 'combobox');
      [trigger, input].forEach((t) => t && t.setAttribute('aria-controls', id));
      const ctl = listController(list, { itemSel: '[data-slot="combobox-item"]', input, groupSel: '[data-slot="combobox-group"]', separatorSel: '[data-slot="combobox-separator"]', emptySel: '[data-slot="combobox-empty"]' });
      const placeholder = valueEl ? valueEl.textContent : '';
      let selected = multiple ? [] : null;
      let layer = null;
      const hidden = () => { let h = host.fbHidden; if (!h && name && !(input && input.getAttribute('name') === name)) { h = document.createElement('input'); h.type = 'hidden'; h.name = name; h.setAttribute('data-fb-combobox', ''); host.insertAdjacentElement('afterend', h); host.fbHidden = h; } return h || null; };

      function reposition() { FB.float(anchor, content, { side: content.getAttribute('data-side') || 'bottom', align: content.getAttribute('data-align') || 'start', sideOffset: Number(content.getAttribute('data-side-offset') || 4), alignOffset: Number(content.getAttribute('data-align-offset') || 0) }); }
      function open() {
        if (FB.isOpen(content)) return;
        if (content.parentNode !== document.body) document.body.appendChild(content);
        FB.setState(content, 'open');
        [trigger, input].forEach((t) => { if (t) { t.setAttribute('aria-expanded', 'true'); if (t === trigger) FB.setState(t, 'open'); } });
        reposition();
        content.style.setProperty('--anchor-width', `${anchor.getBoundingClientRect().width}px`);
        layer = { content, trigger: anchor, modal: false, reposition, onDismiss: () => close() };
        FB.pushLayer(layer);
        ctl.filter(input && document.activeElement === input ? input.value : '');
        if (!input) content.focus({ preventScroll: true });
      }
      function close() {
        if (!FB.isOpen(content)) return;
        FB.setState(content, 'closed');
        [trigger, input].forEach((t) => { if (t) { t.setAttribute('aria-expanded', 'false'); if (t === trigger) FB.setState(t, 'closed'); } });
        if (layer) { FB.removeLayer(layer); layer = null; }
      }
      function labelOf(item) { return (FB.qs(item, '[data-slot="combobox-item-text"]') || item).textContent.trim(); }
      function valueOf(item) { return item.getAttribute('data-value') || item.getAttribute('value') || labelOf(item); }
      function renderChips() {
        if (!chips) return;
        FB.qsa(chips, '[data-slot="combobox-chip"]').forEach((c) => c.remove());
        const inputEl = FB.qs(chips, '[data-slot="combobox-chip-input"]');
        selected.forEach((item) => {
          const chip = document.createElement('div');
          chip.setAttribute('data-slot', 'combobox-chip'); chip.setAttribute('tabindex', '-1');
          chip.className = 'cn-combobox-chip has-disabled:pointer-events-none has-disabled:cursor-not-allowed has-disabled:opacity-50 has-disabled:text-muted-foreground';
          chip.innerHTML = `<span>${labelOf(item).replace(/</g, '&lt;')}</span><button type="button" data-slot="combobox-chip-remove" data-variant="ghost" data-size="icon-xs" tabindex="-1" aria-label="Remove" class="cn-button group/button inline-flex shrink-0 items-center justify-center whitespace-nowrap transition-all outline-none select-none cn-button-variant-ghost cn-button-size-icon-xs cn-combobox-chip-remove">${(window.FlaskBasecoatIcons && window.FlaskBasecoatIcons.x) || '×'}</button>`;
          chip.querySelector('button').addEventListener('click', (e) => { e.stopPropagation(); toggleItem(item); });
          chips.insertBefore(chip, inputEl);
        });
      }
      function sync() {
        const values = multiple ? selected.map(valueOf) : (selected ? [valueOf(selected)] : []);
        const h = hidden(); if (h) h.value = values.join(',');
        host.setAttribute('data-value', values.join(','));
        if (valueEl) { valueEl.textContent = multiple ? (values.length ? selected.map(labelOf).join(', ') : placeholder) : (selected ? labelOf(selected) : placeholder); }
        if (input && !multiple && selected) input.value = labelOf(selected);
        if (clear) clear.toggleAttribute('data-visible', values.length > 0);
        ctl.items().forEach((i) => { const on = multiple ? selected.includes(i) : i === selected; i.setAttribute('data-checked', String(on)); i.setAttribute('aria-selected', String(on || i === ctl.highlighted)); const ind = FB.qs(i, '[data-slot="combobox-item-indicator"]'); if (ind) ind.style.visibility = on ? '' : 'hidden'; });
        renderChips();
        FB.emit(host, 'change', { value: multiple ? values : values[0] || null });
      }
      function toggleItem(item) {
        if (multiple) { const i = selected.indexOf(item); if (i >= 0) selected.splice(i, 1); else selected.push(item); sync(); if (input) { input.value = ''; ctl.filter(''); input.focus(); } }
        else { selected = item; sync(); close(); (trigger || input).focus(); }
      }
      // preselected
      const pre = ctl.items().filter((i) => i.getAttribute('data-checked') === 'true' || i.getAttribute('data-selected') === 'true' || i.hasAttribute('data-preselected'));
      if (multiple) selected = pre; else selected = pre[0] || null;
      if (pre.length) sync(); else if (clear) clear.toggleAttribute('data-visible', false);
      if (trigger) {
        trigger.addEventListener('click', (e) => { e.preventDefault(); FB.isOpen(content) ? close() : open(); if (input && FB.isOpen(content)) input.focus(); });
        trigger.addEventListener('keydown', (e) => { if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(e.key)) { e.preventDefault(); open(); if (!input) ctl.move(1); } });
      }
      if (input) {
        input.addEventListener('focus', () => { if (!host.hasAttribute('data-open-on-click-only')) open(); });
        input.addEventListener('click', open);
        input.addEventListener('input', () => { open(); ctl.filter(input.value); if (!multiple && selected && labelOf(selected) !== input.value) { selected = null; const h = hidden(); if (h) h.value = ''; } });
        input.addEventListener('keydown', (e) => {
          if (e.key === 'ArrowDown') { e.preventDefault(); open(); ctl.move(1); }
          else if (e.key === 'ArrowUp') { e.preventDefault(); open(); ctl.move(-1); }
          else if (e.key === 'Enter') { const h = ctl.highlighted; if (FB.isOpen(content) && h) { e.preventDefault(); toggleItem(h); } }
          else if (e.key === 'Escape') { close(); }
          else if (e.key === 'Backspace' && multiple && !input.value && selected.length) { selected.pop(); sync(); }
        });
      }
      content.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown') { e.preventDefault(); ctl.move(1); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); ctl.move(-1); }
        else if (e.key === 'Enter' || e.key === ' ') { const h = ctl.highlighted; if (h) { e.preventDefault(); toggleItem(h); } }
      });
      list.addEventListener('click', (e) => { const it = e.target.closest('[data-slot="combobox-item"]'); if (it && it.getAttribute('aria-disabled') !== 'true') toggleItem(it); });
      if (clear) clear.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); selected = multiple ? [] : null; if (input) input.value = ''; sync(); ctl.filter(''); });
      content.fbOpen = open; content.fbClose = close; host.fbOpen = open; host.fbClose = close;
    },
  });
})(window.FlaskBasecoat);


/* ---- dialog ---- */
/* Dialog, Alert Dialog, Sheet and Drawer: modal layers.
   Markup (server-rendered, same DOM as upstream): a trigger, then an overlay and a content element. The runtime
   pairs each content with the nearest preceding trigger of its kind in document order (FB.pairWith); any element
   with data-fb-open="<content id>" opens it too. Behaviour mirrors Radix Dialog: aria-expanded/data-state on the
   trigger, scroll lock, focus trap, focus restore, Escape and overlay click dismiss (alert-dialog ignores overlay
   click), exit animation before hiding. */
(function (FB) {
  'use strict';

  function setup(kind, content) {
    const id = FB.ensureId(content, kind);
    const trigger = FB.pairWith(content, `[data-slot="${kind}-trigger"]`);
    const overlay = FB.pairWith(content, `[data-slot="${kind}-overlay"]`, { adjacent: true });
    if (trigger) trigger.setAttribute('aria-controls', id);
    const title = FB.qs(content, `[data-slot="${kind}-title"]`);
    const desc = FB.qs(content, `[data-slot="${kind}-description"]`);
    if (title && !content.hasAttribute('aria-labelledby')) content.setAttribute('aria-labelledby', FB.ensureId(title, `${kind}-title`));
    if (desc && !content.hasAttribute('aria-describedby')) content.setAttribute('aria-describedby', FB.ensureId(desc, `${kind}-description`));
    let layer = null, untrap = null, previouslyFocused = null, closing = null, opener = null;

    function finishHide() {
      [overlay, content].forEach((el) => el && el.removeAttribute('data-fb-animating'));
      closing = null;
    }
    function open(from) {
      if (FB.isOpen(content)) return;
      if (closing) { clearTimeout(closing); finishHide(); }
      opener = from || null;
      previouslyFocused = document.activeElement;
      // Portal to <body> so stacking is independent of the trigger's ancestors.
      if (overlay && overlay.parentNode !== document.body) document.body.appendChild(overlay);
      if (content.parentNode !== document.body) document.body.appendChild(content);
      [overlay, content].forEach((el) => el && FB.setState(el, 'open'));
      if (trigger) { FB.setState(trigger, 'open'); trigger.setAttribute('aria-expanded', 'true'); }
      FB.lockScroll();
      untrap = FB.trapFocus(content);
      layer = {
        content, trigger, modal: true,
        onDismiss(reason, e) {
          if (reason === 'outside' && (kind === 'alert-dialog' || (e && content.contains(e.target)))) return;
          close();
        },
      };
      FB.pushLayer(layer);
      FB.focusFirst(content, '[data-autofocus], [autofocus]');
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
      // Radix returns focus to the trigger; fall back to whatever had focus before opening.
      const target = (opener && opener.isConnected) ? opener : (trigger && trigger.isConnected ? trigger : previouslyFocused);
      if (target && target.focus) target.focus({ preventScroll: true });
      FB.emit(content, 'close', { kind });
    }
    if (trigger) trigger.addEventListener('click', (e) => { e.preventDefault(); open(trigger); });
    content.addEventListener('click', (e) => {
      const btn = e.target.closest(`[data-slot="${kind}-close"], [data-slot="${kind}-cancel"], [data-slot="${kind}-action"], [data-fb-close]`);
      if (btn && content.contains(btn)) { e.preventDefault(); close(); }
    });
    if (overlay) overlay.addEventListener('click', (e) => { if (e.target === overlay && kind !== 'alert-dialog') close(); });
    content.fbOpen = open; content.fbClose = close;
    if (trigger) { trigger.fbOpen = open; trigger.fbClose = close; }
    if (content.getAttribute('data-state') === 'open') { FB.setState(content, 'closed'); open(); }
    document.addEventListener('click', (e) => {
      const from = e.target.closest && e.target.closest(`[data-fb-open="${id}"]`);
      if (from) { e.preventDefault(); open(from); }
    });
  }

  ['dialog', 'alert-dialog', 'sheet', 'drawer'].forEach((kind) => {
    FB.register(kind, { selector: `[data-slot="${kind}-content"]`, init: (el) => setup(kind, el) });
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
        // The trigger is usually [data-slot=kind-trigger]; with asChild upstream it keeps the child's slot (sidebar-group-label, sidebar-menu-button).
        const trigger = FB.qs(root, `[data-slot="${kind}-trigger"]`) || FB.qsa(root, '[aria-expanded]').find((t) => t.closest(`[data-slot="${kind}"]`) === root);
        const content = FB.qs(root, `[data-slot="${kind}-content"]`);
        if (!trigger) return;
        if (content) trigger.setAttribute('aria-controls', FB.ensureId(content, `${kind}-content`));
        trigger.addEventListener('click', (e) => {
          e.preventDefault();
          const isOpen = trigger.getAttribute('aria-expanded') === 'true';
          if (content) toggleContent(trigger, content, !isOpen, '--radix-collapsible-content-height');
          else {
            // No panel upstream (state-driven content): only the state flips; CSS swaps [data-fb-preview]/[data-fb-full].
            FB.setState(trigger, isOpen ? 'closed' : 'open');
            trigger.setAttribute('aria-expanded', String(!isOpen));
            FB.setState(root, isOpen ? 'closed' : 'open');
          }
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

  /* Radix renders the indicator icon only while checked. */
  function setIndicator(item, on, icon) {
    const ind = item.querySelector('[class*="item-indicator"]');
    if (!ind) return;
    const icons = window.FlaskBasecoatIcons || {};
    ind.innerHTML = on ? (icons[icon] || '') : '';
  }

  function setupMenu(kind, content, opts) {
    const trigger = FB.pairWith(content, `[data-slot="${kind}-trigger"]`);
    if (!trigger) return null;
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
        // Keep the menu inside the viewport, flipping like Radix does near the edges.
        const r = content.getBoundingClientRect();
        const vw = document.documentElement.clientWidth, vh = document.documentElement.clientHeight;
        let x = anchorPoint.x, y = anchorPoint.y;
        if (x + r.width > vw - 8) x = Math.max(8, anchorPoint.x - r.width);
        if (y + r.height > vh - 8) y = Math.max(8, anchorPoint.y - r.height);
        content.style.transform = `translate(${Math.round(x)}px, ${Math.round(y)}px)`;
        content.setAttribute('data-side', y < anchorPoint.y ? 'top' : 'bottom'); content.setAttribute('data-align', 'start');
      } else FB.float(trigger, content, { side, align, sideOffset: Number(content.getAttribute('data-side-offset') || 4), alignOffset: Number(content.getAttribute('data-align-offset') || 0) });
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
        setIndicator(item, !checked, 'check');
        FB.emit(item, 'change', { checked: !checked, value: item.getAttribute('data-value') });
        return;
      }
      if (item.getAttribute('role') === 'menuitemradio') {
        const group = item.closest('[role="group"]') || content;
        FB.qsa(group, '[role="menuitemradio"]').forEach((r) => { r.setAttribute('aria-checked', 'false'); FB.setState(r, 'unchecked'); setIndicator(r, false, 'circle'); });
        item.setAttribute('aria-checked', 'true'); FB.setState(item, 'checked'); setIndicator(item, true, 'circle');
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

    /* submenus: a sub-content follows its sub-trigger inside the menu */
    const subs = FB.qsa(content, `[data-slot="${kind}-sub-content"]`).map((sc) => {
      const st = FB.pairWith(sc, `[data-slot="${kind}-sub-trigger"]`);
      if (!st) return null;
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
    content.fbOpen = open; content.fbClose = close; trigger.fbOpen = open; trigger.fbClose = close;
    return api;
  }

  FB.register('dropdown-menu', { selector: '[data-slot="dropdown-menu-content"]', init: (el) => setupMenu('dropdown-menu', el, {}) });
  FB.register('context-menu', { selector: '[data-slot="context-menu-content"]', init: (el) => setupMenu('context-menu', el, {}) });

  /* Menubar: a row of menus; hovering across triggers while one is open switches menus. */
  FB.register('menubar', {
    selector: '[data-slot="menubar"]',
    init(bar) {
      // Each trigger inside the bar is followed (in document order) by its content.
      const triggersInBar = FB.qsa(bar, '[data-slot="menubar-trigger"]');
      const menus = FB.qsa(document, '[data-slot="menubar-content"]')
        .filter((c) => { const t = FB.qsa(document, '[data-slot="menubar-trigger"]').filter((x) => !x.fbPaired && (x.compareDocumentPosition(c) & Node.DOCUMENT_POSITION_FOLLOWING)).pop(); return t && triggersInBar.includes(t); })
        .map((c) => setupMenu('menubar', c, { side: 'bottom', align: 'start' })).filter(Boolean);
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
      // Panels that end up scrollable must be reachable from the keyboard.
      const keyboardReach = () => FB.qsa(group, '[data-slot="resizable-panel"], [data-slot="resizable-panel"] > div').forEach((p) => {
        const cs = getComputedStyle(p);
        const scrolls = cs.overflowY === 'auto' || cs.overflowY === 'scroll' || cs.overflowX === 'auto' || cs.overflowX === 'scroll';
        if (scrolls && !p.hasAttribute('tabindex')) p.setAttribute('tabindex', '0');
      });
      keyboardReach();
      new ResizeObserver(keyboardReach).observe(group);
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
/* Popover, Hover Card and Tooltip: non-modal floating layers anchored to the trigger that precedes them.
   Popover opens on click (dismiss on outside/Escape, focus moves into the content).
   Hover Card opens on pointer hover / focus with open and close delays.
   Tooltip opens on hover / focus with a delay, closes on pointer leave, blur or Escape. */
(function (FB) {
  'use strict';

  function setup(kind, content) {
    const trigger = FB.pairWith(content, `[data-slot="${kind}-trigger"], [data-slot="${kind}-anchor"]`);
    if (!trigger) return;
    const id = FB.ensureId(content, kind);
    content.setAttribute('data-floating', '');
    content.setAttribute('data-popper-var', kind);
    const side = content.getAttribute('data-side') || (kind === 'tooltip' ? 'top' : 'bottom');
    const align = content.getAttribute('data-align') || 'center';
    const sideOffset = Number(content.getAttribute('data-side-offset') || (kind === 'tooltip' ? 0 : 4));
    const alignOffset = Number(content.getAttribute('data-align-offset') || 0);
    if (kind === 'popover') trigger.setAttribute('aria-controls', id);
    if (kind === 'tooltip') trigger.setAttribute('aria-describedby', id);
    let layer = null, openTimer = 0, closeTimer = 0;

    function reposition() { FB.float(trigger, content, { side, align, sideOffset, alignOffset }); }
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
      if (kind === 'popover') { trigger.setAttribute('aria-expanded', 'false'); trigger.focus({ preventScroll: true }); }
      if (layer) { FB.removeLayer(layer); layer = null; }
      FB.emit(content, 'close', { kind });
    }
    if (kind === 'popover') {
      trigger.addEventListener('click', (e) => { e.preventDefault(); FB.isOpen(content) ? close() : open(); });
      content.addEventListener('click', (e) => { if (e.target.closest('[data-fb-close]')) close(); });
    } else {
      const openDelay = Number(content.getAttribute('data-open-delay') || trigger.getAttribute('data-open-delay') || (kind === 'tooltip' ? 0 : 700));
      const closeDelay = Number(content.getAttribute('data-close-delay') || trigger.getAttribute('data-close-delay') || (kind === 'tooltip' ? 0 : 300));
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
    content.fbOpen = open; content.fbClose = close; trigger.fbOpen = open; trigger.fbClose = close;
    if (content.getAttribute('data-state') === 'open') { FB.setState(content, 'closed'); open(); }
  }

  ['popover', 'hover-card', 'tooltip'].forEach((kind) => {
    FB.register(kind, { selector: `[data-slot="${kind}-content"]`, init: (el) => setup(kind, el) });
  });
})(window.FlaskBasecoat);


/* ---- select ---- */
/* Select: a button trigger (role=combobox) opening a listbox; keyboard navigation, type-ahead, Enter/Space selects,
   Escape closes. The selected item's label is copied into [data-slot="select-value"] and the value into a hidden
   input named by the wrapper's data-name (or `name`). Native Select needs no script. */
(function (FB) {
  'use strict';

  FB.register('select', {
    selector: '[data-slot="select-content"]',
    init(content) {
      const trigger = FB.pairWith(content, '[data-slot="select-trigger"]');
      if (!trigger) return;
      const wrapper = trigger; // data-name and data-value live on the trigger
      const valueEl = FB.qs(trigger, '[data-slot="select-value"]');
      const id = FB.ensureId(content, 'select');
      trigger.setAttribute('aria-controls', id);
      content.setAttribute('data-floating', '');
      content.setAttribute('data-popper-var', 'select');
      const name = trigger.getAttribute('data-name') || content.getAttribute('data-name') || trigger.getAttribute('name');
      let input = null;
      if (name) { input = document.createElement('input'); input.type = 'hidden'; input.name = name; trigger.insertAdjacentElement('afterend', input); }
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
        const value = item.getAttribute('data-value') || item.getAttribute('value') || item.textContent.trim();
        const label = (FB.qs(item, '[data-slot="select-item-text"]') || item).textContent.trim();
        if (valueEl) { valueEl.textContent = label; }
        trigger.removeAttribute('data-placeholder');
        if (input) input.value = value;
        wrapper.setAttribute('data-value', value);
        FB.emit(wrapper, 'change', { value, label });
        close();
      }
      const preselected = items().find((i) => i.getAttribute('data-state') === 'checked' || i.getAttribute('aria-selected') === 'true');
      if (preselected) { const label = preselected.textContent.trim(); if (valueEl && !valueEl.textContent.trim()) valueEl.textContent = label; if (input) input.value = preselected.getAttribute('data-value') || preselected.getAttribute('value') || label; trigger.removeAttribute('data-placeholder'); }
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
      content.fbOpen = open; content.fbClose = close; trigger.fbOpen = open; trigger.fbClose = close; trigger.fbSelect = select;
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

      // Accessible names: Radix leaves thumbs unnamed unless the author labels them; derive one from the
      // slider's own label (aria-label, aria-labelledby or a <label for>) so screen readers announce the control.
      const ownLabel = root.getAttribute('aria-label') || (root.getAttribute('aria-labelledby') && (document.getElementById(root.getAttribute('aria-labelledby')) || {}).textContent)
        || (root.id && (document.querySelector(`label[for="${root.id}"]`) || {}).textContent) || (root.closest('[data-slot="field"]') && (FB.qs(root.closest('[data-slot="field"]'), '[data-slot="field-label"]') || {}).textContent) || 'Value';
      thumbs.forEach((t, i) => {
        if (!t.hasAttribute('aria-label') && !t.hasAttribute('aria-labelledby')) {
          const base = String(ownLabel).trim();
          t.setAttribute('aria-label', thumbs.length > 1 ? `${base} ${i === 0 ? 'minimum' : i === thumbs.length - 1 ? 'maximum' : i + 1}` : base);
        }
      });
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

  // Any element with data-fb-toast shows a toast on click (title from the attribute, optional description/variant).
  document.addEventListener('click', (e) => {
    const t = e.target.closest && e.target.closest('[data-fb-toast]');
    if (!t) return;
    toast({ title: t.getAttribute('data-fb-toast'), description: t.getAttribute('data-fb-toast-description') || undefined, variant: t.getAttribute('data-fb-toast-variant') || 'default',
      action: t.getAttribute('data-fb-toast-action') ? { label: t.getAttribute('data-fb-toast-action') } : undefined });
  });

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
