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
