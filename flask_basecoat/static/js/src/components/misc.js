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
      // A vertical group stacks panels (flex-direction: column); upstream may say so only through its inline style.
      const vertical = group.getAttribute('data-orientation') === 'vertical' || group.getAttribute('aria-orientation') === 'vertical' || group.style.flexDirection === 'column';
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
        // The separator runs across the group: a row of panels has vertical handles (react-resizable-panels semantics).
        handle.setAttribute('aria-orientation', vertical ? 'horizontal' : 'vertical');
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
