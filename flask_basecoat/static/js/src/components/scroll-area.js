/* Scroll area: what Radix ScrollArea does once mounted in the browser.
   The viewport scrolls with its native scrollbar hidden, and an overlay scrollbar (data-slot="scroll-area-scrollbar",
   upstream classes) with a thumb sized and moved from the viewport's scroll position is drawn instead.
   Like Radix's default type="hover", the scrollbar shows while the pointer is over the area or it is scrolling, and
   only when the content overflows. A horizontal bar is added when the root has data-scrollbar="horizontal" or "both",
   or the page already contains a horizontal scrollbar element. */
(function (FB) {
  'use strict';

  const BAR = 'cn-scroll-area-scrollbar flex touch-none p-px transition-colors select-none';
  const THUMB = 'cn-scroll-area-thumb relative flex-1 bg-border';
  const HIDE_DELAY = 600;

  function bar(root, orientation) {
    let el = FB.qs(root, `:scope > [data-slot="scroll-area-scrollbar"][data-orientation="${orientation}"]`);
    if (!el) {
      el = document.createElement('div');
      el.setAttribute('data-slot', 'scroll-area-scrollbar');
      el.setAttribute('data-orientation', orientation);
      el.className = BAR;
      root.appendChild(el);
    }
    let thumb = FB.qs(el, '[data-slot="scroll-area-thumb"]');
    if (!thumb) {
      thumb = document.createElement('div');
      thumb.setAttribute('data-slot', 'scroll-area-thumb');
      thumb.className = THUMB;
      el.appendChild(thumb);
    }
    el.style.position = 'absolute';
    if (orientation === 'vertical') Object.assign(el.style, { top: '0', right: '0', bottom: '0' });
    else Object.assign(el.style, { left: '0', right: '0', bottom: '0' });
    return { el, thumb, orientation };
  }

  FB.register('scroll-area', {
    init(root) {
      const viewport = FB.qs(root, ':scope > [data-slot="scroll-area-viewport"]');
      if (!viewport) return;
      const mode = root.getAttribute('data-scrollbar') || '';
      const wantsX = mode === 'horizontal' || mode === 'both' || !!FB.qs(root, ':scope > [data-slot="scroll-area-scrollbar"][data-orientation="horizontal"]');
      const wantsY = mode !== 'horizontal';
      if (getComputedStyle(root).position === 'static') root.style.position = 'relative';
      viewport.style.overflowY = wantsY ? 'scroll' : 'hidden';
      viewport.style.overflowX = wantsX ? 'scroll' : 'hidden';
      viewport.style.scrollbarWidth = 'none';
      viewport.setAttribute('data-radix-scroll-area-viewport', '');
      const bars = [];
      if (wantsY) bars.push(bar(root, 'vertical'));
      if (wantsX) bars.push(bar(root, 'horizontal'));

      let hover = false, timer = 0;
      function update() {
        bars.forEach(({ el, thumb, orientation }) => {
          const vertical = orientation === 'vertical';
          const size = vertical ? viewport.clientHeight : viewport.clientWidth;
          const content = vertical ? viewport.scrollHeight : viewport.scrollWidth;
          const overflow = content > size + 1;
          el.hidden = !overflow;
          // A scrollable region must be reachable from the keyboard (axe scrollable-region-focusable).
          if (overflow && !viewport.hasAttribute('tabindex')) viewport.setAttribute('tabindex', '0');
          if (!overflow) return;
          const track = vertical ? el.clientHeight : el.clientWidth;
          const len = Math.max(18, (size / content) * track);
          const pos = ((vertical ? viewport.scrollTop : viewport.scrollLeft) / (content - size)) * (track - len);
          if (vertical) { thumb.style.height = `${len}px`; thumb.style.flex = 'none'; thumb.style.transform = `translate3d(0, ${pos}px, 0)`; }
          else { thumb.style.width = `${len}px`; thumb.style.flex = 'none'; thumb.style.transform = `translate3d(${pos}px, 0, 0)`; }
        });
      }
      function show(on) { bars.forEach(({ el }) => el.setAttribute('data-state', on ? 'visible' : 'hidden')); }
      function settle() { clearTimeout(timer); timer = setTimeout(() => { if (!hover) show(false); }, HIDE_DELAY); }
      show(false);
      root.addEventListener('pointerenter', () => { hover = true; update(); show(true); });
      root.addEventListener('pointerleave', () => { hover = false; settle(); });
      viewport.addEventListener('scroll', () => { update(); show(true); settle(); }, { passive: true });

      // Dragging the thumb scrolls the viewport.
      bars.forEach(({ el, thumb, orientation }) => {
        const vertical = orientation === 'vertical';
        thumb.addEventListener('pointerdown', (e) => {
          e.preventDefault(); thumb.setPointerCapture(e.pointerId);
          const start = vertical ? e.clientY : e.clientX, from = vertical ? viewport.scrollTop : viewport.scrollLeft;
          const move = (ev) => {
            const size = vertical ? viewport.clientHeight : viewport.clientWidth;
            const content = vertical ? viewport.scrollHeight : viewport.scrollWidth;
            const track = vertical ? el.clientHeight : el.clientWidth;
            const ratio = (content - size) / Math.max(1, track - thumb.getBoundingClientRect()[vertical ? 'height' : 'width']);
            const delta = ((vertical ? ev.clientY : ev.clientX) - start) * ratio;
            if (vertical) viewport.scrollTop = from + delta; else viewport.scrollLeft = from + delta;
          };
          const up = () => { thumb.removeEventListener('pointermove', move); thumb.removeEventListener('pointerup', up); };
          thumb.addEventListener('pointermove', move); thumb.addEventListener('pointerup', up);
        });
      });

      new ResizeObserver(update).observe(viewport);
      if (viewport.firstElementChild) new ResizeObserver(update).observe(viewport.firstElementChild);
      update();
    },
  });
})(window.FlaskBasecoat);
