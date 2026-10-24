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
    selector: '[data-fb="combobox"]',
    init(wrapper) {
      const content = FB.qs(wrapper, '[data-slot="combobox-content"]');
      const trigger = FB.qs(wrapper, '[data-slot="combobox-trigger"], [data-slot="input-group-button"][role="combobox"]');
      const input = FB.qs(wrapper, '[data-slot="combobox-input"], [data-slot="combobox-chip-input"], [data-slot="input-group-control"][role="combobox"]');
      const valueEl = FB.qs(wrapper, '[data-slot="combobox-value"]');
      const clear = FB.qs(wrapper, '[data-slot="combobox-clear"]');
      const chips = FB.qs(wrapper, '[data-slot="combobox-chips"]');
      const list = content && (FB.qs(content, '[data-slot="combobox-list"]') || content);
      if (!content || !list) return;
      const anchor = trigger || (input && (input.closest('[data-slot="input-group"]') || input)) || wrapper;
      const multiple = !!chips || wrapper.hasAttribute('data-multiple');
      const name = wrapper.getAttribute('data-name') || wrapper.getAttribute('name');
      content.setAttribute('data-floating', ''); content.setAttribute('data-popper-var', 'combobox');
      const id = FB.ensureId(content, 'combobox');
      [trigger, input].forEach((t) => t && t.setAttribute('aria-controls', id));
      const ctl = listController(list, { itemSel: '[data-slot="combobox-item"]', input, groupSel: '[data-slot="combobox-group"]', separatorSel: '[data-slot="combobox-separator"]', emptySel: '[data-slot="combobox-empty"]' });
      const placeholder = valueEl ? valueEl.textContent : '';
      let selected = multiple ? [] : null;
      let layer = null;
      const hidden = () => { let h = FB.qs(wrapper, 'input[type=hidden][data-fb-combobox]'); if (!h && name) { h = document.createElement('input'); h.type = 'hidden'; h.name = name; h.setAttribute('data-fb-combobox', ''); wrapper.appendChild(h); } return h; };

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
        wrapper.setAttribute('data-value', values.join(','));
        if (valueEl) { valueEl.textContent = multiple ? (values.length ? selected.map(labelOf).join(', ') : placeholder) : (selected ? labelOf(selected) : placeholder); }
        if (input && !multiple && selected) input.value = labelOf(selected);
        if (clear) clear.toggleAttribute('data-visible', values.length > 0);
        ctl.items().forEach((i) => { const on = multiple ? selected.includes(i) : i === selected; i.setAttribute('data-checked', String(on)); i.setAttribute('aria-selected', String(on || i === ctl.highlighted)); const ind = FB.qs(i, '[data-slot="combobox-item-indicator"]'); if (ind) ind.style.visibility = on ? '' : 'hidden'; });
        renderChips();
        FB.emit(wrapper, 'change', { value: multiple ? values : values[0] || null });
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
        input.addEventListener('focus', () => { if (!wrapper.hasAttribute('data-open-on-click-only')) open(); });
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
      wrapper.fbOpen = open; wrapper.fbClose = close;
    },
  });
})(window.FlaskBasecoat);
