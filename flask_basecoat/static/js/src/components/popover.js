/* Popover, Hover Card and Tooltip: non-modal floating layers anchored to a trigger.
   Popover opens on click (dismiss on outside/Escape, focus moves into the content).
   Hover Card opens on pointer hover / focus with open and close delays.
   Tooltip opens on hover / focus with a delay, closes on pointer leave, blur or Escape. */
(function (FB) {
  'use strict';

  function setup(kind, wrapper) {
    const trigger = FB.qs(wrapper, `[data-slot="${kind}-trigger"]`) || FB.qs(wrapper, `[data-slot="${kind}-anchor"]`);
    const content = FB.qs(wrapper, `[data-slot="${kind}-content"]`);
    if (!trigger || !content) return;
    const id = FB.ensureId(content, kind);
    content.setAttribute('data-floating', '');
    content.setAttribute('data-popper-var', kind === 'popover' ? 'popover' : kind === 'hover-card' ? 'hover-card' : 'tooltip');
    const side = content.getAttribute('data-side') || wrapper.getAttribute('data-side') || (kind === 'tooltip' ? 'top' : 'bottom');
    const align = content.getAttribute('data-align') || wrapper.getAttribute('data-align') || 'center';
    const sideOffset = Number(content.getAttribute('data-side-offset') || (kind === 'tooltip' ? 0 : 4));
    const alignOffset = Number(content.getAttribute('data-align-offset') || 0);
    if (kind === 'popover') trigger.setAttribute('aria-controls', id);
    if (kind === 'tooltip') trigger.setAttribute('aria-describedby', id);
    let layer = null, openTimer = 0, closeTimer = 0;

    function reposition() { FB.float(trigger, content, { side, align, sideOffset, alignOffset }); }
    function open() {
      clearTimeout(closeTimer);
      if (FB.isOpen(content)) return;
      if (content.parentNode !== document.body) document.body.appendChild(content);
      FB.setState(content, 'open');
      FB.setState(trigger, kind === 'tooltip' ? 'delayed-open' : 'open');
      if (kind === 'popover') trigger.setAttribute('aria-expanded', 'true');
      reposition();
      layer = { content, trigger, modal: false, reposition, onDismiss: () => close() };
      FB.pushLayer(layer);
      if (kind === 'popover') FB.focusFirst(content);
      FB.emit(content, 'open', { kind });
    }
    function close() {
      clearTimeout(openTimer);
      if (!FB.isOpen(content)) return;
      FB.setState(content, 'closed');
      FB.setState(trigger, 'closed');
      if (kind === 'popover') { trigger.setAttribute('aria-expanded', 'false'); trigger.focus({ preventScroll: true }); }
      if (layer) { FB.removeLayer(layer); layer = null; }
      FB.emit(content, 'close', { kind });
    }
    if (kind === 'popover') {
      trigger.addEventListener('click', (e) => { e.preventDefault(); FB.isOpen(content) ? close() : open(); });
      content.addEventListener('click', (e) => { if (e.target.closest('[data-fb-close]')) close(); });
    } else {
      const openDelay = Number(wrapper.getAttribute('data-open-delay') || (kind === 'tooltip' ? 0 : 700));
      const closeDelay = Number(wrapper.getAttribute('data-close-delay') || (kind === 'tooltip' ? 0 : 300));
      const scheduleOpen = () => { clearTimeout(closeTimer); openTimer = setTimeout(open, openDelay); };
      const scheduleClose = () => { clearTimeout(openTimer); closeTimer = setTimeout(close, closeDelay); };
      trigger.addEventListener('pointerenter', scheduleOpen);
      trigger.addEventListener('pointerleave', scheduleClose);
      trigger.addEventListener('focus', open);
      trigger.addEventListener('blur', close);
      content.addEventListener('pointerenter', () => clearTimeout(closeTimer));
      content.addEventListener('pointerleave', scheduleClose);
      if (kind === 'tooltip') trigger.addEventListener('pointerdown', close);
    }
    wrapper.fbOpen = open; wrapper.fbClose = close;
    if (content.getAttribute('data-state') === 'open') { FB.setState(content, 'closed'); open(); }
  }

  ['popover', 'hover-card', 'tooltip'].forEach((kind) => {
    FB.register(kind, { selector: `[data-fb="${kind}"]`, init: (el) => setup(kind, el) });
  });
})(window.FlaskBasecoat);
