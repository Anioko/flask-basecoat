(() => {
  // shadcn's SelectScrollUpButton/DownButton exist only while the list overflows: show each when there is more to scroll
  // in its direction, and scroll while the pointer rests on it.
  const setup = (root) => {
    const content = root.querySelector('[data-slot="select-content"]');
    const up = content && content.querySelector('[data-slot="select-scroll-up-button"]');
    const down = content && content.querySelector('[data-slot="select-scroll-down-button"]');
    if (!up || !down) return;

    const update = () => {
      up.hidden = content.scrollTop <= 0;
      down.hidden = content.scrollTop + content.clientHeight >= content.scrollHeight - 1;
    };

    let timer = null;
    const stop = () => { clearInterval(timer); timer = null; };
    const hold = (button, step) => {
      button.addEventListener('pointerenter', () => {
        stop();
        timer = setInterval(() => { content.scrollTop += step; update(); }, 16);
      });
      button.addEventListener('pointerleave', stop);
    };
    hold(up, -4);
    hold(down, 4);

    content.addEventListener('scroll', update, { passive: true });
    new MutationObserver(update).observe(content.parentElement, { attributes: true, attributeFilter: ['aria-hidden'] });
    update();
  };

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-slot="select"]').forEach(setup);
  });
})();
