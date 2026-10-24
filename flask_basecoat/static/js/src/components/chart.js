/* Chart: the runtime behind shadcn's ChartContainer.

   A [data-slot="chart"] element carries its spec in a child <script type="application/json" data-chart-spec>
   (written by the `chart` macro, see flask_basecoat/charts.py). The runtime measures the
   .recharts-responsive-container, draws the Recharts DOM into .recharts-wrapper (chart-surface.js and
   chart-polar.js do the layout), keeps it in sync with the container size, and shows the tooltip
   (ChartTooltipContent markup) on hover and the legend (ChartLegendContent markup).

   The older attribute API still works and is translated to a spec:
     <div data-slot="chart" data-chart-type="bar|stacked-bar|line|area|stacked-area|pie|donut|radial"
          data-chart-x="month" data-chart-data='[...]' data-chart-series='[{"key":"desktop","label":"Desktop"}]'
          data-chart-legend data-chart-grid data-chart-y-axis data-chart-x-short data-chart-dots>

   Interactive charts: an element with data-chart-control="<the chart's data-chart value>" and data-chart-state="<name>"
   sets that state value from its basecoat:change event (select, single toggle group) or from data-chart-value on
   click (buttons), then the chart redraws; the other controls bound to the same state show the new value.
   spec.onMedia sets state from a media query (upstream useIsMobile effects). */
