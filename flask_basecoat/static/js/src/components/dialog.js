/* Dialog, Alert Dialog, Sheet and Drawer: modal layers.
   Markup (server-rendered): a display:contents wrapper [data-fb="dialog"] holding the trigger, overlay and content.
   Behaviour mirrors Radix Dialog: aria-expanded/data-state on the trigger, scroll lock, focus trap, focus restore,
   Escape and overlay click dismiss (alert-dialog ignores overlay click), exit animation before hiding. */
(function (FB) {
  'use strict';

  function setup(kind, wrapper) {
    const trigger = FB.qs(wrapper, `[data-slot="${kind}-trigger"]`);
    const overlay = FB.qs(wrapper, `[data-slot="${kind}-overlay"]`);
    const content = FB.qs(wrapper, `[data-slot="${kind}-content"]`);
    if (!content) return;
    const id = FB.ensureId(content, kind);
    if (trigger) trigger.setAttribute('aria-controls', id);
    const title = FB.qs(content, `[data-slot="${kind}-title"]`);
    const desc = FB.qs(content, `[data-slot="${kind}-description"]`);
    if (title) content.setAttribute('aria-labelledby', FB.ensureId(title, `${kind}-title`));
    if (desc) content.setAttribute('aria-describedby', FB.ensureId(desc, `${kind}-description`));
    let layer = null, untrap = null, previouslyFocused = null, closing = null;

    function finishHide() {
      [overlay, content].forEach((el) => el && el.removeAttribute('data-fb-animating'));
      closing = null;
    }
    function open() {
      if (FB.isOpen(content)) return;
      if (closing) { clearTimeout(closing); finishHide(); }
      previouslyFocused = document.activeElement;
      // Portal to <body> so stacking is independent of the trigger's ancestors.
      if (overlay && overlay.parentNode !== document.body) document.body.appendChild(overlay);
      if (content.parentNode !== document.body) document.body.appendChild(content);
      [overlay, content].forEach((el) => el && FB.setState(el, 'open'));
      if (trigger) { FB.setState(trigger, 'open'); trigger.setAttribute('aria-expanded', 'true'); }
      FB.lockScroll();
      untrap = FB.trapFocus(content);
      FB.focusFirst(content, '[data-autofocus], [autofocus]');
      layer = {
        content, trigger, modal: true,
        onDismiss(reason, e) {
          if (reason === 'outside' && (kind === 'alert-dialog' || (e && content.contains(e.target)))) return;
          if (reason === 'outside' && e && overlay && !overlay.contains(e.target) && e.target !== overlay) {
            // clicks on other fixed layers (toasts) do not dismiss
            if (!e.target.closest || !e.target.closest('body')) return;
          }
          close();
        },
      };
      FB.pushLayer(layer);
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
      if (previouslyFocused && previouslyFocused.focus) previouslyFocused.focus({ preventScroll: true });
      FB.emit(content, 'close', { kind });
    }
    if (trigger) trigger.addEventListener('click', (e) => { e.preventDefault(); open(); });
    content.addEventListener('click', (e) => {
      const btn = e.target.closest(`[data-slot="${kind}-close"], [data-slot="${kind}-cancel"], [data-slot="${kind}-action"], [data-fb-close]`);
      if (btn && content.contains(btn)) { e.preventDefault(); close(); }
    });
    if (overlay) overlay.addEventListener('click', (e) => { if (e.target === overlay && kind !== 'alert-dialog') close(); });
    wrapper.fbOpen = open; wrapper.fbClose = close;
    if (content.getAttribute('data-state') === 'open') { FB.setState(content, 'closed'); open(); }
    // Any element elsewhere may open this dialog through data-fb-open="<id>"
    document.addEventListener('click', (e) => {
      const opener = e.target.closest && e.target.closest(`[data-fb-open="${id}"]`);
      if (opener) { e.preventDefault(); open(); }
    });
  }

  ['dialog', 'alert-dialog', 'sheet', 'drawer'].forEach((kind) => {
    FB.register(kind, { selector: `[data-fb="${kind}"]`, init: (el) => setup(kind, el) });
  });
})(window.FlaskBasecoat);
