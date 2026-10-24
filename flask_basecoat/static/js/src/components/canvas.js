/* Strategy canvases (templates/basecoat/canvas). One [data-canvas] root per canvas:
   - the ToggleGroup [data-canvas-view] switches between the drawing and the list route (panes [data-canvas-pane]);
   - a button [data-canvas-edit="<box key>"] fills the canvas's edit Sheet from the box's notes and opens it;
   - [data-canvas-save] writes the Textarea back: one note per line, into the drawing ([data-canvas-notes]) and into the
     list table ([data-canvas-rows]), and tells the polite live region. */
(function (FB) {
  'use strict';

  FB.register('canvas', {
    selector: '[data-canvas]',
    init(root) {
      const sheet = FB.qs(root, '[data-canvas-sheet]');
      const input = FB.qs(root, '[data-canvas-notes-input]');
      const live = FB.qs(root, '[data-canvas-live]');
      const group = FB.qs(root, '[data-canvas-view]');
      let key = null, title = '';

      if (group) {
        group.addEventListener('basecoat:change', (e) => {
          const v = (e.detail.value || [])[0];
          if (!v) { group.fbSetValue(root.getAttribute('data-view') || 'canvas'); return; }   // one view is always on
          root.setAttribute('data-view', v);
          FB.qsa(root, '[data-canvas-pane]').forEach((p) => { p.hidden = p.getAttribute('data-canvas-pane') !== v; });
        });
      }

      const notesOf = (k) => FB.qsa(root, `[data-canvas-notes="${k}"] > li`).map((li) => li.textContent.trim());

      root.addEventListener('click', (e) => {
        const edit = e.target.closest('[data-canvas-edit]');
        if (edit && sheet) {
          key = edit.getAttribute('data-canvas-edit');
          title = edit.getAttribute('data-title') || key;
          FB.qs(sheet, '[data-canvas-sheet-title]').textContent = 'Edit ' + title;
          FB.qs(sheet, '[data-canvas-sheet-question]').textContent = (edit.getAttribute('data-question') || '') + ' One note per line.';
          input.value = notesOf(key).join('\n');
        }
      });
      // The sheet is moved to <body> when it opens, so it is listened to directly.
      if (sheet) sheet.addEventListener('click', (e) => { if (e.target.closest('[data-canvas-save]') && key) save(); });

      function save() {
        const lines = input.value.split('\n').map((l) => l.trim()).filter(Boolean);
        const list = FB.qs(root, `[data-canvas-notes="${key}"]`);
        if (list) {
          list.replaceChildren(...lines.map((text) => {
            const li = document.createElement('li');
            li.className = 'rounded-md border bg-muted px-2 py-1.5 text-sm';
            li.textContent = text;
            return li;
          }));
        }
        const body = FB.qs(root, '[data-canvas-rows]');
        const proto = FB.qs(root, 'template[data-canvas-row]');
        if (body && proto) {   // rebuild the list route from the drawing, so both always hold the same notes
          const rows = [];
          FB.qsa(root, '[data-canvas-notes]').forEach((ul) => {
            const notes = Array.from(ul.children).map((li) => li.textContent.trim());
            (notes.length ? notes : ['No notes yet']).forEach((text) => {
              const tr = proto.content.firstElementChild.cloneNode(true);
              tr.setAttribute('data-box', ul.getAttribute('data-notes-key') || ul.getAttribute('data-canvas-notes'));
              tr.querySelector('th').textContent = ul.getAttribute('data-title');
              tr.querySelector('td').textContent = text;
              rows.push(tr);
            });
          });
          body.replaceChildren(...rows);
        }
        if (live) live.textContent = 'Saved ' + lines.length + (lines.length === 1 ? ' note' : ' notes') + ' for ' + title + '.';
      }
    },
  });
})(window.FlaskBasecoat);
