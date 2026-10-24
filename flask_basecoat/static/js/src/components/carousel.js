/* Carousel: scroll-snap based slides with previous/next buttons, keyboard arrows and disabled state at the ends. */
(function (FB) {
  'use strict';

  FB.register('carousel', {
    init(root) {
      const content = FB.qs(root, '[data-slot="carousel-content"]');
      const track = content && (content.firstElementChild && content.firstElementChild.getAttribute('data-slot') !== 'carousel-item' ? content.firstElementChild : content);
      const items = () => FB.qsa(root, '[data-slot="carousel-item"]');
      const prev = FB.qs(root, '[data-slot="carousel-previous"]');
      const next = FB.qs(root, '[data-slot="carousel-next"]');
      if (!content || !items().length) return;
      const vertical = root.getAttribute('data-orientation') === 'vertical';
      const loop = root.hasAttribute('data-loop');
      let index = 0;
      const viewport = content;
      viewport.style.overflow = 'hidden';
      function go(i) {
        const n = items().length;
        if (loop) i = (i + n) % n; else i = Math.max(0, Math.min(n - 1, i));
        index = i;
        const el = items()[index];
        const offset = vertical ? el.offsetTop - track.offsetTop : el.offsetLeft - track.offsetLeft;
        track.style.transform = vertical ? `translate3d(0, -${offset}px, 0)` : `translate3d(-${offset}px, 0, 0)`;
        track.style.transition = 'transform 300ms ease';
        if (prev) prev.disabled = !loop && index === 0;
        if (next) next.disabled = !loop && index >= n - 1;
        items().forEach((it, k) => it.setAttribute('aria-hidden', String(k !== index)));
        FB.emit(root, 'change', { index });
      }
      if (prev) prev.addEventListener('click', (e) => { e.preventDefault(); go(index - 1); });
      if (next) next.addEventListener('click', (e) => { e.preventDefault(); go(index + 1); });
      root.addEventListener('keydown', (e) => {
        if (e.key === (vertical ? 'ArrowUp' : 'ArrowLeft')) { e.preventDefault(); go(index - 1); }
        if (e.key === (vertical ? 'ArrowDown' : 'ArrowRight')) { e.preventDefault(); go(index + 1); }
      });
      let startX = 0, startY = 0;
      viewport.addEventListener('pointerdown', (e) => { startX = e.clientX; startY = e.clientY; });
      viewport.addEventListener('pointerup', (e) => {
        const dx = e.clientX - startX, dy = e.clientY - startY;
        const d = vertical ? dy : dx;
        if (Math.abs(d) > 40) go(index + (d < 0 ? 1 : -1));
      });
      window.addEventListener('resize', () => go(index));
      go(0);
      root.fbGo = go;
    },
  });
})(window.FlaskBasecoat);
