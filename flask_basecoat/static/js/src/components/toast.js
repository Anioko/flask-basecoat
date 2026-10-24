/* Toasts (Sonner-style): FlaskBasecoat.toast({title, description, variant, action, duration}) stacks toasts in a
   viewport in the bottom-right corner; flashes rendered server-side as [data-fb-flash] are promoted on load.
   Each toast is a data-slot="toast" element styled by the upstream cn-toast recipe. */
(function (FB) {
  'use strict';

  let viewport = null;
  function getViewport() {
    if (viewport) return viewport;
    viewport = document.querySelector('[data-slot="toast-viewport"]');
    if (!viewport) {
      viewport = document.createElement('div');
      viewport.setAttribute('data-slot', 'toast-viewport');
      viewport.setAttribute('tabindex', '-1');
      viewport.className = 'pointer-events-none fixed inset-x-4 bottom-4 z-50 mx-auto w-auto max-w-sm outline-none sm:right-4 sm:left-auto sm:mx-0 sm:w-full';
      document.body.appendChild(viewport);
    }
    return viewport;
  }
  const ICONS = {
    success: 'circle-check', info: 'info', warning: 'triangle-alert', error: 'octagon-x', loading: 'loader-circle',
  };
  function toast(opts) {
    opts = typeof opts === 'string' ? { title: opts } : (opts || {});
    const vp = getViewport();
    const el = document.createElement('div');
    el.setAttribute('data-slot', 'toast');
    el.setAttribute('role', opts.variant === 'error' ? 'alert' : 'status');
    el.setAttribute('aria-live', 'polite');
    el.setAttribute('data-type', opts.variant || 'default');
    el.setAttribute('data-state', 'open');
    el.className = 'cn-toast group/toast pointer-events-auto relative mt-3 flex w-full items-center gap-3 border bg-popover p-4 text-popover-foreground shadow-lg outline-none select-none data-[type=error]:text-destructive';
    const icon = opts.icon || (window.FlaskBasecoatIcons && window.FlaskBasecoatIcons[ICONS[opts.variant]]) || '';
    el.innerHTML =
      (icon ? `<div data-slot="toast-icon" class="cn-toast-icon flex shrink-0 items-center justify-center [&_svg]:size-4">${icon}</div>` : '') +
      `<div data-slot="toast-content" class="cn-toast-content flex flex-1 flex-col gap-0.5 text-sm">` +
      (opts.title ? `<div data-slot="toast-title" class="cn-toast-title font-medium"></div>` : '') +
      (opts.description ? `<div data-slot="toast-description" class="cn-toast-description text-muted-foreground"></div>` : '') +
      `</div>` +
      (opts.action ? `<button type="button" data-slot="toast-action" class="cn-button group/button inline-flex shrink-0 items-center justify-center whitespace-nowrap transition-all outline-none select-none cn-button-variant-outline cn-button-size-xs"></button>` : '') +
      (opts.dismissible === false ? '' : `<button type="button" data-slot="toast-close" aria-label="Close" class="cn-button group/button inline-flex shrink-0 items-center justify-center whitespace-nowrap transition-all outline-none select-none cn-button-variant-ghost cn-button-size-icon-xs absolute top-2 right-2 opacity-0 group-hover/toast:opacity-100">${(window.FlaskBasecoatIcons && window.FlaskBasecoatIcons.x) || '×'}</button>`);
    if (opts.title) FB.qs(el, '[data-slot="toast-title"]').textContent = opts.title;
    if (opts.description) FB.qs(el, '[data-slot="toast-description"]').textContent = opts.description;
    const actionBtn = FB.qs(el, '[data-slot="toast-action"]');
    if (actionBtn) { actionBtn.textContent = opts.action.label; actionBtn.addEventListener('click', () => { opts.action.onClick && opts.action.onClick(); dismiss(); }); }
    const closeBtn = FB.qs(el, '[data-slot="toast-close"]');
    if (closeBtn) closeBtn.addEventListener('click', dismiss);
    vp.appendChild(el);
    let timer = opts.duration === Infinity ? 0 : setTimeout(dismiss, opts.duration || 4000);
    el.addEventListener('pointerenter', () => { clearTimeout(timer); });
    el.addEventListener('pointerleave', () => { if (opts.duration !== Infinity) timer = setTimeout(dismiss, 2000); });
    function dismiss() {
      clearTimeout(timer);
      el.setAttribute('data-state', 'closed');
      el.setAttribute('data-fb-animating', '');
      setTimeout(() => el.remove(), 220);
      FB.emit(vp, 'toast-dismiss', { id: el.id });
    }
    return { element: el, dismiss };
  }
  FB.toast = toast;
  ['success', 'info', 'warning', 'error', 'loading'].forEach((v) => { toast[v] = (title, opts) => toast(Object.assign({ title, variant: v }, opts || {})); });

  // Server-rendered flash messages: <template data-fb-flash data-variant="success">text</template>
  document.addEventListener('DOMContentLoaded', () => {
    FB.qsa(document, '[data-fb-flash]').forEach((t) => {
      toast({ title: t.getAttribute('data-title') || (t.content ? t.content.textContent.trim() : t.textContent.trim()), description: t.getAttribute('data-description') || undefined, variant: t.getAttribute('data-variant') || 'default' });
      t.remove();
    });
  });
})(window.FlaskBasecoat);