(function (FB) {
  'use strict';
  const NS = (window.FlaskBasecoatChart = window.FlaskBasecoatChart || {});
  let UID = 0;
  let CLIP_UID = 0;

  function L() { return NS.internal; }

  /* ---------------------------------------------------------------- legacy attribute API */
  function parseAttr(root, name, fallback) {
    try { const v = root.getAttribute(name); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; }
  }
  function legacySpec(root) {
    const data = parseAttr(root, 'data-chart-data', null);
    if (!Array.isArray(data) || !data.length) return null;
    const type = root.getAttribute('data-chart-type') || 'bar';
    const xKey = root.getAttribute('data-chart-x') || Object.keys(data[0])[0];
    const series = parseAttr(root, 'data-chart-series', Object.keys(data[0]).filter((k) => k !== xKey && k !== 'fill').map((k) => ({ key: k, label: k })));
    const config = {};
    series.forEach((s, i) => { config[s.key] = { label: s.label || s.key, color: s.color || `var(--chart-${(i % 5) + 1})` }; });
    const stacked = type === 'stacked-bar' || type === 'stacked-area';
    const xAxis = { component: 'XAxis', dataKey: xKey, tickLine: false, axisLine: false, tickMargin: 10 };
    if (root.hasAttribute('data-chart-x-short')) xAxis.tickFormatter = { $fn: 'slice', start: 0, end: 3 };
    const axes = [xAxis];
    if (root.hasAttribute('data-chart-y-axis')) axes.push({ component: 'YAxis', tickLine: false, axisLine: false, tickMargin: 8 });
    const grid = root.hasAttribute('data-chart-no-grid') ? null : { component: 'CartesianGrid', vertical: false };
    const legend = root.hasAttribute('data-chart-legend') ? { content: 'ChartLegendContent' } : null;
    if (type === 'pie' || type === 'donut' || type === 'radial') {
      const key = series[0].key;
      const rows = data.map((d, i) => Object.assign({ fill: `var(--color-${String(d[xKey]).toLowerCase().replace(/\s+/g, '-')}, var(--chart-${(i % 5) + 1}))` }, d));
      data.forEach((d, i) => { config[String(d[xKey]).toLowerCase().replace(/\s+/g, '-')] = { label: String(d[xKey]), color: `var(--chart-${(i % 5) + 1})` }; });
      if (type === 'radial') {
        return { type: 'radial', component: 'RadialBarChart', config, data: rows, props: { innerRadius: 30, outerRadius: 110 }, series: [{ component: 'RadialBar', dataKey: key, background: true }], axes: [], grid: null, tooltip: { cursor: false, content: 'ChartTooltipContent', hideLabel: true, nameKey: xKey }, legend, labels: [] };
      }
      return { type: 'pie', component: 'PieChart', config, data: rows, props: {}, series: [Object.assign({ component: 'Pie', data: rows, dataKey: key, nameKey: xKey }, type === 'donut' ? { innerRadius: 60, strokeWidth: 5 } : {})], axes: [], grid: null, tooltip: { cursor: false, content: 'ChartTooltipContent', hideLabel: true }, legend: legend ? Object.assign({ nameKey: xKey }, legend) : null, labels: [] };
    }
    const comp = { bar: 'Bar', 'stacked-bar': 'Bar', line: 'Line', area: 'Area', 'stacked-area': 'Area' }[type] || 'Bar';
    const chartComp = { Bar: 'BarChart', Line: 'LineChart', Area: 'AreaChart' }[comp];
    const s = series.map((sr, i) => {
      const o = { component: comp, dataKey: sr.key };
      if (comp === 'Bar') { o.fill = `var(--color-${sr.key})`; o.radius = stacked ? (i === 0 ? [0, 0, 4, 4] : i === series.length - 1 ? [4, 4, 0, 0] : 0) : 4; }
      if (comp === 'Line') { o.type = 'natural'; o.stroke = `var(--color-${sr.key})`; o.strokeWidth = 2; o.dot = root.hasAttribute('data-chart-dots') ? { fill: `var(--color-${sr.key})` } : false; }
      if (comp === 'Area') { o.type = 'natural'; o.fill = `var(--color-${sr.key})`; o.fillOpacity = 0.4; o.stroke = `var(--color-${sr.key})`; }
      if (stacked) o.stackId = 'a';
      return o;
    });
    return { type: comp.toLowerCase(), component: chartComp, config, data, props: { accessibilityLayer: true, margin: comp === 'Bar' ? undefined : { left: 12, right: 12 } }, series: s, axes, grid, tooltip: { cursor: false, content: 'ChartTooltipContent', indicator: comp === 'Bar' ? 'dashed' : 'dot' }, legend, labels: [] };
  }

  /* Inject the --color-<key> style the ChartContainer would (only for the attribute API). */
  function ensureStyle(root, spec) {
    if (root.querySelector(':scope > style')) return;
    const id = root.getAttribute('data-chart') || `chart-${++UID}`;
    root.setAttribute('data-chart', id);
    const keys = Object.entries(spec.config).filter(([, c]) => c.theme || c.color);
    if (!keys.length) return;
    const style = document.createElement('style');
    style.textContent = ['', '.dark'].map((prefix) => `\n${prefix} [data-chart=${id}] {\n${keys.map(([k, c]) => `  --color-${k}: ${(c.theme && c.theme[prefix ? 'dark' : 'light']) || c.color};`).join('\n')}\n}\n`).join('\n');
    root.insertBefore(style, root.firstChild);
  }

  /* ---------------------------------------------------------------- tooltip and legend content (shadcn chart.tsx) */
  function payloadConfig(config, payload, key) {
    if (typeof payload !== 'object' || payload === null) return undefined;
    const pp = payload.payload && typeof payload.payload === 'object' ? payload.payload : undefined;
    let k = key;
    if (key in payload && typeof payload[key] === 'string') k = payload[key];
    else if (pp && key in pp && typeof pp[key] === 'string') k = pp[key];
    return k in config ? config[k] : config[key];
  }
  function htmlEl(tag, cls, style) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (style) Object.keys(style).forEach((k) => { if (k.startsWith('--')) n.style.setProperty(k, style[k]); else n.style[k] = style[k]; });
    return n;
  }
  function textOf(v) { return v == null ? '' : String(v); }

  function tooltipContent(chart, t, payload, label) {
    const config = chart.ctx.config;
    const indicator = t.indicator || 'dot';
    const hideLabel = !!t.hideLabel, hideIndicator = !!t.hideIndicator;
    const labelFormatter = chart.fn(t.labelFormatter);
    const formatter = chart.fn(t.formatter);
    const nameKey = t.nameKey, labelKey = t.labelKey;
    let tooltipLabel = null;
    if (!hideLabel && payload.length) {
      const item = payload[0];
      const key = `${labelKey != null ? labelKey : (item.dataKey != null ? item.dataKey : (item.name != null ? item.name : 'value'))}`;
      const itemConfig = payloadConfig(config, item, key);
      const value = !labelKey && typeof label === 'string' ? (config[label] && config[label].label != null ? config[label].label : label) : itemConfig && itemConfig.label;
      if (labelFormatter) { tooltipLabel = htmlEl('div', t.$labelClass || 'font-medium'); appendContent(tooltipLabel, labelFormatter(value, payload)); } else if (value) { tooltipLabel = htmlEl('div', t.$labelClass || 'font-medium'); tooltipLabel.textContent = value; }
    }
    const nestLabel = payload.length === 1 && indicator !== 'dot';
    const root = htmlEl('div', t.$class || 'cn-chart-tooltip grid min-w-32 items-start');
    if (!nestLabel && tooltipLabel) root.appendChild(tooltipLabel);
    const list = htmlEl('div', 'grid gap-1.5');
    payload.filter((item) => item.type !== 'none').forEach((item, index) => {
      const key = `${nameKey != null ? nameKey : (item.name != null ? item.name : (item.dataKey != null ? item.dataKey : 'value'))}`;
      const itemConfig = payloadConfig(config, item, key);
      const indicatorColor = t.color != null ? t.color : (item.payload && item.payload.fill != null ? item.payload.fill : item.color);
      const row = htmlEl('div', indicator === 'dot' ? 'flex w-full flex-wrap gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 [&>svg]:text-muted-foreground items-center' : 'flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 [&>svg]:text-muted-foreground');
      if (formatter && item.value !== undefined && item.name) {
        appendContent(row, formatter(item.value, item.name, item, index, item.payload));
      } else {
        if (itemConfig && itemConfig.icon) {
          row.insertAdjacentHTML('beforeend', chart.iconMarkup(itemConfig.icon));
        } else if (!hideIndicator) {
          const cls = ['shrink-0 rounded-[2px] border-(--color-border)'];
          if (indicator === 'dot') cls.push('bg-(--color-bg) h-2.5 w-2.5');
          else if (indicator === 'line') cls.push('bg-(--color-bg) w-1');
          else cls.push('w-0 border-[1.5px] border-dashed bg-transparent');
          if (nestLabel && indicator === 'dashed') cls.push('my-0.5');
          row.appendChild(htmlEl('div', cls.join(' '), { '--color-bg': indicatorColor, '--color-border': indicatorColor }));
        }
        const body = htmlEl('div', `flex flex-1 justify-between leading-none ${nestLabel ? 'items-end' : 'items-center'}`);
        const names = htmlEl('div', 'grid gap-1.5');
        if (nestLabel && tooltipLabel) names.appendChild(tooltipLabel);
        const nm = htmlEl('span', 'text-muted-foreground');
        nm.textContent = textOf(itemConfig && itemConfig.label != null ? itemConfig.label : item.name);
        names.appendChild(nm);
        body.appendChild(names);
        if (item.value != null) {
          const v = htmlEl('span', 'font-mono font-medium text-foreground tabular-nums');
          v.textContent = typeof item.value === 'number' ? item.value.toLocaleString() : String(item.value);
          body.appendChild(v);
        }
        row.appendChild(body);
      }
      list.appendChild(row);
    });
    root.appendChild(list);
    return root;
  }
  function appendContent(parent, content) {
    if (content == null || content === false) return;
    if (content instanceof Node) parent.appendChild(content);
    else parent.appendChild(document.createTextNode(String(content)));
  }

  function legendContent(chart, model) {
    const config = chart.ctx.config;
    const lg = model.props;
    const payload = model.payload;
    if (!payload || !payload.length) return null;
    const root = htmlEl('div', lg.$class || `flex items-center justify-center gap-4 ${lg.verticalAlign === 'top' ? 'pb-3' : 'pt-3'}`);
    payload.filter((item) => item.type !== 'none').forEach((item) => {
      const key = `${lg.nameKey != null ? lg.nameKey : (item.dataKey != null ? item.dataKey : 'value')}`;
      const itemConfig = payloadConfig(config, item, key);
      const row = htmlEl('div', 'flex items-center gap-1.5 [&>svg]:h-3 [&>svg]:w-3 [&>svg]:text-muted-foreground');
      if (itemConfig && itemConfig.icon && !lg.hideIcon) row.insertAdjacentHTML('beforeend', chart.iconMarkup(itemConfig.icon));
      else row.appendChild(htmlEl('div', 'h-2 w-2 shrink-0 rounded-[2px]', { backgroundColor: item.color }));
      if (itemConfig && itemConfig.label != null) row.appendChild(document.createTextNode(String(itemConfig.label)));
      root.appendChild(row);
    });
    return root;
  }

  /* derive / computed functions of interactive specs (see flask_basecoat/charts.py FORMATTERS) */
  const DERIVE = {
    sinceDays(o, rows, state) {
      const reference = new Date(o.reference);
      const days = (o.days && o.days[state[o.state]]) || o.default;
      const start = new Date(reference);
      start.setDate(start.getDate() - days);
      return rows.filter((r) => new Date(r[o.key]) >= start);
    },
    indexOf(o, rows, state) { return rows.findIndex((r) => r[o.key] === state[o.state]); },
  };
  NS.derive = DERIVE;

  /* ---------------------------------------------------------------- the chart */
  class Chart {
    constructor(root, spec) {
      this.root = root;
      this.spec = spec;
      this.uid = ++UID;
      this.clipId = `recharts${++CLIP_UID}-clip`;
      this.state = Object.assign({}, spec.state || {});
      this.active = null;
      this.ctx = this.makeContext();
      this.mount();
    }

    makeContext() {
      const I = L();
      const chart = this;
      const ctx = {
        config: this.spec.config || {},
        state: this.state,
        get data() { return chart.data(); },
        iconMarkup: (name, attrs) => chart.iconMarkup(name, attrs),
        shapes: { Rectangle: I.Rectangle, Sector: I.Sector, Curve: I.Curve, Dot: I.Dot, h: I.h },
      };
      return ctx;
    }

    /* Chart rows, after the interactive filter (if any). */
    data() {
      const spec = this.spec;
      let rows = spec.data || [];
      if (spec.derive && spec.derive.$fn) rows = DERIVE[spec.derive.$fn](spec.derive, rows, this.state);
      return rows;
    }

    /* State values computed from other state (computed: {name: {"$fn": ...}}). */
    applyComputed() {
      const comp = this.spec.computed || {};
      Object.keys(comp).forEach((k) => { this.state[k] = DERIVE[comp[k].$fn](comp[k], this.spec.data || [], this.state); });
    }

    fn(ref) { return NS.surface.fn(ref, this.ctx); }

    iconMarkup(name, attrs) {
      let markup = (this.spec.icons || {})[name] || '';
      if (attrs && markup) {
        const extra = Object.keys(attrs).filter((k) => attrs[k] != null).map((k) => ` ${k}="${String(attrs[k]).replace(/"/g, '&quot;')}"`).join('');
        markup = markup.replace(/<svg /, '<svg ').replace(/ fill="none"/, attrs.fill != null ? '' : ' fill="none"').replace(/ stroke="currentColor"/, attrs.stroke != null ? '' : ' stroke="currentColor"');
        markup = markup.replace(/ width="24" height="24"/, '').replace(/^<svg/, `<svg${extra}`);
      }
      return markup;
    }

    mount() {
      const root = this.root;
      let container = root.querySelector(':scope > .recharts-responsive-container');
      if (!container) {
        container = document.createElement('div');
        container.className = 'recharts-responsive-container';
        container.setAttribute('style', 'width: 100%; height: 100%; min-width: 0px;');
        const inner = document.createElement('div');
        inner.setAttribute('style', 'width: 0px; height: 0px; overflow: visible;');
        container.appendChild(inner);
        root.appendChild(container);
      }
      this.container = container;
      this.inner = container.firstElementChild;
      let wrapper = this.inner.querySelector(':scope > .recharts-wrapper');
      if (!wrapper) { wrapper = document.createElement('div'); wrapper.className = 'recharts-wrapper'; this.inner.appendChild(wrapper); }
      this.wrapper = wrapper;
      wrapper.innerHTML = '';
      this.tooltipEl = document.createElement('div');
      this.tooltipEl.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml');
      this.tooltipEl.setAttribute('tabindex', '-1');
      this.tooltipEl.className = 'recharts-tooltip-wrapper';
      this.tooltipEl.setAttribute('style', 'visibility: hidden; pointer-events: none; position: absolute; top: 0px; left: 0px;');
      if (this.spec.tooltip) wrapper.appendChild(this.tooltipEl);
      const t = this.spec.tooltip;
      if (t && t.defaultIndex != null) this.defaultIndex = Number(t.defaultIndex);
      wrapper.addEventListener('mousemove', (e) => this.onMove(e));
      wrapper.addEventListener('mouseleave', () => this.onLeave());
      // accessibility layer: focus shows the first category, arrows move, Enter toggles, blur hides
      this.kb = { active: false, index: null };
      wrapper.addEventListener('focusin', (e) => { if (e.target === this.svg) this.onFocus(); });
      wrapper.addEventListener('focusout', (e) => { if (e.target === this.svg) this.onBlur(); });
      wrapper.addEventListener('keydown', (e) => this.onKey(e));
      wrapper.addEventListener('touchmove', (e) => { if (e.touches[0]) this.onMove(e.touches[0], e); }, { passive: true });
      this.size = { width: 0, height: 0 };
      const measure = () => {
        const r = container.getBoundingClientRect();
        const w = Math.round(r.width), h = Math.round(r.height);
        if (w !== this.size.width || h !== this.size.height) { this.size = { width: w, height: h }; this.render(); }
      };
      this.measure = measure;
      if (typeof ResizeObserver !== 'undefined') { this.ro = new ResizeObserver(() => measure()); this.ro.observe(container); }
      measure();
    }

    setState(name, value) {
      this.state[name] = value;
      this.mouse = null;
      this.render();
    }

    /* Which interaction shows the tooltip: pointer, then keyboard, then the defaultIndex until the pointer was used. */
    resolveActive() {
      if (this.mouse) return this.mouse;
      if (this.kb && this.kb.active && this.kb.index != null) return this.activeForIndex(this.kb.index, null);
      if (this.defaultIndex != null && !this.pointerSeen) return this.activeForIndex(this.defaultIndex, null);
      return null;
    }

    accessibilityLayer() { return !(this.spec.props && this.spec.props.accessibilityLayer === false); }
    onFocus() {
      if (!this.accessibilityLayer() || !this.spec.tooltip || this.tooltipEventType() !== 'axis' || this.kb.active) return;
      if (this.kb.index == null) { this.kb = { active: true, index: 0 }; this.active = this.resolveActive(); this.draw(); }
    }
    onBlur() {
      if (!this.accessibilityLayer() || !this.kb.active) return;
      this.kb = { active: false, index: this.kb.index };
      this.active = this.resolveActive();
      this.draw();
    }
    onKey(e) {
      if (!this.accessibilityLayer() || !this.spec.tooltip || this.tooltipEventType() !== 'axis' || !this.model) return;
      const key = e.key;
      if (key !== 'ArrowRight' && key !== 'ArrowLeft' && key !== 'Enter') return;
      const current = this.kb.index == null ? -1 : Number(this.kb.index);
      if (!(current >= 0)) return;
      if (key === 'Enter') this.kb = { active: !this.kb.active, index: this.kb.index };
      else {
        const m = this.model;
        const reversed = m.kind === 'cartesian' && (m.layout === 'horizontal' ? m.xAxis.reversed : m.yAxis.reversed);
        const next = current + (key === 'ArrowRight' ? 1 : -1) * (reversed ? -1 : 1);
        if (!m.tooltipTicks || next >= m.tooltipTicks.length || next < 0) return;
        this.kb = { active: true, index: next };
      }
      this.active = this.resolveActive();
      this.draw();
    }

    /* ---- measurement helpers used by the layout ---- */
    axisFontSize() {
      if (this._font) return this._font;
      const I = L();
      const probe = document.createElementNS(I.SVG_NS, 'svg');
      probe.setAttribute('style', 'position:absolute;visibility:hidden;width:0;height:0');
      const t = document.createElementNS(I.SVG_NS, 'text');
      t.setAttribute('class', 'recharts-text recharts-cartesian-axis-tick-value');
      t.textContent = '0';
      const g = document.createElementNS(I.SVG_NS, 'g');
      g.setAttribute('class', 'recharts-cartesian-axis-tick');
      g.appendChild(t);
      probe.appendChild(g);
      this.wrapper.appendChild(probe);
      const cs = getComputedStyle(t);
      this._font = { fontSize: cs.fontSize, letterSpacing: cs.letterSpacing };
      probe.remove();
      return this._font;
    }
    pathLength(d) {
      if (!d) return 0;
      const I = L();
      const probe = document.createElementNS(I.SVG_NS, 'svg');
      probe.setAttribute('style', 'position:absolute;visibility:hidden;width:0;height:0');
      const p = document.createElementNS(I.SVG_NS, 'path');
      p.setAttribute('d', d);
      probe.appendChild(p);
      this.wrapper.appendChild(probe);
      let len = 0;
      try { len = p.getTotalLength(); } catch (e) { len = 0; }
      probe.remove();
      return len;
    }
    measureLegend(model) {
      let el = this.wrapper.querySelector(':scope > .recharts-legend-wrapper');
      if (!el) {
        el = document.createElement('div');
        el.className = 'recharts-legend-wrapper';
        if (this.tooltipEl.parentNode) this.tooltipEl.insertAdjacentElement('afterend', el); else this.wrapper.insertBefore(el, this.wrapper.firstChild);
      }
      el.setAttribute('style', Object.entries(model.style).map(([k, v]) => `${k.replace(/[A-Z]/g, (c) => '-' + c.toLowerCase())}: ${v};`).join(' '));
      el.innerHTML = '';
      const content = legendContent(this, model);
      if (content) el.appendChild(content);
      this.legendEl = el;
      const r = el.getBoundingClientRect();
      return { width: r.width, height: r.height };
    }

    /* ---- render ---- */
    render() {
      const I = L();
      this.applyComputed();
      const { width, height } = this.size;
      this.width = width; this.height = height;
      const w = this.wrapper;
      w.setAttribute('width', width);
      w.setAttribute('height', height);
      w.setAttribute('style', `position: relative; cursor: default; width: ${width}px; height: ${height}px;`);
      const old = w.querySelector(':scope > svg.recharts-surface');
      if (!(width > 0 && height > 0)) { if (old) old.remove(); return; }
      const polar = ['PieChart', 'RadarChart', 'RadialBarChart'].includes(this.spec.component);
      this.model = polar ? NS.polar.buildPolar(this) : NS.surface.buildCartesian(this);
      if (!this.spec.legend && this.legendEl) { this.legendEl.remove(); this.legendEl = null; }
      if (this.mouse && this.mouse.pointer) this.mouse = this.computeActive(this.mouse.pointer, this.mouse.itemTarget);
      this.active = this.resolveActive();
      this.draw();
    }

    draw() {
      const I = L();
      const m = this.model;
      const polar = m.kind === 'polar';
      const { layers, z0 } = polar ? NS.polar.renderPolar(this, m, this.active) : NS.surface.renderCartesian(this, m, this.active);
      const { h } = I;
      const svgAttrs = {};
      if (polar) { svgAttrs.cx = m.props.cx; svgAttrs.cy = m.props.cy; }
      const access = this.spec.props && this.spec.props.accessibilityLayer === false ? false : true;
      if (access) { svgAttrs.role = 'application'; svgAttrs.tabindex = 0; }
      Object.assign(svgAttrs, { class: 'recharts-surface', width: m.width, height: m.height, viewBox: `0 0 ${m.width} ${m.height}`, style: 'width: 100%; height: 100%; display: block;' });
      const off = m.offset;
      const kids = [h('title', {}, []), h('desc', {}, [])];
      const layer = (z) => h('g', { tabindex: -1, class: `recharts-zIndex-layer_${z}` }, layers[z]);
      kids.push(layer(-100), layer(-50));
      kids.push(h('defs', {}, [h('clipPath', { id: this.clipId }, [h('rect', { x: off.left, y: off.top, height: off.height, width: off.width })])]));
      if (this.spec.defs && this.spec.defs.length) kids.push(h('defs', {}, this.spec.defs.map(defNode)));
      z0.forEach((n) => kids.push(n));
      NS.surface.Z_LAYERS.filter((z) => z > 0).forEach((z) => kids.push(layer(z)));
      const svgNode = h('svg', svgAttrs, kids);
      const svg = I.toDom(svgNode);
      const old = this.wrapper.querySelector(':scope > svg.recharts-surface');
      const hadFocus = old && document.activeElement === old;
      this.svg = svg;
      if (old) old.replaceWith(svg); else this.wrapper.appendChild(svg);
      if (hadFocus) svg.focus({ preventScroll: true });
      this.drawTooltip();
    }

    /* ---- tooltip ---- */
    tooltipEventType() {
      const t = this.spec.tooltip || {};
      if (this.spec.component === 'PieChart') return t.shared === true ? 'axis' : 'item';
      if (this.spec.component === 'RadarChart') return 'axis';
      if (this.spec.component === 'RadialBarChart') return t.shared === false ? 'item' : 'axis';
      return t.shared === false ? 'item' : 'axis';
    }

    relative(e) {
      const rect = this.wrapper.getBoundingClientRect();
      const sx = this.wrapper.offsetWidth > 0 ? rect.width / this.wrapper.offsetWidth : 1;
      const sy = this.wrapper.offsetHeight > 0 ? rect.height / this.wrapper.offsetHeight : 1;
      return { relativeX: Math.round((e.clientX - rect.left) / sx), relativeY: Math.round((e.clientY - rect.top) / sy) };
    }

    onMove(e) {
      if (!this.spec.tooltip || !this.model) return;
      this.pointerSeen = true;
      const pointer = this.relative(e);
      let itemTarget = null;
      if (this.tooltipEventType() === 'item') {
        const t = e.target && e.target.closest ? e.target.closest('[data-recharts-item-index]') : null;
        itemTarget = t ? { index: Number(t.getAttribute('data-recharts-item-index')), id: t.getAttribute('data-recharts-item-id') } : null;
      }
      this.mouse = this.computeActive(pointer, itemTarget);
      const next = this.resolveActive();
      const prev = this.active;
      const key = (a) => (a ? `${a.index}|${a.itemIndex}|${a.coordinate ? a.coordinate.x : ''},${a.coordinate ? a.coordinate.y : ''}` : '');
      const indexChanged = (next ? `${next.index}|${next.itemIndex}` : '') !== (prev ? `${prev.index}|${prev.itemIndex}` : '');
      this.active = next;
      if (indexChanged) this.draw();
      else if (key(next) !== key(prev)) this.drawTooltip();
    }
    onLeave() {
      this.pointerSeen = true;
      this.mouse = null;
      const next = this.resolveActive();
      if (next || this.active) { this.active = next; this.draw(); }
    }

    computeActive(pointer, itemTarget) {
      const I = L();
      const m = this.model;
      if (this.tooltipEventType() === 'item') {
        if (!itemTarget) return null;
        const it = m.items.find((i) => `recharts-pie-${this.uid}-${i.index}` === itemTarget.id);
        if (!it || !it.sectors[itemTarget.index]) return null;
        const sector = it.sectors[itemTarget.index];
        return { pointer, itemTarget, itemIndex: itemTarget.index, graphicalItem: it.id, index: itemTarget.index, coordinate: sector.tooltipPosition, payload: this.itemPayload(it, itemTarget.index), cursor: false };
      }
      if (m.kind === 'cartesian') {
        const off = m.offset;
        const x = pointer.relativeX, y = pointer.relativeY;
        if (!(x >= off.left && x <= off.left + off.width && y >= off.top && y <= off.top + off.height)) return null;
        const pos = m.layout === 'horizontal' ? x : y;
        const ticks = m.tooltipTicks;
        const ordered = ticks.slice().sort((a, b) => a.coordinate - b.coordinate);
        const idx = NS.surface.calculateActiveTickIndex(pos, ordered, ticks, m.layout === 'horizontal' ? 'xAxis' : 'yAxis', m.tooltipAxis.range);
        const entry = ticks.find((t) => t.index === idx);
        const coordinate = entry ? (m.layout === 'horizontal' ? { x: entry.coordinate, y } : { x, y: entry.coordinate }) : { x: 0, y: 0 };
        return this.finishAxisActive(idx, coordinate, pointer);
      }
      // polar axis tooltip
      const vb = m.polarViewBox;
      const dx = pointer.relativeX - vb.cx, dy = pointer.relativeY - vb.cy;
      const radius = Math.sqrt(dx * dx + dy * dy);
      if (radius < vb.innerRadius || radius > vb.outerRadius || radius === 0) return null;
      let angle = Math.acos(dx / radius) * 180 / Math.PI;
      if (pointer.relativeY > vb.cy) angle = 360 - angle;
      const startCnt = Math.floor(vb.startAngle / 360), endCnt = Math.floor(vb.endAngle / 360);
      const min = Math.min(startCnt, endCnt);
      const sA = vb.startAngle - min * 360, eA = vb.endAngle - min * 360;
      let fa = angle, inRange;
      if (sA <= eA) { while (fa > eA) fa -= 360; while (fa < sA) fa += 360; inRange = fa >= sA && fa <= eA; } else { while (fa > sA) fa -= 360; while (fa < eA) fa += 360; inRange = fa >= eA && fa <= sA; }
      if (!inRange) return null;
      const rangeObj = Object.assign({}, vb, { radius, angle: fa + min * 360 });
      const pos = m.layout === 'centric' ? rangeObj.angle : rangeObj.radius;
      const ticks = m.tooltipTicks;
      const ordered = ticks.slice().sort((a, b) => a.coordinate - b.coordinate);
      const idx = NS.surface.calculateActiveTickIndex(pos, ordered, ticks, m.layout === 'centric' ? 'angleAxis' : 'radiusAxis', m.tooltipAxis.range);
      const entry = ticks.find((t) => t.index === idx);
      let coordinate;
      if (entry) {
        if (m.layout === 'centric') coordinate = Object.assign({}, rangeObj, I.polarToCartesian(vb.cx, vb.cy, rangeObj.radius, entry.coordinate), { angle: entry.coordinate, radius: rangeObj.radius });
        else coordinate = Object.assign({}, rangeObj, I.polarToCartesian(vb.cx, vb.cy, entry.coordinate, rangeObj.angle), { angle: rangeObj.angle, radius: entry.coordinate });
      } else coordinate = { x: 0, y: 0 };
      return this.finishAxisActive(idx, coordinate, pointer);
    }

    /* Clamp the index into the data like combineActiveTooltipIndex, compute payload and label. */
    finishAxisActive(idx, coordinate, pointer) {
      const data = this.ctx.data;
      if (idx == null || !Number.isFinite(Number(idx))) return null;
      const clamped = Math.max(0, Math.min(Number(idx), data.length > 0 ? data.length - 1 : Infinity));
      const ticks = this.model.tooltipTicks;
      const label = ticks && ticks[clamped] ? ticks[clamped].value : undefined;
      const payload = this.axisPayload(clamped, label);
      return { pointer, index: clamped, coordinate, payload, label, cursor: true, payloads: Array.from(new Set(payload.map((p) => p.payload).filter((p) => p != null))) };
    }

    activeForIndex(index, pointer) {
      const m = this.model;
      if (!m || !this.spec.tooltip) return null;
      if (this.tooltipEventType() === 'item') {
        const it = m.items[0];
        if (!it || !it.sectors || !it.sectors[index]) return null;
        return { pointer, itemIndex: index, graphicalItem: it.id, index, coordinate: it.sectors[index].tooltipPosition, payload: this.itemPayload(it, index), cursor: false };
      }
      const tick = m.tooltipTicks && m.tooltipTicks[index];
      if (!tick) return null;
      let coordinate;
      if (m.kind === 'cartesian') coordinate = m.layout === 'horizontal' ? { x: tick.coordinate, y: (m.offset.top + m.height) / 2 } : { x: (m.offset.left + m.width) / 2, y: tick.coordinate };
      else coordinate = { x: 0, y: 0 };
      const a = this.finishAxisActive(index, coordinate, pointer);
      return a;
    }

    itemPayload(it, index) {
      const sector = it.sectors[index];
      const p = it.props;
      const color = p.fill;
      return sector.tooltipPayload.map((item) => ({ stroke: p.stroke, strokeWidth: p.strokeWidth, fill: item.fill != null ? item.fill : color, dataKey: item.dataKey, nameKey: p.nameKey, name: item.name == null ? undefined : String(item.name), hide: p.hide, type: item.type, color: item.color != null ? item.color : color, unit: '', payload: item.payload, value: L().getValue(item.payload, item.dataKey) }));
    }

    axisPayload(index, label) {
      const I = L();
      const m = this.model;
      const data = this.ctx.data;
      const axisKey = m.tooltipAxis && m.tooltipAxis.dataKey;
      const out = [];
      m.items.forEach((it) => {
        const p = it.props;
        const settings = { stroke: p.stroke, strokeWidth: p.strokeWidth, fill: p.fill, dataKey: p.dataKey, name: NS.surface.tooltipNameProp(p.name, p.dataKey), hide: p.hide, type: p.tooltipType, unit: p.unit };
        settings.color = it.component === 'Bar' || it.component === 'RadialBar' ? p.fill : NS.surface.legendColor(p.stroke, p.fill);
        let row;
        if (it.component === 'RadialBar') {
          const sectors = it.sectors || [];
          row = axisKey != null ? sectors.find((s) => I.getValue(s, axisKey) === label) : sectors[index];
        } else if (axisKey != null) row = data.find((r) => I.getValue(r, axisKey) === label);
        else row = data[index];
        const value = I.getValue(row, settings.dataKey);
        out.push(Object.assign({}, settings, { dataKey: settings.dataKey, payload: row, value, name: settings.name }));
      });
      return out.filter((e) => e.value != null && e.hide !== true);
    }

    drawTooltip() {
      const t = this.spec.tooltip;
      const el = this.tooltipEl;
      const a = this.active;
      if (!t || !a || !a.payload || !a.payload.length) {
        el.innerHTML = '';
        el.className = 'recharts-tooltip-wrapper';
        el.setAttribute('style', 'visibility: hidden; pointer-events: none; position: absolute; top: 0px; left: 0px;');
        return;
      }
      const resolved = NS.surface.resolveProps(t, this.ctx);
      const content = tooltipContent(this, resolved, a.payload, a.label);
      el.innerHTML = '';
      el.appendChild(content);
      const prev = el.getAttribute('style') || '';
      if (!/visibility: visible/.test(prev)) el.setAttribute('style', 'visibility: hidden; pointer-events: none; position: absolute; top: 0px; left: 0px;');
      const box = el.getBoundingClientRect();
      const vb = this.model.kind === 'cartesian' ? this.model.viewBox : { x: this.model.offset.left, y: this.model.offset.top, width: this.model.offset.width, height: this.model.offset.height };
      const offset = t.offset != null ? t.offset : 10;
      const pos = (key, dim, vbKey, vbDim) => {
        const negative = a.coordinate[key] - dim - (offset > 0 ? offset : 0);
        const positive = a.coordinate[key] + offset;
        const boundary = positive + dim;
        if (boundary > vb[vbKey] + vb[vbDim]) return Math.max(negative, vb[vbKey]);
        return Math.max(positive, vb[vbKey]);
      };
      if (!(box.width > 0 && box.height > 0)) return;
      const tx = pos('x', box.width, 'x', 'width');
      const ty = pos('y', box.height, 'y', 'height');
      const cls = ['recharts-tooltip-wrapper'];
      cls.push(tx >= a.coordinate.x ? 'recharts-tooltip-wrapper-right' : 'recharts-tooltip-wrapper-left');
      cls.push(ty >= a.coordinate.y ? 'recharts-tooltip-wrapper-bottom' : 'recharts-tooltip-wrapper-top');
      el.className = cls.join(' ');
      const reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      el.setAttribute('style', `visibility: visible; pointer-events: none; position: absolute; top: 0px; left: 0px;${reduced ? '' : ' transition: transform 400ms;'} transform: translate(${tx}px, ${ty}px);`);
    }
  }

  function defNode(d) {
    const { h, A } = L();
    const kids = (d.children || []).map(defNode);
    return h(d.tag, A(d.props || {}), kids);
  }

  NS.Chart = Chart;

  FB.register('chart', {
    init(root) {
      let spec = null;
      const script = root.querySelector(':scope > script[data-chart-spec]');
      if (script) { try { spec = JSON.parse(script.textContent); } catch (e) { console.error('[Flask-Basecoat] invalid chart spec', e); return; } }
      if (!spec) { spec = legacySpec(root); if (spec) ensureStyle(root, spec); }
      if (!spec) return; // a static chart shell
      root.fbChart = new Chart(root, spec);
      root.fbRedraw = () => root.fbChart.render();
      const id = root.getAttribute('data-chart');
      if (id) {
        // Controls sharing one state (a ToggleGroup and a Select both bound to `timeRange`, as upstream) follow each
        // other: the value chosen in one is shown by the others, without them emitting a change of their own.
        let syncing = false;
        const sync = (state, value, source) => {
          syncing = true;
          try {
            document.querySelectorAll(`[data-chart-control="${id}"][data-chart-state="${state}"]`).forEach((o) => {
              if (o === source || !o.fbSetValue) return;
              const current = o.fbGetValue ? o.fbGetValue() : null;
              if (current !== value) o.fbSetValue(value);
            });
          } finally { syncing = false; }
        };
        document.addEventListener('basecoat:change', (e) => {
          if (syncing) return;
          const c = e.target.closest && e.target.closest(`[data-chart-control="${id}"]`);
          if (!c) return;
          const state = c.getAttribute('data-chart-state');
          // a single ToggleGroup reports [value] (or [] once its item is pressed again, upstream's "" value)
          let value = e.detail.value;
          if (Array.isArray(value)) value = value.length ? value[0] : '';
          root.fbChart.setState(state, value);
          sync(state, value, c);
        });
        // spec.onMedia: [{query, state: {name: value}}]: state set when the query matches at load and whenever it
        // starts matching (upstream `useIsMobile()` + `useEffect(() => { if (isMobile) setTimeRange("7d") })`).
        (spec.onMedia || []).forEach((m) => {
          if (!window.matchMedia) return;
          const mql = window.matchMedia(m.query);
          const apply = () => {
            if (!mql.matches) return;
            Object.entries(m.state || {}).forEach(([state, value]) => { root.fbChart.setState(state, value); sync(state, value, null); });
          };
          if (mql.addEventListener) mql.addEventListener('change', apply);
          setTimeout(apply, 0); // after the controls on the page have been initialised
        });
        document.addEventListener('click', (e) => {
          const c = e.target.closest && e.target.closest(`[data-chart-control="${id}"][data-chart-value]`);
          if (!c) return;
          root.fbChart.setState(c.getAttribute('data-chart-state'), c.getAttribute('data-chart-value'));
          document.querySelectorAll(`[data-chart-control="${id}"][data-chart-value]`).forEach((b) => {
            if (b.getAttribute('data-chart-state') === c.getAttribute('data-chart-state')) b.setAttribute('data-active', String(b === c));
          });
        });
      }
    },
  });
})(window.FlaskBasecoat);
