/* Strategy canvases (templates/basecoat/canvas). One [data-canvas] root per canvas:
   - the ToggleGroup [data-canvas-view] switches between the drawing and the list route (panes [data-canvas-pane]);
   - a button [data-canvas-edit="<box key>"] (or a note's own text, [data-canvas-edit-from-note]) fills the canvas's edit
     Sheet from the box's notes and opens it;
   - [data-canvas-save] writes the Textarea back: one note per line, as one note card per line (cloned from
     <template data-canvas-note-template>) into the drawing ([data-canvas-notes]), the entry count Badge and the empty state
     of the box, and into the list table ([data-canvas-rows]), and tells the polite live region. */
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

      const EMPTY_ROW = 'Empty. Add the first entry from the canvas view.';
      const textOf = (li) => (FB.qs(li, '[data-note-text]') || li).textContent.trim();
      const notesOf = (k) => FB.qsa(root, `[data-canvas-notes="${k}"] > li`).map(textOf);

      root.addEventListener('click', (e) => {
        const fromNote = e.target.closest('[data-canvas-edit-from-note]');
        const list = fromNote && fromNote.closest('[data-canvas-notes]');
        const edit = list || e.target.closest('[data-canvas-edit]');
        if (edit && sheet) {
          key = edit.getAttribute('data-canvas-notes') || edit.getAttribute('data-canvas-edit');
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
        const proto = FB.qs(root, 'template[data-canvas-note-template]');
        if (list && proto) {
          list.replaceChildren(...lines.map((text) => {
            const li = proto.content.firstElementChild.cloneNode(true);
            FB.qsa(li, '[data-note-text], [data-note-hover-title]').forEach((n) => { n.textContent = text; });
            FB.qs(li, '[data-note-field="element"]').textContent = list.getAttribute('data-element') || 'Note';
            FB.qs(li, '[data-note-field="box"]').textContent = title;
            return li;
          }));
          FB.initAll(list);   // pairs the new hover cards with their triggers
          const empty = FB.qs(root, `[data-canvas-empty="${key}"]`);
          if (empty) empty.hidden = lines.length > 0;
          const count = FB.qs(root, `[data-canvas-count="${key}"]`);
          if (count) count.textContent = String(lines.length);
        }
        const body = FB.qs(root, '[data-canvas-rows]');
        const rowProto = FB.qs(root, 'template[data-canvas-row]');
        if (body && rowProto) {   // rebuild the list route from the drawing, so both always hold the same notes
          const rows = [];
          FB.qsa(root, '[data-canvas-notes]').forEach((ul) => {
            const notes = Array.from(ul.children).map(textOf);
            (notes.length ? notes : [EMPTY_ROW]).forEach((text) => {
              const tr = rowProto.content.firstElementChild.cloneNode(true);
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
