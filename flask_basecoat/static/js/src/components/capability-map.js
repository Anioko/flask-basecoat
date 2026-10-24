/* Capability map family (templates/basecoat/capability_map): the map, the tree, applications by capability, the dialogs.
   - [data-capmap-view] / [data-capmap-filter] ToggleGroups switch panes and filter rows;
   - [data-capmap-metric] switches the heat metric: data-heat of every [data-h-maturity] element and the visible text;
   - [data-cap-toggle="<id>"] discloses [data-cap-children="<id>"]; [data-expand-all] and [data-collapse-all];
   - [data-cap-open="<id>"] fills the detail Sheet from the page data (<script data-capmap-data>);
   - [data-cap-action="add|child|edit|delete|meta|types"] opens the dialogs with their values, and the dialogs announce
     their result and emit basecoat:capability-save and basecoat:capability-delete (the page decides what to store). */
(function (FB) {
  'use strict';
  const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : '');
  const TYPES = { strategic: 'Strategic', operational: 'Operational', supporting: 'Supporting' };
  // The ramp: primary at 20, 40, 60, 80 and 100 percent (step 0 is a dashed outline). Literal class names, so Tailwind builds them.
  const RAMP = ['border-dashed', 'bg-primary/20', 'bg-primary/40', 'bg-primary/60', 'bg-primary/80', 'bg-primary'];
  const MATURITY = { 1: 'Initial', 2: 'Developing', 3: 'Defined', 4: 'Managed', 5: 'Optimized' };

  let data = null;
  function pageData() {
    if (data) return data;
    const el = document.querySelector('script[data-capmap-data]');
    const d = el ? JSON.parse(el.textContent) : { capabilities: [], applications: [] };
    data = { caps: {}, apps: d.applications };
    d.capabilities.forEach((c) => { data.caps[c.id] = c; });
    return data;
  }
  const live = (msg) => FB.qsa(document, '[data-capmap-live]').forEach((el) => { el.textContent = msg; });
  const descendants = (id) => Object.values(pageData().caps).filter((c) => c.parentId === id).flatMap((c) => [c.id, ...descendants(c.id)]);

  FB.register('capmap', {
    selector: '[data-capmap]',
    init(root) {
      let metric = 'maturity';
      const view = FB.qs(root, '[data-capmap-view]');
      if (view) view.addEventListener('basecoat:change', (e) => {
        const v = (e.detail.value || [])[0];
        if (!v) { view.fbSetValue(root.getAttribute('data-view') || FB.qs(view, '[data-slot="toggle-group-item"]').getAttribute('data-value')); return; }
        root.setAttribute('data-view', v);
        FB.qsa(root, '[data-capmap-pane]').forEach((p) => { p.hidden = p.getAttribute('data-capmap-pane') !== v; });
      });

      const filter = FB.qs(root, '[data-capmap-filter]');
      if (filter) filter.addEventListener('basecoat:change', (e) => {
        const v = (e.detail.value || [])[0];
        if (!v) { filter.fbSetValue('all'); return; }
        FB.qsa(root, '[data-covered]').forEach((r) => { r.hidden = v === 'gaps' && r.getAttribute('data-covered') === '1'; });
        const shown = FB.qsa(root, '[data-covered]').filter((r) => !r.hidden).length;
        live(v === 'gaps' ? shown + ' capabilities without an application.' : 'All capabilities shown.');
      });

      const apply = (m) => {
        metric = m;
        FB.qsa(root, '[data-ramp][data-h-maturity]').forEach((el) => { el.classList.remove(...RAMP); el.classList.add(RAMP[Number(el.getAttribute('data-h-' + m))]); });
        FB.qsa(root, '[data-metric-text]').forEach((el) => { el.hidden = el.getAttribute('data-metric-text') !== m; });
        FB.qsa(root, '[data-legend]').forEach((el) => { el.hidden = el.getAttribute('data-legend') !== m; });
      };
      const toggle = FB.qs(root, '[data-capmap-metric]');
      if (toggle) toggle.addEventListener('basecoat:change', (e) => {
        const v = (e.detail.value || [])[0];
        if (!v) { toggle.fbSetValue(metric); return; }
        apply(v);
        live('Heat by ' + v + '.');
      });

      const expanded = () => FB.qsa(root, '[data-cap-toggle]');
      const set = (b, on) => {
        b.setAttribute('aria-expanded', String(on));
        FB.qsa(root, '[data-cap-children="' + b.getAttribute('data-cap-toggle') + '"]').forEach((c) => { c.hidden = !on; });
      };
      expanded().forEach((b) => set(b, b.getAttribute('aria-expanded') === 'true'));
      root.addEventListener('click', (e) => {
        const t = e.target.closest('[data-cap-toggle]');
        if (t) { set(t, t.getAttribute('aria-expanded') !== 'true'); return; }
        if (e.target.closest('[data-expand-all]')) { expanded().forEach((b) => set(b, true)); live('All capabilities expanded.'); }
        if (e.target.closest('[data-collapse-all]')) { expanded().forEach((b) => set(b, false)); live('All capabilities collapsed.'); }
        const open = e.target.closest('[data-cap-open]');
        if (open) fillDetail(open.getAttribute('data-fb-open'), open.getAttribute('data-cap-open'));
      });
    },
  });

  function fillDetail(sheetId, id) {
    const sheet = document.getElementById(sheetId), c = pageData().caps[id];
    if (!sheet || !c) return;
    const m = c.metrics || {};
    const f = (k, v) => { const el = FB.qs(sheet, '[data-f="' + k + '"]'); if (el) el.textContent = v; };
    const apps = pageData().apps.filter((a) => (a.capabilities || []).includes(id)).map((a) => a.name);
    f('name', c.name); f('description', c.description || '');
    f('type', TYPES[String(c.capability_type || '').toLowerCase()] || 'Type not set');
    f('level', 'L' + c.level); f('owner', m.owner || 'No owner. Assign one');
    f('maturity', m.maturity + '/5, ' + (MATURITY[m.maturity] || '')); f('importance', cap(m.strategicImportance));
    f('investment', cap(m.currentInvestment) + ' now, ' + (m.plannedInvestment || '') + ' planned'); f('risk', cap(m.riskLevel || 'medium'));
    f('apps', apps.length ? apps.join(', ') : 'No application supports this capability. Add one.');
  }

  /* ---- dialogs (portaled to <body> when open, so listened to on the document) ---- */
  const dlg = (id) => document.getElementById(id);
  const setSelect = (form, name, value, locked) => {
    const t = FB.qs(form, '[data-field="' + name + '"]');
    if (!t) return;
    if (t.fbSetValue) t.fbSetValue(String(value == null ? '' : value));
    t.disabled = !!locked;
  };
  const getSelect = (form, name) => { const t = FB.qs(form, '[data-field="' + name + '"]'); return t ? (t.fbGetValue ? t.fbGetValue() : t.getAttribute('data-value')) || '' : ''; };
  function nameError(form, on) {
    const field = FB.qs(form, '[data-name-field]'); if (!field) return;
    field.setAttribute('data-invalid', String(on));
    form.elements.name.setAttribute('aria-invalid', String(on));
    FB.qs(field, '[data-slot="field-error"]').hidden = !on;
  }
  let current = null;

  document.addEventListener('click', (e) => {
    const a = e.target.closest('[data-cap-action]');
    if (a) {
      e.preventDefault();
      const act = a.getAttribute('data-cap-action'), id = a.getAttribute('data-cap-id'), c = id ? pageData().caps[id] : null;
      if (act === 'delete') {
        const content = dlg('cap-delete'); if (!content || !c) return;
        const n = descendants(id).length; current = { act, id };
        FB.qs(content, '[data-del-name]').textContent = '"' + c.name + '"';
        FB.qs(content, '[data-del-leaf]').hidden = n > 0;
        FB.qs(content, '[data-del-warning]').hidden = n === 0;
        FB.qs(content, '[data-del-count]').textContent = n;
        FB.qs(content, '[data-del-noun]').textContent = n === 1 ? 'sub-capability' : 'sub-capabilities';
        FB.qs(content, '[data-del-confirm]').textContent = n > 0 ? 'Delete (' + (n + 1) + ' total)' : 'Delete';
        content.fbOpen(a);
      } else if (act === 'meta' || act === 'types') {
        const content = dlg(act === 'meta' ? 'map-meta' : 'type-desc'); if (content) content.fbOpen(a);
      } else {
        const content = dlg('cap-form'); if (!content) return;
        const f = FB.qs(content, 'form'), parent = act === 'child' ? c : null, m = (act === 'edit' && c && c.metrics) || { maturity: 3, strategicImportance: 'medium', currentInvestment: 'medium', plannedInvestment: 'medium', riskLevel: 'medium' };
        const level = act === 'edit' ? c.level : parent ? parent.level + 1 : 0;
        current = { act, id };
        FB.qs(content, '[data-f-title]').textContent = act === 'edit' ? 'Edit capability' : parent ? 'Add sub-capability to "' + parent.name + '"' : 'Add capability';
        FB.qs(content, '[data-f-desc]').textContent = act === 'edit' ? 'Update the capability details.' : parent ? 'Create a level ' + level + ' capability under ' + parent.name + '. Its type and level follow the parent.' : 'Create a capability at the root level.';
        FB.qs(content, '[data-f-submit]').textContent = act === 'edit' ? 'Update capability' : 'Create capability';
        f.elements.name.value = act === 'edit' ? c.name : '';
        f.elements.description.value = act === 'edit' ? (c.description || '') : '';
        f.elements.owner.value = m.owner || '';
        setSelect(f, 'capability_type', act === 'edit' ? (c.capability_type || '') : parent ? (parent.capability_type || '') : (a.getAttribute('data-group') || 'operational'), !!parent);
        setSelect(f, 'level', level, !!parent);
        ['maturity', 'strategicImportance', 'currentInvestment', 'plannedInvestment', 'riskLevel'].forEach((k) => setSelect(f, k, m[k]));
        nameError(f, false);
        content.fbOpen(a);
      }
      return;
    }
    if (e.target.closest('[data-del-confirm]') && current && current.act === 'delete') {
      const gone = [current.id, ...descendants(current.id)];
      document.dispatchEvent(new CustomEvent('basecoat:capability-delete', { detail: { ids: gone } }));
      live('Deleted ' + pageData().caps[current.id].name + (gone.length > 1 ? ' and ' + (gone.length - 1) + ' sub-capabilities.' : '.'));
      current = null;
    }
  });

  document.addEventListener('input', (e) => { const f = e.target.closest && e.target.closest('form[data-cap-form]'); if (f && e.target === f.elements.name && f.elements.name.value.trim()) nameError(f, false); });
  document.addEventListener('submit', (e) => {
    const f = e.target.closest('form[data-cap-form], form[data-meta-form], form[data-type-form]');
    if (!f) return;
    e.preventDefault();
    const content = f.closest('[data-slot="dialog-content"]');
    if (f.hasAttribute('data-cap-form')) {
      if (!f.elements.name.value.trim()) { nameError(f, true); f.elements.name.focus(); return; }
      const values = { name: f.elements.name.value.trim(), description: f.elements.description.value.trim(), owner: f.elements.owner.value.trim(),
        capability_type: getSelect(f, 'capability_type') || null, level: Number(getSelect(f, 'level') || 0), maturity: Number(getSelect(f, 'maturity') || 3),
        strategicImportance: getSelect(f, 'strategicImportance'), currentInvestment: getSelect(f, 'currentInvestment'), plannedInvestment: getSelect(f, 'plannedInvestment'), riskLevel: getSelect(f, 'riskLevel') };
      document.dispatchEvent(new CustomEvent('basecoat:capability-save', { detail: { mode: current && current.act, id: current && current.id, values } }));
      live((current && current.act === 'edit' ? 'Updated "' : 'Created "') + values.name + '" (' + (TYPES[values.capability_type] || 'Type not set') + ', level ' + values.level + ').');
    } else if (f.hasAttribute('data-meta-form')) {
      document.dispatchEvent(new CustomEvent('basecoat:capability-save', { detail: { mode: 'meta', values: { name: f.elements.name.value.trim(), description: f.elements.description.value.trim() } } }));
      live('Saved the capability map details.');
    } else {
      const values = {}; ['strategic', 'operational', 'supporting'].forEach((k) => { values[k] = f.elements[k].value.trim(); });
      document.dispatchEvent(new CustomEvent('basecoat:capability-save', { detail: { mode: 'types', values } }));
      live('Saved the capability type descriptions.');
    }
    if (content && content.fbClose) content.fbClose();
  });
})(window.FlaskBasecoat);
