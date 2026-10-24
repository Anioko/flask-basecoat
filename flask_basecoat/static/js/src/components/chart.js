/* Chart: an SVG renderer for the shadcn chart container.
   Upstream draws with Recharts; the style pack styles Recharts' class names (recharts-cartesian-grid lines,
   recharts-cartesian-axis-tick text, recharts-sector ...) and colours come from --color-<series> variables that
   the ChartContainer declares. This module reproduces that contract without React:
     <div data-slot="chart" data-chart="c1" data-chart-type="bar|stacked-bar|line|area|pie|donut|radial"
          data-chart-x="month" data-chart-data='[{"month":"Jan","desktop":186,"mobile":80}]'
          data-chart-series='[{"key":"desktop","label":"Desktop"},{"key":"mobile","label":"Mobile"}]'
          data-chart-legend data-chart-grid>
   Series colours default to --color-<key> (declared by the page) and then to --chart-1..5.
   Hover shows the ChartTooltipContent markup; a legend renders ChartLegendContent. */
(function (FB) {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';
  function el(tag, attrs, parent) {
    const n = document.createElementNS(NS, tag);
    Object.entries(attrs || {}).forEach(([k, v]) => n.setAttribute(k, String(v)));
    if (parent) parent.appendChild(n);
    return n;
  }
  function parse(root, name, fallback) {
    try { const v = root.getAttribute(name); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; }
  }
  function nice(max) {
    if (max <= 0) return 1;
    const p = Math.pow(10, Math.floor(Math.log10(max)));
    const n = max / p;
    const step = n <= 1 ? 0.25 : n <= 2 ? 0.5 : n <= 5 ? 1 : 2;
    return Math.ceil(n / step) * step * p;
  }
  function fmt(v) { return Number(v).toLocaleString(); }

  FB.register('chart', {
    init(root) {
      const data = parse(root, 'data-chart-data', null);
      if (!data || !Array.isArray(data) || !data.length) return; // static or externally rendered chart
      const type = root.getAttribute('data-chart-type') || 'bar';
      const xKey = root.getAttribute('data-chart-x') || Object.keys(data[0])[0];
      const series = parse(root, 'data-chart-series', Object.keys(data[0]).filter((k) => k !== xKey).map((k) => ({ key: k, label: k })));
      series.forEach((s, i) => { s.color = s.color || `var(--color-${s.key}, var(--chart-${(i % 5) + 1}))`; });
      const showGrid = root.hasAttribute('data-chart-grid') || !root.hasAttribute('data-chart-no-grid');
      const stacked = type === 'stacked-bar' || type === 'stacked-area';
      root.innerHTML = '';
      const container = document.createElement('div');
      container.className = 'recharts-responsive-container';
      container.style.cssText = 'width:100%;height:100%;min-width:0';
      const wrapper = document.createElement('div');
      wrapper.className = 'recharts-wrapper';
      wrapper.style.cssText = 'position:relative;cursor:default;width:100%;height:100%';
      container.appendChild(wrapper);
      root.appendChild(container);

      function draw() {
        wrapper.querySelectorAll('svg, .recharts-tooltip-wrapper, .recharts-legend-wrapper').forEach((n) => n.remove());
        const W = Math.max(200, root.clientWidth), H = Math.max(120, root.clientHeight);
        const svg = el('svg', { class: 'recharts-surface', width: W, height: H, viewBox: `0 0 ${W} ${H}` }, wrapper);
        const legendH = root.hasAttribute('data-chart-legend') ? 28 : 0;
        if (type === 'pie' || type === 'donut' || type === 'radial') return drawPie(svg, W, H - legendH);
        const m = { top: 12, right: 12, bottom: 28 + legendH, left: root.hasAttribute('data-chart-y-axis') ? 40 : 12 };
        const iw = W - m.left - m.right, ih = H - m.top - m.bottom;
        const totals = data.map((d) => stacked ? series.reduce((a, s) => a + (+d[s.key] || 0), 0) : Math.max(...series.map((s) => +d[s.key] || 0)));
        const maxV = nice(Math.max(...totals));
        const y = (v) => m.top + ih - (v / maxV) * ih;
        const n = data.length;
        const band = iw / n;
        // grid
        if (showGrid) {
          const grid = el('g', { class: 'recharts-cartesian-grid' }, svg);
          const gh = el('g', { class: 'recharts-cartesian-grid-horizontal' }, grid);
          for (let i = 0; i <= 4; i++) { const yy = m.top + (ih / 4) * i; el('line', { stroke: '#ccc', fill: 'none', x1: m.left, x2: m.left + iw, y1: yy, y2: yy }, gh); }
        }
        // x axis
        const axis = el('g', { class: 'recharts-cartesian-axis recharts-xAxis xAxis' }, svg);
        data.forEach((d, i) => {
          const tick = el('g', { class: 'recharts-cartesian-axis-tick' }, axis);
          const t = el('text', { x: m.left + band * i + band / 2, y: m.top + ih + 18, 'text-anchor': 'middle', class: 'recharts-text recharts-cartesian-axis-tick-value', fill: '#666' }, tick);
          const label = String(d[xKey] ?? '');
          el('tspan', {}, t).textContent = root.hasAttribute('data-chart-x-short') ? label.slice(0, 3) : label;
        });
        if (root.hasAttribute('data-chart-y-axis')) {
          const yaxis = el('g', { class: 'recharts-cartesian-axis recharts-yAxis yAxis' }, svg);
          for (let i = 0; i <= 4; i++) { const v = (maxV / 4) * i; const tick = el('g', { class: 'recharts-cartesian-axis-tick' }, yaxis); const t = el('text', { x: m.left - 8, y: y(v) + 4, 'text-anchor': 'end', class: 'recharts-text recharts-cartesian-axis-tick-value', fill: '#666' }, tick); el('tspan', {}, t).textContent = fmt(v); }
        }
        const hit = [];
        if (type === 'bar' || type === 'stacked-bar') {
          const gap = band * 0.2;
          const bw = stacked ? band - gap : (band - gap) / series.length;
          series.forEach((s, si) => {
            const layer = el('g', { class: 'recharts-layer recharts-bar' }, svg);
            data.forEach((d, i) => {
              const v = +d[s.key] || 0;
              const base = stacked ? series.slice(0, si).reduce((a, p) => a + (+d[p.key] || 0), 0) : 0;
              const x = m.left + band * i + gap / 2 + (stacked ? 0 : bw * si);
              const top = y(base + v), bottom = y(base);
              const r = Math.min(4, bw / 2);
              const path = stacked && si !== series.length - 1 ? `M${x},${bottom}h${bw}v${top - bottom}h${-bw}z` : `M${x},${bottom}v${-(bottom - top) + r}a${r},${r} 0 0 1 ${r},${-r}h${bw - 2 * r}a${r},${r} 0 0 1 ${r},${r}v${bottom - top - r}z`;
              el('path', { class: 'recharts-rectangle recharts-bar-rectangle', fill: s.color, d: path }, layer);
            });
          });
        } else {
          const points = (s) => data.map((d, i) => [m.left + band * i + band / 2, y(+d[s.key] || 0)]);
          series.forEach((s) => {
            const pts = points(s);
            const dLine = pts.map((p, i) => (i ? 'L' : 'M') + p[0] + ',' + p[1]).join('');
            if (type === 'area' || type === 'stacked-area') {
              el('path', { class: 'recharts-curve recharts-area-area', fill: s.color, 'fill-opacity': 0.4, stroke: 'none', d: dLine + `L${pts[pts.length - 1][0]},${y(0)}L${pts[0][0]},${y(0)}z` }, el('g', { class: 'recharts-layer recharts-area' }, svg));
            }
            el('path', { class: 'recharts-curve recharts-line-curve', fill: 'none', stroke: s.color, 'stroke-width': 2, d: dLine }, el('g', { class: 'recharts-layer recharts-line' }, svg));
            if (root.hasAttribute('data-chart-dots')) pts.forEach((p) => el('circle', { class: 'recharts-dot recharts-line-dot', r: 4, cx: p[0], cy: p[1], fill: s.color, stroke: '#fff', 'stroke-width': 2 }, svg));
          });
        }
        // hover regions and tooltip
        const cursor = el('path', { class: type.includes('bar') ? 'recharts-rectangle recharts-tooltip-cursor' : 'recharts-curve recharts-tooltip-cursor', fill: type.includes('bar') ? '#ccc' : 'none', stroke: '#ccc', 'fill-opacity': 0.3, style: 'display:none;pointer-events:none' }, svg);
        const tip = document.createElement('div');
        tip.className = 'recharts-tooltip-wrapper';
        tip.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;visibility:hidden;z-index:1';
        tip.innerHTML = '<div data-slot="chart-tooltip" class="cn-chart-tooltip grid min-w-32 items-start"><div class="cn-chart-tooltip-label font-medium"></div><div class="grid gap-1.5"></div></div>';
        wrapper.appendChild(tip);
        data.forEach((d, i) => {
          const zone = el('rect', { x: m.left + band * i, y: m.top, width: band, height: ih, fill: 'transparent' }, svg);
          zone.addEventListener('pointerenter', () => {
            cursor.setAttribute('d', type.includes('bar') ? `M${m.left + band * i},${m.top}h${band}v${ih}h${-band}z` : `M${m.left + band * i + band / 2},${m.top}v${ih}`);
            cursor.style.display = '';
            tip.querySelector('.cn-chart-tooltip-label').textContent = String(d[xKey] ?? '');
            tip.querySelector('.grid.gap-1\\.5').innerHTML = series.map((s) => `<div class="flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 [&>svg]:text-muted-foreground items-center"><div class="shrink-0 rounded-[2px] border-(--color-border) bg-(--color-bg) h-2.5 w-2.5" style="--color-bg:${s.color};--color-border:${s.color}"></div><div class="flex flex-1 justify-between leading-none items-center"><div class="grid gap-1.5"><span class="text-muted-foreground">${s.label}</span></div><span class="font-mono font-medium text-foreground tabular-nums">${fmt(d[s.key] || 0)}</span></div></div>`).join('');
            tip.style.visibility = 'visible';
            const x = m.left + band * i + band / 2;
            tip.style.transform = `translate(${Math.min(W - tip.offsetWidth - 4, Math.max(0, x + 12))}px, ${m.top}px)`;
          });
          zone.addEventListener('pointerleave', () => { cursor.style.display = 'none'; tip.style.visibility = 'hidden'; });
          hit.push(zone);
        });
        if (legendH) drawLegend(W, H);
      }
      function drawPie(svg, W, H) {
        const cx = W / 2, cy = H / 2, R = Math.min(W, H) / 2 - 8;
        const inner = type === 'donut' ? R * 0.6 : 0;
        const key = series[0].key;
        const total = data.reduce((a, d) => a + (+d[key] || 0), 0) || 1;
        let a0 = -Math.PI / 2;
        const g = el('g', { class: 'recharts-layer recharts-pie' }, svg);
        data.forEach((d, i) => {
          const v = +d[key] || 0, a1 = a0 + (v / total) * Math.PI * 2;
          const color = d.fill || `var(--color-${String(d[xKey]).toLowerCase().replace(/\s+/g, '-')}, var(--chart-${(i % 5) + 1}))`;
          const p = (r, a) => [cx + r * Math.cos(a), cy + r * Math.sin(a)];
          const [x0, y0] = p(R, a0), [x1, y1] = p(R, a1), [ix0, iy0] = p(inner, a0), [ix1, iy1] = p(inner, a1);
          const large = a1 - a0 > Math.PI ? 1 : 0;
          const dPath = inner ? `M${x0},${y0}A${R},${R} 0 ${large} 1 ${x1},${y1}L${ix1},${iy1}A${inner},${inner} 0 ${large} 0 ${ix0},${iy0}z` : `M${cx},${cy}L${x0},${y0}A${R},${R} 0 ${large} 1 ${x1},${y1}z`;
          const sector = el('path', { class: 'recharts-sector', fill: color, stroke: '#fff', d: dPath }, g);
          sector.setAttribute('role', 'img');
          sector.setAttribute('aria-label', `${d[xKey]}: ${fmt(v)}`);
          a0 = a1;
        });
        if (root.hasAttribute('data-chart-legend')) drawLegend(W, H + 28);
      }
      function drawLegend(W, H) {
        const legend = document.createElement('div');
        legend.className = 'recharts-legend-wrapper';
        legend.style.cssText = `position:absolute;width:${W}px;left:0;bottom:0`;
        const items = type === 'pie' || type === 'donut' ? data.map((d, i) => ({ label: d[xKey], color: d.fill || `var(--color-${String(d[xKey]).toLowerCase().replace(/\s+/g, '-')}, var(--chart-${(i % 5) + 1}))` })) : series.map((s) => ({ label: s.label, color: s.color }));
        legend.innerHTML = `<div data-slot="chart-legend" class="flex items-center justify-center gap-4 pt-3">${items.map((it) => `<div class="[&>svg]:text-muted-foreground flex items-center gap-1.5 [&>svg]:h-3 [&>svg]:w-3"><div class="h-2 w-2 shrink-0 rounded-[2px]" style="background-color:${it.color}"></div>${it.label}</div>`).join('')}</div>`;
        wrapper.appendChild(legend);
      }
      draw();
      new ResizeObserver(() => draw()).observe(root);
      root.fbRedraw = draw;
    },
  });
})(window.FlaskBasecoat);
