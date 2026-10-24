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
