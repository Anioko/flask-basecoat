/* Polar charts for the chart renderer: PieChart, RadarChart and RadialBarChart (ports of Recharts' Pie, Radar,
   RadialBar, PolarGrid, PolarAngleAxis and PolarRadiusAxis, with their selectors). */
(function () {
  'use strict';
  const NS = (window.FlaskBasecoatChart = window.FlaskBasecoatChart || {});
  const I = () => NS.internal;
  const S = () => NS.surface;

  const CHART_DEFAULTS = {
    PieChart: { layout: 'centric', startAngle: 0, endAngle: 360, cx: '50%', cy: '50%', innerRadius: 0, outerRadius: '80%' },
    RadarChart: { layout: 'centric', startAngle: 90, endAngle: -270, cx: '50%', cy: '50%', innerRadius: 0, outerRadius: '80%' },
    RadialBarChart: { layout: 'radial', startAngle: 0, endAngle: 360, cx: '50%', cy: '50%', innerRadius: 0, outerRadius: '80%' },
  };
  const ANGLE_DEFAULTS = { allowDecimals: false, allowDuplicatedCategory: false, allowDataOverflow: false, angle: 0, axisLine: true, axisLineType: 'polygon', hide: false, label: false, niceTicks: 'auto', orientation: 'outer', reversed: false, scale: 'auto', tick: true, tickLine: true, tickSize: 8, type: 'auto' };
  const RADIUS_DEFAULTS = { allowDataOverflow: false, allowDecimals: false, allowDuplicatedCategory: true, angle: 0, axisLine: true, hide: false, niceTicks: 'auto', label: false, orientation: 'right', reversed: false, scale: 'auto', stroke: '#ccc', tick: true, tickCount: 5, tickLine: true, type: 'auto' };

  function buildPolar(chart) {
    const L = I(), SU = S();
    const { getPercentValue, getValue, resolveAxis, bandSizeOfAxis, isNil, polarToCartesian, mathSign } = L;
    const spec = chart.spec, ctx = chart.ctx;
    const W = chart.width, H = chart.height;
    const chartName = spec.component;
    const props = Object.assign({}, CHART_DEFAULTS[chartName], SU.resolveProps(spec.props, ctx));
    const layout = props.layout;
    const margin = SU.margins(props);
    const data = ctx.data;
    const items = spec.series.map((s, idx) => {
      const p = Object.assign({}, SU.SERIES_DEFAULTS[s.component], SU.resolveProps(s, ctx));
      return { component: s.component, props: p, dataKey: p.dataKey, stackId: p.stackId == null ? undefined : String(p.stackId), id: `${s.component.toLowerCase()}-${idx}`, spec: s, index: idx, data: s.component === 'Pie' ? (p.data || data) : data, cells: s.cells };
    });
    const legend = spec.legend ? SU.buildLegendModel(spec, items, ctx, margin, W, H) : null;
    const legendBox = legend ? chart.measureLegend(legend) : null;
    const off = { left: margin.left, right: margin.right, top: margin.top, bottom: margin.bottom };
    if (legend && legendBox) {
      const { layout: ll, align, verticalAlign } = legend.settings;
      if ((ll === 'vertical' || (ll === 'horizontal' && verticalAlign === 'middle')) && align !== 'center') off[align] += legendBox.width || 0;
      else if ((ll === 'horizontal' || (ll === 'vertical' && align === 'center')) && verticalAlign !== 'middle') off[verticalAlign] += legendBox.height || 0;
    }
    off.width = Math.max(W - off.left - off.right, 0);
    off.height = Math.max(H - off.top - off.bottom, 0);
    const maxRadius = Math.min(Math.abs(W - off.left - off.right), Math.abs(H - off.top - off.bottom)) / 2;
    const innerRadius = getPercentValue(props.innerRadius, maxRadius, 0);
    const outerRadius = getPercentValue(props.outerRadius, maxRadius, maxRadius * 0.8);
    const viewBox = { cx: getPercentValue(props.cx, W, W / 2), cy: getPercentValue(props.cy, H, H / 2), innerRadius, outerRadius, startAngle: props.startAngle, endAngle: props.endAngle, clockWise: false };
    const m = { kind: 'polar', layout, chartName, offset: off, width: W, height: H, items, legend, legendBox, margin, data, polarViewBox: viewBox, props };

    if (chartName === 'PieChart') {
      items.forEach((it) => { it.sectors = pieSectors(it, off); });
      m.tooltipEventType = 'item';
      return m;
    }
    // polar axes
    const angleSpec = spec.axes.find((a) => a.component === 'PolarAngleAxis');
    const radiusSpec = spec.axes.find((a) => a.component === 'PolarRadiusAxis');
    const angleAxis = Object.assign({ axisType: 'angleAxis' }, ANGLE_DEFAULTS, angleSpec ? SU.resolveProps(angleSpec, ctx) : { implicit: true }, { allowDuplicatedCategory: false });
    const radiusAxis = Object.assign({ axisType: 'radiusAxis' }, RADIUS_DEFAULTS, radiusSpec ? SU.resolveProps(radiusSpec, ctx) : { implicit: true });
    if (!angleSpec) { angleAxis.tickCount = undefined; }
    [angleAxis, radiusAxis].forEach((ax) => {
      if (ax.type === 'auto') ax.type = L.isCategoricalAxis(layout, ax.axisType) ? 'category' : 'number';
      ax.tickFormatterFn = SU.fn(ax.tickFormatter, ctx);
    });
    angleAxis.range = [props.startAngle, props.endAngle];
    radiusAxis.range = [innerRadius, outerRadius];
    const visible = items.filter((i) => !i.props.hide);
    const axisCtx = { layout, data, items: visible, stackGroups: undefined, stackOffset: 'none', chartName, hasBar: items.some((i) => i.component === 'RadialBar'), polar: true };
    resolveAxis(angleAxis, axisCtx);
    resolveAxis(radiusAxis, axisCtx);
    // PolarAngleAxis keeps one tick per angle
    const seen = new Map();
    angleAxis.ticks_.forEach((t) => { const k = (t.coordinate + 360) % 360; if (!seen.has(k)) seen.set(k, t); });
    angleAxis.uniqueTicks = Array.from(seen.values());
    m.angleAxis = angleAxis; m.radiusAxis = radiusAxis;
    m.tooltipAxis = layout === 'centric' ? angleAxis : radiusAxis;
    m.tooltipTicks = m.tooltipAxis.tooltipTicks;

    if (chartName === 'RadarChart') {
      const bandSize = L.isCategoricalAxis(layout, 'radiusAxis') ? bandSizeOfAxis(radiusAxis, radiusAxis.ticks_, false) : bandSizeOfAxis(angleAxis, angleAxis.ticks_, false);
      items.forEach((it) => {
        const angleBand = angleAxis.type !== 'number' ? (bandSize || 0) : 0;
        it.points = data.map((entry, i) => {
          const name = getValue(entry, angleAxis.dataKey, i);
          const value = getValue(entry, it.dataKey);
          const sc = angleAxis.scale(name);
          const angle = (sc == null ? 0 : sc) + angleBand;
          const pv = Array.isArray(value) ? value[value.length - 1] : value;
          const r = isNil(pv) ? 0 : radiusAxis.scale(pv);
          const radius = r == null ? 0 : r;
          return Object.assign(polarToCartesian(viewBox.cx, viewBox.cy, radius, angle), { name, value, cx: viewBox.cx, cy: viewBox.cy, radius, angle, payload: entry });
        });
      });
      return m;
    }

    // RadialBarChart
    const bars = visible.filter((i) => i.component === 'RadialBar');
    const catAxis = L.isCategoricalAxis(layout, 'radiusAxis') ? radiusAxis : angleAxis;
    const numAxis = catAxis === radiusAxis ? angleAxis : radiusAxis;
    const groups = {};
    bars.filter((b) => b.stackId != null).forEach((b) => { (groups[b.stackId] = groups[b.stackId] || []).push(b); });
    const sizeList = Object.keys(groups).map((sid) => ({ stackId: sid, dataKeys: groups[sid].map((b) => b.dataKey), barSize: groups[sid][0].props.barSize != null ? groups[sid][0].props.barSize : props.barSize }))
      .concat(bars.filter((b) => b.stackId == null).map((b) => ({ stackId: undefined, dataKeys: [b.dataKey].filter((k) => k != null), barSize: b.props.barSize != null ? b.props.barSize : props.barSize })));
    const barBand = bandSizeOfAxis(catAxis, catAxis.itemTicks, true);
    const barBandSize = (barBand != null ? barBand : props.maxBarSize) || 0;
    const axisBand = bandSizeOfAxis(catAxis, catAxis.itemTicks, false);
    let positions = SU.barPositionList(props.barGap != null ? props.barGap : 4, props.barCategoryGap != null ? props.barCategoryGap : '10%', barBandSize !== axisBand ? barBandSize : axisBand, sizeList, props.maxBarSize);
    if (barBandSize !== axisBand && positions) positions = positions.map((p) => Object.assign({}, p, { position: Object.assign({}, p.position, { offset: p.position.offset - barBandSize / 2 }) }));
    // stacks (by the categorical axis' tooltip value, as combineDisplayedStackedData)
    let stackGroups;
    const stacked = bars.filter((b) => b.stackId != null);
    if (stacked.length) {
      stackGroups = {};
      const rows = data.map((entry) => { const row = {}; stacked.forEach((it) => { row[it.id] = getValue(entry, it.dataKey, 0); }); return row; });
      Object.keys(groups).forEach((sid) => { stackGroups[sid] = { stackedData: NS.d3.stack(rows, groups[sid].map((b) => b.id), (d, k) => Number(getValue(d, k, 0)), props.stackOffset || 'none') }; });
    }
    const baseValue = SU.baseValueOfBar(numAxis);
    bars.forEach((it) => {
      const pos = positions && positions.find((p) => p.stackId === it.stackId && it.dataKey != null && p.dataKeys.includes(it.dataKey));
      const stackedData = stackGroups && it.stackId != null ? stackGroups[it.stackId].stackedData.find((sd) => sd.key === it.id) : undefined;
      const stackedDomain = stackedData ? numAxis.scale.domain() : null;
      if (!pos) { it.sectors = []; return; }
      it.sectors = data.map((entry, index) => {
        let value = stackedData ? SU.truncateByDomain([stackedData[index][0], stackedData[index][1]], stackedDomain) : getValue(entry, it.dataKey);
        if (!stackedData && !Array.isArray(value)) value = [baseValue, value];
        let innerR, outerR, startA, endA, bg;
        if (layout === 'radial') {
          const s = angleAxis.scale(value[0]), e = angleAxis.scale(value[1]);
          startA = s == null ? props.startAngle : s;
          endA = e == null ? props.endAngle : e;
          const t = radiusAxis.type === 'category' ? radiusAxis.itemTicks[index] : null;
          innerR = t ? t.coordinate + pos.position.offset : null;
          if (innerR != null) {
            outerR = innerR + pos.position.size;
            const minPointSize = it.props.minPointSize || 0;
            const delta = endA - startA;
            if (Math.abs(minPointSize) > 0 && Math.abs(delta) < Math.abs(minPointSize)) endA += mathSign(delta || minPointSize) * (Math.abs(minPointSize) - Math.abs(delta));
            bg = { background: { cx: viewBox.cx, cy: viewBox.cy, innerRadius: innerR, outerRadius: outerR, startAngle: props.startAngle, endAngle: props.endAngle } };
          }
        }
        return Object.assign({}, entry, bg, { payload: entry, value: stackedData ? value : value[1], cx: viewBox.cx, cy: viewBox.cy, innerRadius: innerR, outerRadius: outerR, startAngle: startA, endAngle: endA }, it.cells && it.cells[index] ? it.cells[index] : {});
      });
    });
    return m;
  }

  function pieSectors(it, offset) {
    const { getPercentValue, getValue, isNum, mathSign, polarToCartesian } = I();
    const p = it.props;
    const data = it.data || [];
    const minAngle = Math.abs(p.minAngle);
    const sign0 = mathSign(p.endAngle - p.startAngle);
    const deltaAngle = sign0 * Math.min(Math.abs(p.endAngle - p.startAngle), 360);
    const absDelta = Math.abs(deltaAngle);
    const paddingAngle = data.length <= 1 ? 0 : (p.paddingAngle || 0);
    const notZero = data.filter((e) => getValue(e, p.dataKey, 0) !== 0).length;
    const totalPadding = (absDelta >= 360 ? notZero : notZero - 1) * paddingAngle;
    const realTotalAngle = absDelta - notZero * minAngle - totalPadding;
    const sum = data.reduce((r, e) => { const v = getValue(e, p.dataKey, 0); return r + (isNum(v) ? v : 0); }, 0);
    if (!(sum > 0)) return [];
    const maxPieRadius = Math.min(offset.width, offset.height) / 2;
    const presentation = I().svgProps(S().seriesSvgProps(it));
    let prev;
    return data.map((entry, i) => {
      const val = getValue(entry, p.dataKey, 0);
      const name = getValue(entry, p.nameKey, i);
      const coordinate = {
        cx: offset.left + getPercentValue(p.cx, offset.width, offset.width / 2),
        cy: offset.top + getPercentValue(p.cy, offset.height, offset.height / 2),
        innerRadius: getPercentValue(p.innerRadius, maxPieRadius, 0),
        outerRadius: getPercentValue(p.outerRadius, maxPieRadius, maxPieRadius * 0.8),
        maxRadius: p.maxRadius || Math.sqrt(offset.width * offset.width + offset.height * offset.height) / 2,
      };
      const percent = (isNum(val) ? val : 0) / sum;
      const withCell = Object.assign({}, entry, it.cells && it.cells[i] ? it.cells[i] : {});
      const color = withCell != null && typeof withCell.fill === 'string' ? withCell.fill : p.fill;
      const start = i ? prev.endAngle + mathSign(deltaAngle) * paddingAngle * (val !== 0 ? 1 : 0) : p.startAngle;
      const end = start + mathSign(deltaAngle) * ((val !== 0 ? minAngle : 0) + percent * realTotalAngle);
      const midAngle = (start + end) / 2;
      const middleRadius = (coordinate.innerRadius + coordinate.outerRadius) / 2;
      const tooltipPayload = [{ name, value: val, payload: withCell, dataKey: p.dataKey, type: p.tooltipType, color, fill: color }];
      prev = Object.assign({}, presentation, { percent, cornerRadius: typeof p.cornerRadius === 'string' ? parseFloat(p.cornerRadius) : p.cornerRadius, name, tooltipPayload, midAngle, middleRadius, tooltipPosition: polarToCartesian(coordinate.cx, coordinate.cy, middleRadius, midAngle) }, withCell, coordinate, { value: val, dataKey: p.dataKey, startAngle: start, endAngle: end, payload: withCell, paddingAngle: mathSign(deltaAngle) * paddingAngle });
      return prev;
    });
  }

  /* ---------------------------------------------------------------- rendering */
  function renderPolar(chart, m, active) {
    const SU = S();
    const layers = SU.newLayers();
    const z0 = [];
    const labelsLater = [];
    const spec = chart.spec;
    if (m.chartName === 'PieChart') {
      m.items.forEach((it) => renderPie(chart, m, it, layers, labelsLater, active));
    } else {
      // render order follows the upstream JSX: grid, series, axes
      if (spec.grid) layers[SU.Z.grid].push(renderPolarGrid(chart, m));
      m.items.forEach((it) => {
        if (it.props.hide) return;
        if (it.component === 'Radar') renderRadar(chart, m, it, layers, labelsLater, active);
        else if (it.component === 'RadialBar') renderRadialBar(chart, m, it, layers, labelsLater, active);
      });
      spec.axes.forEach((a) => {
        if (a.component === 'PolarAngleAxis' && !m.angleAxis.hide) renderAngleAxis(chart, m, layers);
        if (a.component === 'PolarRadiusAxis' && !m.radiusAxis.hide) renderRadiusAxis(chart, m, layers, labelsLater);
      });
    }
    if (active && active.cursor && spec.tooltip && spec.tooltip.cursor !== false && m.layout === 'centric' && m.chartName !== 'PieChart') {
      const L = I();
      const coord = active.coordinate;
      const a = L.polarToCartesian(coord.cx, coord.cy, coord.innerRadius, coord.angle), b = L.polarToCartesian(coord.cx, coord.cy, coord.outerRadius, coord.angle);
      const extra = typeof spec.tooltip.cursor === 'object' ? L.svgProps(spec.tooltip.cursor) : {};
      layers[SU.Z.cursorLine].push(L.Curve(Object.assign({ stroke: '#ccc', pointerEvents: 'none', width: m.offset.width, height: m.offset.height, points: [a, b] }, extra, { className: 'recharts-tooltip-cursor' })));
    }
    labelsLater.forEach((l) => layers[SU.Z.label].push(l));
    return { layers, z0 };
  }

  function pieLabelContextEntries(sectors) {
    return sectors.map((e) => ({ value: e.value, payload: e.payload, clockWise: false, parentViewBox: undefined, viewBox: { cx: e.cx, cy: e.cy, innerRadius: e.innerRadius, outerRadius: e.outerRadius, startAngle: e.startAngle, endAngle: e.endAngle, clockWise: false }, fill: e.fill }));
  }

  function renderPie(chart, m, it, layers, labelsLater, active) {
    const L = I(), SU = S();
    const { h, Shape, svgProps, Text, Curve, polarToCartesian, getValue } = L;
    const p = it.props;
    const sectors = it.sectors || [];
    const kids = sectors.map((entry, i) => {
      if (entry.startAngle === 0 && entry.endAngle === 0 && sectors.length !== 1) return null;
      const isActive = !!active && active.itemIndex === i && active.graphicalItem === it.id;
      const sp = Object.assign({}, entry, { stroke: entry.stroke, tabIndex: -1, 'data-recharts-item-index': i, 'data-recharts-item-id': `recharts-pie-${chart.uid}-${it.index}` });
      const props = Object.assign({}, svgProps(sp), { cx: entry.cx, cy: entry.cy, innerRadius: entry.innerRadius, outerRadius: entry.outerRadius, startAngle: entry.startAngle, endAngle: entry.endAngle, cornerRadius: entry.cornerRadius, index: i, isActive, payload: entry.payload });
      return h('g', { class: 'recharts-layer recharts-pie-sector', tabindex: -1 }, [Shape('sector', p.shape || null, props, chart.ctx)]);
    });
    const inner = [h('g', { class: 'recharts-layer' }, kids)];
    // label prop
    if (p.label) {
      const offsetRadius = (typeof p.label === 'object' && typeof p.label.offsetRadius === 'number' && p.label.offsetRadius) || 20;
      const pieProps = svgProps(SU.seriesSvgProps(it));
      const custom = typeof p.label === 'object' && !p.label.$fn ? svgProps(p.label) : {};
      const customLine = typeof p.labelLine === 'object' ? svgProps(p.labelLine) : {};
      const groups = sectors.map((entry, i) => {
        const mid = (entry.startAngle + entry.endAngle) / 2;
        const endPoint = polarToCartesian(entry.cx, entry.cy, entry.outerRadius + offsetRadius, mid);
        const anchor = endPoint.x > entry.cx ? 'start' : endPoint.x < entry.cx ? 'end' : 'middle';
        const labelProps = Object.assign({}, pieProps, svgProps(entry), { stroke: 'none' }, custom, { index: i, textAnchor: anchor }, endPoint);
        const lineProps = Object.assign({}, pieProps, svgProps(entry), { fill: 'none', stroke: entry.fill }, customLine, { index: i, points: [polarToCartesian(entry.cx, entry.cy, entry.outerRadius, mid), endPoint] });
        let labelEl;
        if (p.label.$fn) labelEl = SU.fn(p.label, chart.ctx)(Object.assign({}, labelProps, { payload: entry.payload, cx: entry.cx, cy: entry.cy }));
        else labelEl = Text(Object.assign({}, labelProps, { alignmentBaseline: 'middle', className: ['recharts-pie-label-text', typeof p.label === 'object' ? p.label.className : ''].filter(Boolean).join(' ') }), getValue(entry, p.dataKey));
        const line = p.labelLine ? Curve(Object.assign({}, lineProps, { type: 'linear', className: ['recharts-pie-label-line', typeof p.labelLine === 'object' ? p.labelLine.className : ''].filter(Boolean).join(' ') })) : null;
        labelsLater.push(h('g', { class: 'recharts-layer' }, [line, labelEl]));
        return null;
      });
      void groups;
      inner.push(h('g', { class: 'recharts-layer recharts-pie-labels' }, []));
    }
    const ctxEntries = pieLabelContextEntries(sectors);
    (it.spec.labelList || []).forEach((ll) => labelsLater.push(SU.LabelList(ll, ctxEntries, chart.ctx)));
    (it.spec.labels || []).forEach((lb) => {
      const el = SU.Label(Object.assign({}, SU.resolveProps(lb, chart.ctx), { viewBox: m.polarViewBox }), chart.ctx);
      if (el) inner.push(el);
    });
    layers[SU.Z.area].push(h('g', { class: 'recharts-layer recharts-pie', tabindex: p.rootTabIndex }, inner));
  }

  function renderPolarGrid(chart, m) {
    const L = I(), SU = S();
    const { h, svgProps, A, polarToCartesian } = L;
    const g = Object.assign({ gridType: 'polygon', radialLines: true }, SU.resolveProps(chart.spec.grid, chart.ctx));
    const vb = m.polarViewBox;
    const polarAngles = Array.isArray(g.polarAngles) ? g.polarAngles : m.angleAxis.ticks_.map((t) => t.coordinate);
    const polarRadius = Array.isArray(g.polarRadius) ? g.polarRadius : m.radiusAxis.ticks_.map((t) => t.coordinate);
    if (!(vb.outerRadius > 0)) return null;
    const inputs = Object.assign({}, g);
    ['gridType', 'radialLines', 'angleAxisId', 'radiusAxisId', 'cx', 'cy', 'innerRadius', 'outerRadius', 'polarAngles', 'polarRadius', 'zIndex', 'component'].forEach((k) => delete inputs[k]);
    const props = Object.assign({ cx: vb.cx, cy: vb.cy, innerRadius: vb.innerRadius, outerRadius: vb.outerRadius }, inputs);
    const polygonD = (radius) => {
      let d = '';
      polarAngles.forEach((angle, i) => { const pt = polarToCartesian(props.cx, props.cy, radius, angle); d += (i ? 'L ' : 'M ') + pt.x + ',' + pt.y; });
      return d + 'Z';
    };
    const shapeEl = (radius, fill) => {
      const base = Object.assign({ stroke: '#ccc', fill: 'none' }, svgProps(Object.assign({}, props, { radius })));
      if (fill !== undefined) base.fill = fill;
      const cls = base.className; delete base.className;
      if (g.gridType === 'circle') {
        const a = A(base);
        return h('circle', Object.assign(a, { class: ['recharts-polar-grid-concentric-circle', cls].filter(Boolean).join(' '), cx: props.cx, cy: props.cy, r: radius }));
      }
      return h('path', Object.assign(A(base), { class: ['recharts-polar-grid-concentric-polygon', cls].filter(Boolean).join(' '), d: polygonD(radius) }));
    };
    const concentric = [];
    if (polarRadius && polarRadius.length) {
      const maxR = Math.max(...polarRadius);
      if (props.fill && props.fill !== 'none') concentric.push(shapeEl(maxR, undefined));
      polarRadius.forEach((r) => concentric.push(shapeEl(r, 'none')));
    }
    const kids = [h('g', { class: 'recharts-polar-grid-concentric' }, concentric)];
    if (polarAngles && polarAngles.length && g.radialLines) {
      const lp = Object.assign({ stroke: '#ccc' }, svgProps(props));
      kids.push(h('g', { class: 'recharts-polar-grid-angle' }, polarAngles.map((angle) => {
        const s = polarToCartesian(props.cx, props.cy, props.innerRadius, angle), e = polarToCartesian(props.cx, props.cy, props.outerRadius, angle);
        return h('line', Object.assign(A(lp), { x1: s.x, y1: s.y, x2: e.x, y2: e.y }));
      })));
    }
    return h('g', { class: 'recharts-polar-grid' }, kids);
  }

  function renderAngleAxis(chart, m, layers) {
    const L = I(), SU = S();
    const { h, svgProps, A, Text, Polygon, Dot, polarToCartesian } = L;
    const ax = m.angleAxis;
    const vb = m.polarViewBox;
    const ticks = ax.uniqueTicks;
    if (!ticks || !ticks.length) return;
    const userProps = SU.resolveProps(chart.spec.axes.find((a) => a.component === 'PolarAngleAxis'), chart.ctx);
    const props = Object.assign({}, ANGLE_DEFAULTS, userProps, vb, { radius: vb.outerRadius });
    const base = svgProps(props);
    delete base.className;
    const children = [];
    if (props.axisLine) {
      const lp = Object.assign({}, base, { fill: 'none' }, typeof props.axisLine === 'object' ? svgProps(props.axisLine) : {});
      if (props.axisLineType === 'circle') children.push(Dot(Object.assign({}, lp, { className: 'recharts-polar-angle-axis-line', cx: vb.cx, cy: vb.cy, r: vb.outerRadius })));
      else children.push(Polygon(Object.assign({}, lp, { className: 'recharts-polar-angle-axis-line', points: ticks.map((t) => polarToCartesian(vb.cx, vb.cy, vb.outerRadius, t.coordinate)) })));
    }
    const eps = 1e-5, COS45 = Math.cos(45 * Math.PI / 180);
    const custom = typeof props.tick === 'object' && !props.tick.$fn ? svgProps(props.tick) : {};
    const items = ticks.map((entry, i) => {
      const size = props.tickSize || 8;
      const p1 = polarToCartesian(vb.cx, vb.cy, vb.outerRadius, entry.coordinate);
      const p2 = polarToCartesian(vb.cx, vb.cy, vb.outerRadius + (props.orientation === 'inner' ? -1 : 1) * size, entry.coordinate);
      const line = { x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y };
      const cos = Math.cos(-entry.coordinate * Math.PI / 180), sin = Math.sin(-entry.coordinate * Math.PI / 180);
      const textAnchor = cos > eps ? (props.orientation === 'outer' ? 'start' : 'end') : cos < -eps ? (props.orientation === 'outer' ? 'end' : 'start') : 'middle';
      const verticalAnchor = Math.abs(cos) <= COS45 ? (sin > 0 ? 'start' : 'end') : 'middle';
      const tp = Object.assign({}, base, { textAnchor, verticalAnchor, stroke: 'none', fill: props.stroke }, custom, { index: i, payload: entry, x: line.x2, y: line.y2 });
      const value = ax.tickFormatterFn ? ax.tickFormatterFn(entry.value, i) : entry.value;
      let textEl = null;
      if (props.tick) {
        if (props.tick.$fn) textEl = SU.fn(props.tick, chart.ctx)(tp);
        else textEl = Text(Object.assign({}, tp, { className: 'recharts-polar-angle-axis-tick-value' }), value);
      }
      return h('g', { class: ['recharts-layer recharts-polar-angle-axis-tick', typeof props.tick === 'object' && props.tick.className].filter(Boolean).join(' ') }, [
        props.tickLine ? h('line', Object.assign(A(Object.assign({}, base, { fill: 'none' }, typeof props.tickLine === 'object' ? svgProps(props.tickLine) : {})), { class: 'recharts-polar-angle-axis-tick-line' }, line)) : null,
        textEl,
      ]);
    });
    children.push(h('g', { class: 'recharts-layer recharts-polar-angle-axis-ticks' }, items));
    layers[SU.Z.axis].push(h('g', { class: ['recharts-layer recharts-polar-angle-axis angleAxis', userProps.className].filter(Boolean).join(' ') }, children));
  }

  function renderRadiusAxis(chart, m, layers, labelsLater) {
    const L = I(), SU = S();
    const { h, svgProps, A, Text, polarToCartesian } = L;
    const ax = m.radiusAxis;
    const vb = m.polarViewBox;
    const ticks = ax.ticks_;
    if (!ticks || !ticks.length) return;
    const userProps = SU.resolveProps(chart.spec.axes.find((a) => a.component === 'PolarRadiusAxis'), chart.ctx);
    const props = Object.assign({}, RADIUS_DEFAULTS, userProps, vb);
    const angle = props.angle;
    const kids = [];
    if (props.axisLine) {
      const ext = ticks.reduce((r, e) => [Math.min(r[0], e.coordinate), Math.max(r[1], e.coordinate)], [Infinity, -Infinity]);
      const p0 = polarToCartesian(vb.cx, vb.cy, ext[0], angle), p1 = polarToCartesian(vb.cx, vb.cy, ext[1], angle);
      const others = Object.assign({}, props); delete others.cx; delete others.cy; delete others.angle; delete others.axisLine;
      const lp = Object.assign({}, svgProps(others), { fill: 'none' }, typeof props.axisLine === 'object' ? svgProps(props.axisLine) : {}, { x1: p0.x, y1: p0.y, x2: p1.x, y2: p1.y });
      delete lp.className;
      kids.push(h('line', Object.assign({ class: 'recharts-polar-radius-axis-line' }, A(lp))));
    }
    if (props.tick) {
      const textAnchor = { left: 'end', right: 'start' }[props.orientation] || 'middle';
      const others = Object.assign({}, props); delete others.angle; delete others.tickFormatter; delete others.stroke; delete others.tick;
      const axisProps = svgProps(others);
      delete axisProps.className;
      const custom = typeof props.tick === 'object' ? svgProps(props.tick) : {};
      kids.push(h('g', { class: 'recharts-layer recharts-polar-radius-axis-ticks' }, ticks.map((entry, i) => {
        const c = polarToCartesian(vb.cx, vb.cy, entry.coordinate, props.angle);
        const tp = Object.assign({ textAnchor, transform: `rotate(${90 - angle}, ${c.x}, ${c.y})` }, axisProps, { stroke: 'none', fill: props.stroke }, custom, { index: i }, c, { payload: entry });
        return h('g', { class: ['recharts-layer recharts-polar-radius-axis-tick', typeof props.tick === 'object' && props.tick.className].filter(Boolean).join(' ') }, [Text(Object.assign({}, tp, { className: 'recharts-polar-radius-axis-tick-value' }), ax.tickFormatterFn ? ax.tickFormatterFn(entry.value, i) : entry.value)]);
      })));
    }
    const maxT = ticks.reduce((a, b) => ((b.coordinate || 0) > (a.coordinate || 0) ? b : a));
    const minT = ticks.reduce((a, b) => ((b.coordinate || 0) < (a.coordinate || 0) ? b : a));
    const labelVB = { cx: vb.cx, cy: vb.cy, startAngle: angle, endAngle: angle, innerRadius: minT.coordinate || 0, outerRadius: maxT.coordinate || 0, clockWise: false };
    const spec = chart.spec.axes.find((a) => a.component === 'PolarRadiusAxis');
    (spec.labels || []).forEach((lb) => {
      const el = SU.Label(Object.assign({}, SU.resolveProps(lb, chart.ctx), { viewBox: labelVB }), chart.ctx);
      if (el) kids.push(el);
    });
    layers[SU.Z.axis].push(h('g', { class: ['recharts-layer recharts-polar-radius-axis radiusAxis', userProps.className].filter(Boolean).join(' ') }, kids));
  }

  function renderRadar(chart, m, it, layers, labelsLater, active) {
    const L = I(), SU = S();
    const { h, svgProps, Polygon } = L;
    const p = it.props;
    const base = svgProps(SU.seriesSvgProps(it));
    const polygon = Polygon(Object.assign({}, base, { id: `recharts-radar-${chart.uid}-${it.index}`, points: it.points, connectNulls: p.connectNulls }));
    layers[SU.Z.area].push(h('g', { class: ['recharts-layer recharts-radar', p.className].filter(Boolean).join(' ') }, [
      h('g', { class: 'recharts-layer recharts-radar-polygon' }, [polygon]),
    ]));
    const dotBase = Object.assign({}, base);
    delete dotBase.id;
    SU.dotsLayer(chart, it, it.points, 'recharts-radar-dots', 'recharts-radar-dot', dotBase, layers);
    SU.activePointLayer(chart, it, it.points, SU.legendColor(p.stroke, p.fill), active, layers);
  }

  function renderRadialBar(chart, m, it, layers, labelsLater, active) {
    const L = I(), SU = S();
    const { h, svgProps, Shape } = L;
    const p = it.props;
    const sectors = it.sectors || [];
    const others = SU.seriesSvgProps(it);
    delete others.cornerRadius; delete others.id;
    const baseProps = svgProps(others);
    delete baseProps.className;
    const kids = [];
    if (p.background) {
      kids.push(h('g', { class: 'recharts-layer recharts-radial-bar-background' }, []));
      const bgProps = typeof p.background === 'object' ? svgProps(p.background) : {};
      sectors.forEach((entry, i) => {
        if (!entry.background) return;
        const rest = Object.assign({}, entry); delete rest.value; delete rest.background;
        const sp = Object.assign({ cornerRadius: p.cornerRadius }, rest, { fill: '#eee' }, entry.background, bgProps, { index: i });
        const attrs = Object.assign({}, svgProps(sp), { cx: sp.cx, cy: sp.cy, innerRadius: sp.innerRadius, outerRadius: sp.outerRadius, startAngle: sp.startAngle, endAngle: sp.endAngle, cornerRadius: sp.cornerRadius, className: 'recharts-radial-bar-background-sector ' + String(bgProps.className), isActive: false });
        layers[SU.Z.barBackground].push(Shape('sector', typeof p.background === 'object' ? p.background : null, attrs, chart.ctx));
      });
    }
    const sectorEls = sectors.map((entry, i) => {
      const sp = Object.assign({}, baseProps, { cornerRadius: p.cornerRadius }, entry);
      const attrs = Object.assign({}, svgProps(sp), { cx: entry.cx, cy: entry.cy, innerRadius: entry.innerRadius, outerRadius: entry.outerRadius, startAngle: entry.startAngle, endAngle: entry.endAngle, cornerRadius: typeof p.cornerRadius === 'string' ? parseInt(p.cornerRadius, 10) : p.cornerRadius, forceCornerRadius: p.forceCornerRadius, cornerIsExternal: p.cornerIsExternal, className: 'recharts-radial-bar-sector ' + String(entry.className), isActive: false, index: i });
      return Shape('sector', p.shape || null, attrs, chart.ctx);
    });
    kids.push(h('g', { class: 'recharts-layer recharts-radial-bar-sectors' }, sectorEls));
    layers[SU.Z.bar].push(h('g', { class: ['recharts-layer recharts-area', p.className].filter(Boolean).join(' ') }, kids));
    const entries = sectors.map((s) => ({ value: s.value, payload: s.payload, parentViewBox: undefined, clockWise: false, viewBox: { cx: s.cx, cy: s.cy, innerRadius: s.innerRadius, outerRadius: s.outerRadius, startAngle: s.startAngle, endAngle: s.endAngle, clockWise: false }, fill: s.fill }));
    (it.spec.labelList || []).forEach((ll) => labelsLater.push(SU.LabelList(ll, entries, chart.ctx)));
  }

  NS.polar = { buildPolar, renderPolar };
})();
