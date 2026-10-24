/* Slider: pointer and keyboard control of one or more thumbs; range and thumb positions are written as inline
   styles the way Radix does (left/right or bottom/top percentages), and the value is mirrored into hidden inputs. */
(function (FB) {
  'use strict';

  FB.register('slider', {
    init(root) {
      const track = FB.qs(root, '[data-slot="slider-track"]');
      const range = FB.qs(root, '[data-slot="slider-range"]');
      const thumbs = FB.qsa(root, '[data-slot="slider-thumb"]');
      if (!track || !thumbs.length) return;
      const vertical = root.getAttribute('data-orientation') === 'vertical';
      const min = Number(thumbs[0].getAttribute('aria-valuemin') || root.getAttribute('data-min') || 0);
      const max = Number(thumbs[0].getAttribute('aria-valuemax') || root.getAttribute('data-max') || 100);
      const step = Number(root.getAttribute('data-step') || 1);
      const disabled = root.getAttribute('aria-disabled') === 'true' || root.hasAttribute('data-disabled');
      const name = root.getAttribute('data-name') || root.getAttribute('name');
      const values = thumbs.map((t, i) => {
        const v = t.getAttribute('aria-valuenow') ?? (root.getAttribute('data-value') || '').split(',')[i];
        return v !== null && v !== undefined && v !== '' ? Number(v) : min;
      });
      const inputs = name ? thumbs.map(() => { const i = document.createElement('input'); i.type = 'hidden'; i.name = name; root.appendChild(i); return i; }) : [];

      // Accessible names: Radix leaves thumbs unnamed unless the author labels them; derive one from the
      // slider's own label (aria-label, aria-labelledby or a <label for>) so screen readers announce the control.
      const ownLabel = root.getAttribute('aria-label') || (root.getAttribute('aria-labelledby') && (document.getElementById(root.getAttribute('aria-labelledby')) || {}).textContent)
        || (root.id && (document.querySelector(`label[for="${root.id}"]`) || {}).textContent) || (root.closest('[data-slot="field"]') && (FB.qs(root.closest('[data-slot="field"]'), '[data-slot="field-label"]') || {}).textContent) || 'Value';
      thumbs.forEach((t, i) => {
        if (!t.hasAttribute('aria-label') && !t.hasAttribute('aria-labelledby')) {
          const base = String(ownLabel).trim();
          t.setAttribute('aria-label', thumbs.length > 1 ? `${base} ${i === 0 ? 'minimum' : i === thumbs.length - 1 ? 'maximum' : i + 1}` : base);
        }
      });
      function pct(v) { return ((v - min) / (max - min)) * 100; }
      function render() {
        thumbs.forEach((t, i) => {
          t.setAttribute('aria-valuenow', String(values[i]));
          t.setAttribute('aria-valuemin', String(min));
          t.setAttribute('aria-valuemax', String(max));
          t.style.display = '';
          const p = pct(values[i]);
          t.parentElement.style.position = 'absolute';
          if (vertical) { t.parentElement.style.bottom = `calc(${p}% - var(--thumb-size, 0px))`; t.parentElement.style.left = ''; }
          else { t.parentElement.style.left = `calc(${p}% + var(--thumb-offset, 0px))`; t.parentElement.style.bottom = ''; }
          t.parentElement.style.transform = vertical ? 'translateY(50%)' : 'translateX(-50%)';
          if (inputs[i]) inputs[i].value = String(values[i]);
        });
        if (range) {
          const lo = values.length > 1 ? Math.min(...values) : min;
          const hi = Math.max(...values);
          if (vertical) { range.style.bottom = `${pct(lo)}%`; range.style.top = `${100 - pct(hi)}%`; }
          else { range.style.left = `${pct(lo)}%`; range.style.right = `${100 - pct(hi)}%`; }
        }
        root.setAttribute('data-value', values.join(','));
      }
      // Radix wraps each thumb in a positioned span; create it when the server did not.
      thumbs.forEach((t) => {
        if (!t.parentElement.hasAttribute('data-fb-thumb')) {
          const wrap = document.createElement('span');
          wrap.setAttribute('data-fb-thumb', '');
          wrap.style.transform = 'var(--radix-slider-thumb-transform)';
          wrap.style.position = 'absolute';
          t.parentNode.insertBefore(wrap, t);
          wrap.appendChild(t);
        }
      });
      function snap(v) { const s = Math.round((v - min) / step) * step + min; return Math.min(max, Math.max(min, Number(s.toFixed(6)))); }
      function valueFromPointer(e) {
        const r = track.getBoundingClientRect();
        const ratio = vertical ? 1 - (e.clientY - r.top) / r.height : (e.clientX - r.left) / r.width;
        return snap(min + Math.min(1, Math.max(0, ratio)) * (max - min));
      }
      function setValue(i, v) {
        v = snap(v);
        if (values.length > 1) {
          if (i > 0) v = Math.max(v, values[i - 1]);
          if (i < values.length - 1) v = Math.min(v, values[i + 1]);
        }
        if (values[i] === v) return;
        values[i] = v; render();
        FB.emit(root, 'change', { value: values.slice() });
      }
      let active = -1;
      root.addEventListener('pointerdown', (e) => {
        if (disabled || e.button !== 0) return;
        e.preventDefault();
        const v = valueFromPointer(e);
        let best = 0; thumbs.forEach((t, i) => { if (Math.abs(values[i] - v) < Math.abs(values[best] - v)) best = i; });
        active = best; setValue(active, v); thumbs[active].focus();
        root.setPointerCapture && root.setPointerCapture(e.pointerId);
      });
      root.addEventListener('pointermove', (e) => { if (active >= 0) setValue(active, valueFromPointer(e)); });
      root.addEventListener('pointerup', () => { active = -1; });
      root.addEventListener('pointercancel', () => { active = -1; });
      thumbs.forEach((t, i) => t.addEventListener('keydown', (e) => {
        if (disabled) return;
        const big = (max - min) / 10;
        const map = { ArrowRight: step, ArrowUp: step, ArrowLeft: -step, ArrowDown: -step, PageUp: big, PageDown: -big };
        if (e.key in map) { e.preventDefault(); setValue(i, values[i] + map[e.key] * (e.shiftKey ? 10 : 1)); }
        else if (e.key === 'Home') { e.preventDefault(); setValue(i, min); }
        else if (e.key === 'End') { e.preventDefault(); setValue(i, max); }
      }));
      render();
    },
  });
})(window.FlaskBasecoat);
