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
