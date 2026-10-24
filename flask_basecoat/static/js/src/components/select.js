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
      // Programmatic selection: trigger.fbSetValue('value') picks the item with that value (or label), like a click.
      function setValue(value) {
        const v = value == null ? '' : String(value);
        if (v === '') {
          // no value (Radix value ""): nothing checked, the placeholder is shown
          items().forEach((i) => { i.setAttribute('aria-selected', 'false'); FB.setState(i, 'unchecked'); });
          if (valueEl) valueEl.textContent = placeholder;
          trigger.setAttribute('data-placeholder', '');
          trigger.removeAttribute('data-value');
          if (input) input.value = '';
          return true;
        }
        const item = items().find((i) => (i.getAttribute('data-value') || i.getAttribute('value')) === v) || items().find((i) => i.textContent.trim() === v);
        if (item) select(item);
        return !!item;
      }
      trigger.fbSetValue = setValue; content.fbSetValue = setValue;
      trigger.fbGetValue = () => trigger.getAttribute('data-value');
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
