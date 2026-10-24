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
          // The indicator mirrors the control's state so the closed-state CSS hides it while unchecked.
          const state = el.getAttribute('aria-checked');
          FB.setState(ind, state === 'mixed' ? 'indeterminate' : state === 'true' ? 'checked' : 'unchecked');
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
        // A click on the control itself bubbles to a wrapping label; it has already toggled, so the label ignores it.
        if (el.id) FB.qsa(document, `label[for="${el.id}"]`).forEach((label) => label.addEventListener('click', (e) => { if (el.contains(e.target)) return; e.preventDefault(); el.click(); el.focus(); }));
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
      items().forEach((r) => { if (r.id) FB.qsa(document, `label[for="${r.id}"]`).forEach((l) => l.addEventListener('click', (e) => { if (r.contains(e.target)) return; e.preventDefault(); select(r, true); })); });
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
        FB.emit(group, 'change', { value: values() });
      });
      const valueOf = (o) => o.getAttribute('data-value') || o.getAttribute('value');
      const values = () => items().filter((o) => o.getAttribute('data-state') === 'on').map(valueOf);
      // Programmatic value (a controlled ToggleGroup): group.fbSetValue('30d') or (['a', 'b']); '' or [] presses none.
      group.fbSetValue = (value) => {
        const want = (Array.isArray(value) ? value : [value]).filter((v) => v !== '' && v != null).map(String);
        items().forEach((o) => set(o, want.includes(valueOf(o))));
      };
      group.fbGetValue = () => (multiple ? values() : (values()[0] || ''));
      const nav = FB.roving(items, { orientation: group.getAttribute('data-orientation') === 'vertical' ? 'vertical' : 'horizontal', loop: true, typeahead: false });
      group.addEventListener('keydown', (e) => { if (!nav(e) && (e.key === ' ' || e.key === 'Enter')) { const it = e.target.closest('[data-slot="toggle-group-item"]'); if (it) { e.preventDefault(); it.click(); } } });
    },
  });
})(window.FlaskBasecoat);
