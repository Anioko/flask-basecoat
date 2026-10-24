/* Chart surface: turns a chart spec plus the measured container size and the tooltip state into the element
   tree Recharts renders (svg.recharts-surface with its z-index layers), the tooltip model and the legend model.
   Cartesian charts (AreaChart, BarChart, LineChart) and polar charts (PieChart, RadarChart, RadialBarChart). */
(function () {
  'use strict';
  const NS = (window.FlaskBasecoatChart = window.FlaskBasecoatChart || {});
  const Z_LAYERS = [-100, -50, 100, 200, 300, 400, 500, 600, 1000, 1100, 1200, 2000];
  const Z = { grid: -100, barBackground: -50, area: 100, cursorRectangle: 200, bar: 300, line: 400, axis: 500, scatter: 600, activeBar: 1000, cursorLine: 1100, activeDot: 1200, label: 2000 };

  function I() { return NS.internal; }

  /* ---------------------------------------------------------------- function-valued props */
  function fn(ref, ctx) {
    if (ref && typeof ref === 'object' && ref.$fn) return NS.formatters.resolve(ref, ctx);
    return typeof ref === 'function' ? ref : undefined;
  }
  function stateValue(v, ctx) {
    if (v && typeof v === 'object' && !Array.isArray(v) && 'state' in v && Object.keys(v).length === 1) return ctx.state[v.state];
    return v;
  }
  /* Resolve {"state": name} references and $template strings against the chart state. */
  function resolveProps(obj, ctx) {
    const out = {};
    for (const k of Object.keys(obj || {})) {
      let v = stateValue(obj[k], ctx);
      if (v && typeof v === 'object' && v.$template) v = v.$template.replace(/\{(\w+)\}/g, (_, n) => ctx.state[n]);
      out[k] = v;
    }
    return out;
  }

  /* ---------------------------------------------------------------- shared helpers */
  function tooltipNameProp(name, dataKey) {
    if (name) return String(name);
    if (typeof dataKey === 'string') return dataKey;
    return undefined;
  }
  const legendColor = (stroke, fill) => (stroke && stroke !== 'none' ? stroke : fill);

  function viewBoxToTrapezoid(vb) {
    if (vb == null) return vb;
    if ('upperWidth' in vb) return vb;
    return { x: vb.x, y: vb.y, width: vb.width, height: vb.height, upperWidth: vb.width, lowerWidth: vb.width };
  }

  /* recharts/cartesian/getCartesianPosition */
  function cartesianPosition(viewBox, position, offset, parentViewBox, clamp) {
    const { x, y, height, upperWidth, lowerWidth } = viewBoxToTrapezoid(viewBox);
    const upperX = x, lowerX = x + (upperWidth - lowerWidth) / 2, middleX = (upperX + lowerX) / 2;
    const midHeightWidth = (upperWidth + lowerWidth) / 2, centerX = upperX + upperWidth / 2;
    const vSign = height >= 0 ? 1 : -1, vOff = vSign * offset, vEnd = vSign > 0 ? 'end' : 'start', vStart = vSign > 0 ? 'start' : 'end';
    const hSign = upperWidth >= 0 ? 1 : -1, hOff = hSign * offset, hEnd = hSign > 0 ? 'end' : 'start', hStart = hSign > 0 ? 'start' : 'end';
    const pv = parentViewBox;
    if (position === 'top') {
      const r = { x: upperX + upperWidth / 2, y: y - vOff, horizontalAnchor: 'middle', verticalAnchor: vEnd };
      if (clamp && pv) { r.height = Math.max(y - pv.y, 0); r.width = upperWidth; }
      return r;
    }
    if (position === 'bottom') {
      const r = { x: lowerX + lowerWidth / 2, y: y + height + vOff, horizontalAnchor: 'middle', verticalAnchor: vStart };
      if (clamp && pv) { r.height = Math.max(pv.y + pv.height - (y + height), 0); r.width = lowerWidth; }
      return r;
    }
    if (position === 'left') {
      const r = { x: middleX - hOff, y: y + height / 2, horizontalAnchor: hEnd, verticalAnchor: 'middle' };
      if (clamp && pv) { r.width = Math.max(r.x - pv.x, 0); r.height = height; }
      return r;
    }
    if (position === 'right') {
      const r = { x: middleX + midHeightWidth + hOff, y: y + height / 2, horizontalAnchor: hStart, verticalAnchor: 'middle' };
      if (clamp && pv) { r.width = Math.max(pv.x + pv.width - r.x, 0); r.height = height; }
      return r;
    }
    const size = clamp && pv ? { width: midHeightWidth, height } : {};
    const m = (o) => Object.assign(o, size);
    switch (position) {
      case 'insideLeft': return m({ x: middleX + hOff, y: y + height / 2, horizontalAnchor: hStart, verticalAnchor: 'middle' });
      case 'insideRight': return m({ x: middleX + midHeightWidth - hOff, y: y + height / 2, horizontalAnchor: hEnd, verticalAnchor: 'middle' });
      case 'insideTop': return m({ x: upperX + upperWidth / 2, y: y + vOff, horizontalAnchor: 'middle', verticalAnchor: vStart });
      case 'insideBottom': return m({ x: lowerX + lowerWidth / 2, y: y + height - vOff, horizontalAnchor: 'middle', verticalAnchor: vEnd });
      case 'insideTopLeft': return m({ x: upperX + hOff, y: y + vOff, horizontalAnchor: hStart, verticalAnchor: vStart });
      case 'insideTopRight': return m({ x: upperX + upperWidth - hOff, y: y + vOff, horizontalAnchor: hEnd, verticalAnchor: vStart });
      case 'insideBottomLeft': return m({ x: lowerX + hOff, y: y + height - vOff, horizontalAnchor: hStart, verticalAnchor: vEnd });
      case 'insideBottomRight': return m({ x: lowerX + lowerWidth - hOff, y: y + height - vOff, horizontalAnchor: hEnd, verticalAnchor: vEnd });
      default: return m({ x: centerX, y: y + height / 2, horizontalAnchor: 'middle', verticalAnchor: 'middle' });
    }
  }

  /* recharts/component/Label getAttrsOfPolarLabel */
  function polarLabelAttrs(vb, offset, position) {
    const { polarToCartesian } = I();
    const midAngle = (vb.startAngle + vb.endAngle) / 2;
    if (position === 'outside') {
      const p = polarToCartesian(vb.cx, vb.cy, vb.outerRadius + offset, midAngle);
      return { x: p.x, y: p.y, textAnchor: p.x >= vb.cx ? 'start' : 'end', verticalAnchor: 'middle' };
    }
    if (position === 'center') return { x: vb.cx, y: vb.cy, textAnchor: 'middle', verticalAnchor: 'middle' };
    if (position === 'centerTop') return { x: vb.cx, y: vb.cy, textAnchor: 'middle', verticalAnchor: 'start' };
    if (position === 'centerBottom') return { x: vb.cx, y: vb.cy, textAnchor: 'middle', verticalAnchor: 'end' };
    const r = (vb.innerRadius + vb.outerRadius) / 2;
    const p = polarToCartesian(vb.cx, vb.cy, r, midAngle);
    return { x: p.x, y: p.y, textAnchor: 'middle', verticalAnchor: 'middle' };
  }
  const isPolarVB = (vb) => vb != null && 'cx' in vb && I().isNum(vb.cx);

  let radialLineId = 0;
  /* Label: props as the Label component receives them. Returns an element or null. */
  function Label(rawProps, ctx) {
    const { h, txt, Text, svgProps, isNil, A, polarToCartesian, mathSign } = I();
    const props = Object.assign({ angle: 0, offset: 5, position: 'middle', textBreakAll: false }, I().stripUndef(rawProps));
    const vb = props.viewBox;
    if (!vb || (isNil(props.value) && isNil(props.children) && !props.content)) return null;
    if (props.content) {
      const f = fn(props.content, ctx);
      if (f) return f(Object.assign({}, props, { viewBox: vb }), ctx);
      return null;
    }
    let label = isNil(props.children) ? props.value : props.children;
    const formatter = fn(props.formatter, ctx);
    if (formatter) label = formatter(label);
    const attrs = svgProps(props);
    let pos;
    if (isPolarVB(vb)) {
      if (props.position === 'insideStart' || props.position === 'insideEnd' || props.position === 'end') {
        const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, clockWise } = vb;
        const radius = (innerRadius + outerRadius) / 2;
        const sign0 = mathSign(endAngle - startAngle);
        const deltaAngle = sign0 * Math.min(Math.abs(endAngle - startAngle), 360);
        const sign = deltaAngle >= 0 ? 1 : -1;
        let labelAngle, direction;
        if (props.position === 'insideStart') { labelAngle = startAngle + sign * props.offset; direction = clockWise; } else if (props.position === 'insideEnd') { labelAngle = endAngle - sign * props.offset; direction = !clockWise; } else { labelAngle = endAngle + sign * props.offset; direction = clockWise; }
        direction = deltaAngle <= 0 ? direction : !direction;
        const sp = polarToCartesian(cx, cy, radius, labelAngle);
        const ep = polarToCartesian(cx, cy, radius, labelAngle + (direction ? 1 : -1) * 359);
        const path = `M${sp.x},${sp.y}
    A${radius},${radius},0,1,${direction ? 0 : 1},
    ${ep.x},${ep.y}`;
        const id = isNil(props.id) ? `recharts-radial-line-${++radialLineId}` : props.id;
        const a = A(attrs);
        a['dominant-baseline'] = 'central';
        a.class = ['recharts-radial-bar-label', props.className].filter(Boolean).join(' ');
        delete a.classname;
        return h('text', a, [h('defs', {}, [h('path', { id, d: path })]), h('textPath', { 'xlink:href': '#' + id }, [txt(label)])]);
      }
      pos = polarLabelAttrs(vb, props.offset, props.position);
    } else {
      const parent = isPolarVB(props.parentViewBox) ? undefined : props.parentViewBox;
      const r = cartesianPosition(vb, props.position, props.offset, parent, true);
      pos = { x: r.x, y: r.y, textAnchor: r.horizontalAnchor, verticalAnchor: r.verticalAnchor };
      if (r.width !== undefined) pos.width = r.width;
      if (r.height !== undefined) pos.height = r.height;
    }
    const tp = Object.assign({ className: ['recharts-label', props.className || ''].join(' ').trim() }, attrs, pos);
    if (attrs.className) tp.className = attrs.className;
    const validAnchor = ['start', 'middle', 'end', 'inherit'].includes(attrs.textAnchor);
    tp.textAnchor = validAnchor ? attrs.textAnchor : pos.textAnchor;
    tp.breakAll = props.textBreakAll;
    // Text receives every svg prop of the label (x, y, width, height, offset, fontSize, fill ...)
    return Text(tp, label);
  }

  /* LabelList over entries ({x,y,width,height,value,payload,viewBox,parentViewBox,fill}). */
  function LabelList(listProps, entries, ctx) {
    const { h, isNil, svgProps, getValue } = I();
    if (!entries || !entries.length) return null;
    const lp = resolveProps(listProps, ctx);
    const { dataKey, valueAccessor } = lp;
    const others = Object.assign({}, lp);
    ['valueAccessor', 'dataKey', 'clockWise', 'id', 'textBreakAll', 'zIndex'].forEach((k) => delete others[k]);
    const kids = entries.map((entry, index) => {
      let value;
      if (isNil(dataKey)) {
        const v = Array.isArray(entry.value) ? entry.value[entry.value.length - 1] : entry.value;
        value = v === null || v === undefined || typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean' ? v : undefined;
      } else {
        value = getValue(entry.payload, dataKey);
      }
      return Label(Object.assign({}, svgProps(entry), others, {
        fill: lp.fill != null ? lp.fill : entry.fill,
        parentViewBox: entry.parentViewBox,
        value,
        textBreakAll: lp.textBreakAll,
        viewBox: entry.viewBox,
        index,
        zIndex: 0,
      }), ctx);
    });
    void valueAccessor;
    return h('g', { class: 'recharts-layer recharts-label-list' }, kids);
  }

  /* ---------------------------------------------------------------- cartesian */
  const X_DEFAULTS = { allowDataOverflow: false, allowDecimals: true, allowDuplicatedCategory: true, angle: 0, axisLine: true, height: 30, hide: false, includeHidden: false, interval: 'preserveEnd', label: false, minTickGap: 5, mirror: false, orientation: 'bottom', padding: { left: 0, right: 0 }, reversed: false, scale: 'auto', tick: true, tickCount: 5, tickLine: true, tickSize: 6, type: 'category', niceTicks: 'auto', stroke: '#666', tickMargin: 2 };
  const Y_DEFAULTS = Object.assign({}, X_DEFAULTS, { orientation: 'left', padding: { top: 0, bottom: 0 }, type: 'number', width: 60 });
  delete Y_DEFAULTS.height;
  const IMPLICIT_X = { allowDataOverflow: false, allowDecimals: true, allowDuplicatedCategory: true, height: 30, hide: true, orientation: 'bottom', padding: { left: 0, right: 0 }, reversed: false, scale: 'auto', tick: true, tickCount: 5, type: 'category', interval: 'preserveEnd', minTickGap: 5, angle: 0, implicit: true };
  const IMPLICIT_Y = { allowDataOverflow: false, allowDecimals: true, allowDuplicatedCategory: true, domain: [0, 'auto'], hide: true, orientation: 'left', padding: { top: 0, bottom: 0 }, reversed: false, scale: 'auto', tick: true, tickCount: 5, type: 'number', width: 60, interval: 'preserveEnd', minTickGap: 5, angle: 0, implicit: true };

  const SERIES_DEFAULTS = {
    Bar: { activeBar: false, background: false, hide: false, label: false, legendType: 'rect', minPointSize: 0, zIndex: Z.bar },
    Area: { activeDot: true, connectNulls: false, dot: false, fill: '#3182bd', fillOpacity: 0.6, hide: false, legendType: 'line', stroke: '#3182bd', strokeWidth: 1, type: 'linear', label: false, zIndex: Z.area },
    Line: { activeDot: true, connectNulls: false, dot: true, fill: '#fff', hide: false, label: false, legendType: 'line', stroke: '#3182bd', strokeWidth: 1, zIndex: Z.line, type: 'linear' },
    Pie: { cx: '50%', cy: '50%', dataKey: 'value', endAngle: 360, fill: '#808080', hide: false, innerRadius: 0, label: false, labelLine: true, legendType: 'rect', minAngle: 0, nameKey: 'name', outerRadius: '80%', paddingAngle: 0, rootTabIndex: 0, startAngle: 0, stroke: '#fff', zIndex: Z.area },
    Radar: { activeDot: true, dot: false, hide: false, label: false, legendType: 'rect', zIndex: Z.area },
    RadialBar: { background: false, cornerIsExternal: false, cornerRadius: 0, forceCornerRadius: false, hide: false, label: false, legendType: 'rect', minPointSize: 0, zIndex: Z.bar },
  };
  /* Props a series component consumes that are not passed on to its SVG elements. */
  const SERIES_META = new Set(['component', 'labelList', 'labels', 'children', 'cells', 'shape', 'activeShape', 'dot', 'activeDot', 'label', 'labelLine', 'background', 'stackId', 'dataKey', 'type', 'zIndex', 'hide', 'legendType', 'connectNulls', 'baseValue', 'minPointSize', 'maxBarSize', 'barSize', 'activeBar', 'nameKey', 'xAxisId', 'yAxisId', 'isAnimationActive', 'animationDuration', 'animationBegin', 'animationEasing']);

  function margins(props, polar) {
    const m = props.margin;
    if (m == null) return { top: 5, right: 5, bottom: 5, left: 5 };
    return { top: m.top || 0, right: m.right || 0, bottom: m.bottom || 0, left: m.left || 0 };
  }

  /* Legend payload as Recharts collects it from the graphical items, sorted by value. */
  function legendPayload(spec, items, ctx) {
    const { getValue, sortByKey } = I();
    let out = [];
    items.forEach((it) => {
      const p = it.props;
      if (it.component === 'Bar') out.push({ inactive: p.hide, dataKey: p.dataKey, type: p.legendType, color: p.fill, value: tooltipNameProp(p.name, p.dataKey), payload: p });
      else if (it.component === 'Area' || it.component === 'Line' || it.component === 'Radar') out.push({ inactive: p.hide, dataKey: p.dataKey, type: p.legendType, color: legendColor(p.stroke, p.fill), value: tooltipNameProp(p.name, p.dataKey), payload: p });
      else if (it.component === 'Pie') {
        it.data.forEach((entry, i) => {
          const name = getValue(entry, p.nameKey, p.name);
          const cell = it.cells && it.cells[i];
          const color = cell && cell.fill ? cell.fill : (entry && typeof entry === 'object' && 'fill' in entry ? entry.fill : p.fill);
          out.push({ value: tooltipNameProp(name, p.dataKey), color, payload: entry, type: p.legendType });
        });
      } else if (it.component === 'RadialBar') {
        ctx.data.forEach((entry) => out.push({ type: p.legendType, value: entry.name, color: entry.fill, payload: entry }));
      }
    });
    out = sortByKey(out, 'value');
    return out;
  }

  function buildCartesian(chart) {
    const L = I();
    const { h, isNum, getValue, range, Text, svgProps, A, Rectangle, Curve, Dot, Shape, getTicks, resolveAxis, bandSizeOfAxis, getPercentValue, round, isNil } = L;
    const spec = chart.spec, ctx = chart.ctx;
    const W = chart.width, H = chart.height;
    const props = resolveProps(spec.props, ctx);
    const chartName = spec.component;
    const layout = props.layout || 'horizontal';
    const margin = margins(props);
    const data = ctx.data;
    const stackOffset = props.stackOffset || 'none';
    const items = spec.series.map((s, idx) => {
      const p = Object.assign({}, SERIES_DEFAULTS[s.component], resolveProps(s, ctx));
      return { component: s.component, props: p, dataKey: p.dataKey, stackId: p.stackId == null ? undefined : String(p.stackId), id: `${s.component.toLowerCase()}-${idx}`, spec: s, index: idx };
    });
    const hasBar = items.some((i) => i.component === 'Bar');

    // axes
    const xs = spec.axes.filter((a) => a.component === 'XAxis').map((a) => Object.assign({ axisType: 'xAxis' }, X_DEFAULTS, resolveProps(a, ctx)));
    const ys = spec.axes.filter((a) => a.component === 'YAxis').map((a) => Object.assign({ axisType: 'yAxis' }, Y_DEFAULTS, resolveProps(a, ctx)));
    const xAxis = xs[0] || Object.assign({ axisType: 'xAxis' }, IMPLICIT_X);
    const yAxis = ys[0] || Object.assign({ axisType: 'yAxis' }, IMPLICIT_Y);
    [xAxis, yAxis].forEach((ax) => { ax.tickFormatterFn = fn(ax.tickFormatter, ctx); });

    // legend size (rendered before the offset is known, like Recharts' second pass)
    const legend = spec.legend ? buildLegendModel(spec, items, ctx, margin, W, H) : null;
    const legendBox = legend ? chart.measureLegend(legend) : null;

    // offset
    const off = { left: margin.left, right: margin.right, top: margin.top, bottom: margin.bottom };
    ys.forEach((y) => { if (!y.hide && !y.mirror) { if (y.orientation === 'left') off.left += isNum(y.width) ? y.width : 60; else if (y.orientation === 'right') off.right += isNum(y.width) ? y.width : 60; } });
    xs.forEach((x) => { if (!x.hide && !x.mirror) { if (x.orientation === 'top') off.top += x.height; else if (x.orientation === 'bottom') off.bottom += x.height; } });
    if (legend && legendBox) {
      const { layout: ll, align, verticalAlign } = legend.settings;
      if ((ll === 'vertical' || (ll === 'horizontal' && verticalAlign === 'middle')) && align !== 'center') off[align] += legendBox.width || 0;
      else if ((ll === 'horizontal' || (ll === 'vertical' && align === 'center')) && verticalAlign !== 'middle') off[verticalAlign] += legendBox.height || 0;
    }
    off.width = Math.max(W - off.left - off.right, 0);
    off.height = Math.max(H - off.top - off.bottom, 0);

    // stacks
    const numericAxisType = layout === 'horizontal' ? 'yAxis' : 'xAxis';
    const stacked = items.filter((i) => (i.component === 'Area' || i.component === 'Bar') && i.stackId != null && !i.props.hide);
    let stackGroups;
    if (stacked.length) {
      stackGroups = {};
      const byId = {};
      stacked.forEach((it) => { (byId[it.stackId] = byId[it.stackId] || []).push(it); });
      const rows = data.map((entry) => { const row = {}; stacked.forEach((it) => { row[it.id] = getValue(entry, it.dataKey, 0); }); return row; });
      for (const sid of Object.keys(byId)) {
        const keys = byId[sid].map((i) => i.id);
        const sd = NS.d3.stack(rows, keys, (d, key) => Number(getValue(d, key, 0)), stackOffset);
        stackGroups[sid] = { stackedData: sd, items: byId[sid] };
      }
    }
    const visibleItems = items.filter((i) => !i.props.hide);
    const axisCtx = { layout, data, items: visibleItems, stackGroups, stackOffset, chartName, hasBar };
    const padX = xAxis.padding || {}, padY = yAxis.padding || {};
    xAxis.range = [off.left + (padX.left || 0), off.left + off.width - (padX.right || 0)];
    yAxis.range = layout === 'horizontal' ? [off.top + off.height - (padY.bottom || 0), off.top + (padY.top || 0)] : [off.top + (padY.top || 0), off.top + off.height - (padY.bottom || 0)];
    resolveAxis(xAxis, Object.assign({}, axisCtx, { stackGroups: numericAxisType === 'xAxis' ? stackGroups : undefined }));
    resolveAxis(yAxis, Object.assign({}, axisCtx, { stackGroups: numericAxisType === 'yAxis' ? stackGroups : undefined }));
    const catAxis = layout === 'horizontal' ? xAxis : yAxis;
    const numAxis = layout === 'horizontal' ? yAxis : xAxis;

    const model = { kind: 'cartesian', layout, offset: off, width: W, height: H, chartName, xAxis, yAxis, catAxis, numAxis, items, legend, legendBox, margin, data };

    // bars: positions
    const bars = visibleItems.filter((i) => i.component === 'Bar');
    let barPositions;
    if (bars.length) {
      const totalSize = layout === 'horizontal' ? off.width : off.height;
      const getBarSize = (self) => { const s = self != null ? self : props.barSize; return isNil(s) ? undefined : getPercentValue(s, totalSize, 0); };
      const groups = {};
      bars.filter((b) => b.stackId != null).forEach((b) => { (groups[b.stackId] = groups[b.stackId] || []).push(b); });
      const sizeList = Object.keys(groups).map((sid) => ({ stackId: sid, dataKeys: groups[sid].map((b) => b.dataKey), barSize: getBarSize(groups[sid][0].props.barSize) }))
        .concat(bars.filter((b) => b.stackId == null).map((b) => ({ stackId: undefined, dataKeys: [b.dataKey].filter((k) => k != null), barSize: getBarSize(b.props.barSize) })));
      const bandSize = bandSizeOfAxis(catAxis, catAxis.itemTicks, true);
      const barBandSize = (bandSize != null ? bandSize : props.maxBarSize) || 0;
      barPositions = barPositionList(props.barGap != null ? props.barGap : 4, props.barCategoryGap != null ? props.barCategoryGap : '10%', barBandSize, sizeList, props.maxBarSize);
      model.barBandSize = barBandSize;
    }

    // per item geometry
    items.forEach((it) => {
      if (it.props.hide) return;
      if (it.component === 'Bar') it.rects = barRects(it, model, barPositions, stackGroups);
      else if (it.component === 'Area') Object.assign(it, areaPoints(it, model, stackGroups));
      else if (it.component === 'Line') it.points = linePoints(it, model);
    });

    // tooltip axis
    model.tooltipAxis = catAxis;
    model.tooltipTicks = catAxis.tooltipTicks;
    model.tooltipBandSize = bandSizeOfAxis(catAxis, catAxis.tooltipTicks, false);
    model.viewBox = { x: off.left, y: off.top, width: off.width, height: off.height };
    return model;
  }

  function barPositionList(barGap, barCategoryGap, bandSize, sizeList, maxBarSize) {
    const { getPercentValue, isWellBehaved } = I();
    const len = sizeList.length;
    if (len < 1) return undefined;
    let realBarGap = getPercentValue(barGap, bandSize, 0, true);
    if (isWellBehaved(sizeList[0].barSize)) {
      let useFull = false;
      let fullBarSize = bandSize / len;
      let sum = sizeList.reduce((r, e) => r + (e.barSize || 0), 0);
      sum += (len - 1) * realBarGap;
      if (sum >= bandSize) { sum -= (len - 1) * realBarGap; realBarGap = 0; }
      if (sum >= bandSize && fullBarSize > 0) { useFull = true; fullBarSize *= 0.9; sum = len * fullBarSize; }
      const offset = ((bandSize - sum) / 2) >> 0;
      let prev = { offset: offset - realBarGap, size: 0 };
      return sizeList.map((e) => {
        const pos = { offset: prev.offset + prev.size + realBarGap, size: useFull ? fullBarSize : (e.barSize || 0) };
        prev = pos;
        return { stackId: e.stackId, dataKeys: e.dataKeys, position: pos };
      });
    }
    const offset = getPercentValue(barCategoryGap, bandSize, 0, true);
    if (bandSize - 2 * offset - (len - 1) * realBarGap <= 0) realBarGap = 0;
    let originalSize = (bandSize - 2 * offset - (len - 1) * realBarGap) / len;
    if (originalSize > 1) originalSize >>= 0;
    const size = isWellBehaved(maxBarSize) ? Math.min(originalSize, maxBarSize) : originalSize;
    return sizeList.map((e, i) => ({ stackId: e.stackId, dataKeys: e.dataKeys, position: { offset: offset + (originalSize + realBarGap) * i + (originalSize - size) / 2, size } }));
  }

  function baseValueOfBar(numericAxis) {
    const domain = numericAxis.scale.domain();
    if (numericAxis.type === 'number') {
      const mn = Math.min(domain[0], domain[1]), mx = Math.max(domain[0], domain[1]);
      if (mn <= 0 && mx >= 0) return 0;
      if (mx < 0) return mx;
      return mn;
    }
    return domain[0];
  }
  function truncateByDomain(value, domain) {
    const { isNum } = I();
    if (!domain || domain.length !== 2 || !isNum(domain[0]) || !isNum(domain[1])) return value;
    const mn = Math.min(domain[0], domain[1]), mx = Math.max(domain[0], domain[1]);
    const r = [value[0], value[1]];
    if (!isNum(value[0]) || value[0] < mn) r[0] = mn;
    if (!isNum(value[1]) || value[1] > mx) r[1] = mx;
    if (r[0] > mx) r[0] = mx;
    if (r[1] < mn) r[1] = mn;
    return r;
  }
  function stackedOf(it, stackGroups) {
    if (!stackGroups || it.stackId == null || !stackGroups[it.stackId]) return undefined;
    return stackGroups[it.stackId].stackedData.find((sd) => sd.key === it.id);
  }

  function barRects(it, m, positions, stackGroups) {
    const { getValue, isNum, isNil, mathSign } = I();
    const pos = positions && positions.find((p) => p.stackId === it.stackId && it.dataKey != null && p.dataKeys.includes(it.dataKey));
    if (!pos) return [];
    const position = pos.position;
    const { layout, xAxis, yAxis, offset } = m;
    const numericAxis = layout === 'horizontal' ? yAxis : xAxis;
    const stackedData = stackedOf(it, stackGroups);
    const stackedDomain = stackedData ? numericAxis.scale.domain() : null;
    const baseValue = baseValueOfBar(numericAxis);
    const stackedBarStart = numericAxis.scale(baseValue);
    const cells = it.spec.cells;
    const hasCustomShape = it.props.shape != null;
    const parentViewBox = { x: 0, y: 0, width: m.width, height: m.height };
    const cateCoord = (axis, ticks, entry, index) => {
      if (axis.type === 'category') return ticks[index] ? ticks[index].coordinate + position.offset : null;
      const value = getValue(entry, axis.dataKey, axis.scale.domain()[index]);
      if (isNil(value)) return null;
      const sc = axis.scale(value);
      return isNum(sc) ? sc - m.barBandSize / 2 + position.offset : null;
    };
    return m.data.map((entry, index) => {
      let value, x, y, width, height, background;
      if (stackedData) {
        const u = stackedData[index];
        if (u == null) return null;
        value = truncateByDomain([u[0], u[1]], stackedDomain);
      } else {
        value = getValue(entry, it.dataKey);
        if (!Array.isArray(value)) value = [baseValue, value];
      }
      const minPointSize = isNum(it.props.minPointSize) ? it.props.minPointSize : 0;
      if (layout === 'horizontal') {
        const b = yAxis.scale(value[0]), c = yAxis.scale(value[1]);
        if (b == null || c == null) return null;
        x = cateCoord(xAxis, xAxis.itemTicks, entry, index);
        y = c != null ? c : b;
        width = position.size;
        const ch = b - c;
        height = Number.isNaN(ch) ? 0 : ch;
        background = { x, y: offset.top, width, height: offset.height };
        if (Math.abs(minPointSize) > 0 && Math.abs(height) < Math.abs(minPointSize)) { const delta = mathSign(height || minPointSize) * (Math.abs(minPointSize) - Math.abs(height)); y -= delta; height += delta; }
      } else {
        const b = xAxis.scale(value[0]), c = xAxis.scale(value[1]);
        if (b == null || c == null) return null;
        x = b;
        y = cateCoord(yAxis, yAxis.itemTicks, entry, index);
        width = c - b;
        height = position.size;
        background = { x: offset.left, y, width: offset.width, height };
        if (Math.abs(minPointSize) > 0 && Math.abs(width) < Math.abs(minPointSize)) width += mathSign(width || minPointSize) * (Math.abs(minPointSize) - Math.abs(width));
      }
      if (x == null || y == null || width == null || height == null || (!hasCustomShape && (width === 0 || height === 0))) return null;
      return Object.assign({}, entry, { stackedBarStart, x, y, width, height, value: stackedData ? value : value[1], payload: entry, background, tooltipPosition: { x: x + width / 2, y: y + height / 2 }, parentViewBox, originalDataIndex: index }, cells && cells[index] ? resolveProps(cells[index], m) : {});
    }).filter(Boolean);
  }

  function cateCoordOfLine(axis, ticks, bandSize, entry, index, dataKey) {
    const { isNil, getValue, isNum } = I();
    if (axis.type === 'category') {
      if (!axis.allowDuplicatedCategory && axis.dataKey && !isNil(entry[axis.dataKey])) {
        const t = ticks.find((tk) => tk.value === entry[axis.dataKey]);
        if (t) return t.coordinate + bandSize / 2;
      }
      return ticks[index] ? ticks[index].coordinate + bandSize / 2 : null;
    }
    const value = getValue(entry, !isNil(dataKey) ? dataKey : axis.dataKey);
    const sc = axis.scale(value);
    return isNum(sc) ? sc : null;
  }

  function areaPoints(it, m, stackGroups) {
    const { getValue, isNum } = I();
    const { layout, xAxis, yAxis } = m;
    const stackedData = stackedOf(it, stackGroups);
    const hasStack = stackedData && stackedData.length;
    const numericAxis = layout === 'horizontal' ? yAxis : xAxis;
    const domain = numericAxis.scale.domain();
    let baseValue = it.props.baseValue;
    if (!isNum(baseValue)) {
      if (numericAxis.type === 'number') {
        const mx = Math.max(domain[0], domain[1]), mn = Math.min(domain[0], domain[1]);
        baseValue = baseValue === 'dataMin' ? mn : baseValue === 'dataMax' ? mx : (mx < 0 ? mx : Math.max(mn, 0));
      } else baseValue = baseValue === 'dataMax' ? domain[1] : domain[0];
    }
    const catAxis = layout === 'horizontal' ? xAxis : yAxis;
    const bandSize = I().bandSizeOfAxis(catAxis, catAxis.itemTicks, false);
    let isRange = false;
    const points = m.data.map((entry, index) => {
      let va;
      if (hasStack) va = [stackedData[index][0], stackedData[index][1]];
      else { const raw = getValue(entry, it.dataKey); if (!Array.isArray(raw)) va = [baseValue, raw]; else { va = raw; isRange = true; } }
      const v1 = va && va[1] != null ? va[1] : null;
      const isBreak = v1 == null || (hasStack && !it.props.connectNulls && getValue(entry, it.dataKey) == null);
      if (layout === 'horizontal') {
        const yv = isBreak ? null : yAxis.scale(v1);
        return { x: cateCoordOfLine(xAxis, xAxis.itemTicks, bandSize, entry, index), y: yv == null ? null : yv, value: va, payload: entry };
      }
      const xv = isBreak ? null : xAxis.scale(v1);
      return { x: xv == null ? null : xv, y: cateCoordOfLine(yAxis, yAxis.itemTicks, bandSize, entry, index), value: va, payload: entry };
    });
    let baseLine;
    if (hasStack || isRange) {
      baseLine = points.map((e) => {
        const x = Array.isArray(e.value) ? e.value[0] : null;
        if (layout === 'horizontal') return { x: e.x, y: x != null && e.y != null ? yAxis.scale(x) : null, payload: e.payload };
        return { x: x != null ? xAxis.scale(x) : null, y: e.y, payload: e.payload };
      });
    } else {
      baseLine = layout === 'horizontal' ? yAxis.scale(baseValue) : xAxis.scale(baseValue);
    }
    return { points, baseLine: baseLine == null ? 0 : baseLine, isRange };
  }

  function linePoints(it, m) {
    const { getValue, isNil } = I();
    const { layout, xAxis, yAxis } = m;
    const catAxis = layout === 'horizontal' ? xAxis : yAxis;
    const bandSize = I().bandSizeOfAxis(catAxis, catAxis.itemTicks, false);
    return m.data.map((entry, index) => {
      const value = getValue(entry, it.dataKey);
      if (layout === 'horizontal') {
        const x = cateCoordOfLine(xAxis, xAxis.itemTicks, bandSize, entry, index);
        const y = isNil(value) ? null : yAxis.scale(value);
        return { x, y: y == null ? null : y, value, payload: entry };
      }
      const x = isNil(value) ? null : xAxis.scale(value);
      const y = cateCoordOfLine(yAxis, yAxis.itemTicks, bandSize, entry, index);
      if (x == null || y == null) return null;
      return { x, y, value, payload: entry };
    }).filter(Boolean);
  }

  /* ---------------------------------------------------------------- rendering: cartesian */
  function renderCartesian(chart, m, active) {
    const L = I();
    const { h, Text, svgProps, A, Rectangle, Curve, Dot, Shape, getTicks, isNum } = L;
    const spec = chart.spec, ctx = chart.ctx;
    const layers = newLayers();
    const z0 = [];
    const { offset: off, layout } = m;
    const labelsLater = [];

    // grid
    if (spec.grid) layers[Z.grid].push(renderCartesianGrid(chart, m));

    // series
    m.items.forEach((it) => {
      if (it.props.hide) return;
      if (it.component === 'Bar') renderBar(chart, m, it, layers, labelsLater, active);
      else if (it.component === 'Area') renderArea(chart, m, it, layers, labelsLater, active);
      else if (it.component === 'Line') renderLine(chart, m, it, layers, labelsLater, active);
    });

    // axes, in spec order
    spec.axes.forEach((raw, i) => {
      const axis = raw.component === 'XAxis' ? m.xAxis : m.yAxis;
      if (axis.implicit || axis.hide) return;
      renderCartesianAxis(chart, m, axis, layers);
    });

    // cursor
    if (active && active.cursor) {
      const cur = spec.tooltip && spec.tooltip.cursor;
      if (cur !== false && cur !== undefined || (spec.tooltip && !('cursor' in spec.tooltip))) {
        renderCursor(chart, m, active, layers);
      }
    }

    labelsLater.forEach((l) => layers[Z.label].push(l));
    return { layers, z0 };
  }

  function newLayers() { const o = {}; Z_LAYERS.forEach((z) => { o[z] = []; }); return o; }

  function renderCartesianGrid(chart, m) {
    const L = I();
    const { h, svgProps, A, getTicks } = L;
    const g = Object.assign({ horizontal: true, vertical: true, stroke: '#ccc', fill: 'none', verticalFill: [], horizontalFill: [], syncWithTicks: false }, resolveProps(chart.spec.grid, chart.ctx));
    const off = m.offset;
    const x = off.left, y = off.top, width = off.width, height = off.height;
    if (!(width > 0) || !(height > 0)) return null;
    const gridTicks = (axis, sizeKeyOrientation) => {
      if (!axis || !axis.scale) return [];
      return getTicks({ tick: axis.tick === undefined ? true : axis.tick, ticks: axis.ticks_, viewBox: { x: 0, y: 0, width: m.width, height: m.height }, minTickGap: axis.minTickGap === undefined ? 5 : axis.minTickGap, orientation: axis.orientation || sizeKeyOrientation, interval: axis.interval === undefined ? 'preserveEnd' : axis.interval, tickFormatter: axis.tickFormatterFn, unit: axis.unit, angle: axis.angle }, undefined, undefined);
    };
    const coordsOf = (ticks, min, max) => {
      if (g.syncWithTicks) return ticks.map((t) => t.coordinate);
      let hasMin = false, hasMax = false;
      const vals = ticks.map((t) => { if (t.coordinate === min) hasMin = true; if (t.coordinate === max) hasMax = true; return t.coordinate; });
      if (!hasMin) vals.push(min);
      if (!hasMax) vals.push(max);
      return vals;
    };
    const lineProps = svgProps(g);
    delete lineProps.className;
    const kids = [];
    if (g.fill && g.fill !== 'none') kids.push(h('rect', { x, y, ry: g.ry, width, height, stroke: 'none', fill: g.fill, 'fill-opacity': g.fillOpacity, class: 'recharts-cartesian-grid-bg' }));
    const hp = g.horizontal ? coordsOf(gridTicks(m.yAxis, 'left'), off.top, off.top + off.height) : [];
    const vp = g.vertical ? coordsOf(gridTicks(m.xAxis, 'bottom'), off.left, off.left + off.width) : [];
    const base = Object.assign({}, lineProps, { x, y, width, height });
    if (g.horizontal && hp.length) {
      kids.push(h('g', { class: 'recharts-cartesian-grid-horizontal' }, hp.map((e) => h('line', Object.assign(A(base), { x1: x, y1: e, x2: x + width, y2: e, fill: 'none' })))));
    }
    if (g.vertical && vp.length) {
      kids.push(h('g', { class: 'recharts-cartesian-grid-vertical' }, vp.map((e) => h('line', Object.assign(A(base), { x1: e, y1: y, x2: e, y2: y + height, fill: 'none' })))));
    }
    return h('g', { class: 'recharts-cartesian-grid' }, kids);
  }

  function tickLineCoord(entry, x, y, width, height, orientation, tickSize, mirror, tickMargin) {
    const sign = mirror ? -1 : 1;
    const ts = entry.tickSize || tickSize;
    const tc = I().isNum(entry.tickCoord) ? entry.tickCoord : entry.coordinate;
    let x1, x2, y1, y2, tx, ty;
    switch (orientation) {
      case 'top': x1 = x2 = entry.coordinate; y2 = y + +!mirror * height; y1 = y2 - sign * ts; ty = y1 - sign * tickMargin; tx = tc; break;
      case 'left': y1 = y2 = entry.coordinate; x2 = x + +!mirror * width; x1 = x2 - sign * ts; tx = x1 - sign * tickMargin; ty = tc; break;
      case 'right': y1 = y2 = entry.coordinate; x2 = x + +mirror * width; x1 = x2 + sign * ts; tx = x1 + sign * tickMargin; ty = tc; break;
      default: x1 = x2 = entry.coordinate; y2 = y + +mirror * height; y1 = y2 + sign * ts; ty = y1 + sign * tickMargin; tx = tc; break;
    }
    return { line: { x1, y1, x2, y2 }, tick: { x: tx, y: ty } };
  }

  function renderCartesianAxis(chart, m, axis, layers) {
    const L = I();
    const { h, Text, svgProps, A } = L;
    const off = m.offset;
    const isX = axis.axisType === 'xAxis';
    let x, y, width, height;
    if (isX) { x = off.left; width = off.width; height = axis.height; y = axis.orientation === 'top' ? off.top - height : m.height - off.bottom; if (axis.orientation === 'top' && axis.mirror) y = off.top; if (axis.orientation === 'bottom' && axis.mirror) y = m.height - off.bottom; } else { y = off.top; height = off.height; width = typeof axis.width === 'number' ? axis.width : 60; x = axis.orientation === 'left' ? off.left - (axis.mirror ? 0 : width) : m.width - off.right - (axis.mirror ? width : 0); }
    if ((width != null && width <= 0) || (height != null && height <= 0)) return;
    const typeName = axis.axisType;
    const fontSize = chart.axisFontSize();
    const finalTicks = L.getTicks({ tick: axis.tick, ticks: axis.ticks_, viewBox: { x: 0, y: 0, width: m.width, height: m.height }, minTickGap: axis.minTickGap, orientation: axis.orientation, interval: axis.interval, tickFormatter: axis.tickFormatterFn, unit: axis.unit, angle: axis.angle }, fontSize.fontSize, fontSize.letterSpacing);
    // svg props of the axis component, as CartesianAxis spreads them on lines and labels
    const axisProps = svgProps(Object.assign({}, axis, { x, y, width, height }));
    delete axisProps.className; delete axisProps.ticks;
    const anchor = { left: axis.mirror ? 'start' : 'end', right: axis.mirror ? 'end' : 'start' }[axis.orientation] || 'middle';
    const vAnchor = axis.orientation === 'left' || axis.orientation === 'right' ? 'middle' : axis.orientation === 'top' ? (axis.mirror ? 'start' : 'end') : (axis.mirror ? 'end' : 'start');
    const textAnchor = ['start', 'middle', 'end', 'inherit'].includes(axisProps.textAnchor) ? axisProps.textAnchor : anchor;
    const coords = finalTicks.map((entry) => Object.assign({ entry }, tickLineCoord(entry, x, y, width, height, axis.orientation, axis.tickSize, axis.mirror, axis.tickMargin)));
    const tickLineObj = typeof axis.tickLine === 'object' && axis.tickLine ? axis.tickLine : {};
    const tickLines = coords.map(({ line }) => h('g', { class: 'recharts-layer recharts-cartesian-axis-tick' }, [
      axis.tickLine ? h('line', Object.assign(A(Object.assign({}, axisProps, { fill: 'none' }, svgProps(tickLineObj))), line, { class: ['recharts-cartesian-axis-tick-line', tickLineObj.className].filter(Boolean).join(' ') })) : null,
    ]));
    const customTick = axis.tick && typeof axis.tick === 'object' && !axis.tick.$fn ? svgProps(axis.tick) : {};
    const labels = coords.map(({ entry, tick }, i) => {
      const tp = Object.assign({ verticalAnchor: vAnchor }, axisProps, { textAnchor, stroke: 'none', fill: axis.stroke }, tick, { index: i, payload: entry, visibleTicksCount: finalTicks.length }, { angle: axisProps.angle != null ? axisProps.angle : 0 }, customTick);
      const value = `${axis.tickFormatterFn ? axis.tickFormatterFn(entry.value, i) : entry.value}${axis.unit || ''}`;
      let el = null;
      if (axis.tick) {
        if (axis.tick && axis.tick.$fn) el = fn(axis.tick, chart.ctx)(Object.assign({}, tp, { className: 'recharts-cartesian-axis-tick-value' }), chart.ctx);
        else el = Text(Object.assign({}, tp, { className: ['recharts-cartesian-axis-tick-value', typeof axis.tick === 'object' ? axis.tick.className : ''].filter(Boolean).join(' ') }), value);
      }
      return h('g', { class: 'recharts-layer recharts-cartesian-axis-tick-label' }, [el]);
    });
    if (labels.length) layers[Z.label].push(h('g', { class: `recharts-cartesian-axis-tick-labels recharts-${typeName}-tick-labels` }, labels));
    const axisLine = axis.axisLine ? (() => {
      const lp = Object.assign({}, svgProps(Object.assign({}, axis, { x, y, width, height })), svgProps(typeof axis.axisLine === 'object' ? axis.axisLine : {}), { fill: 'none' });
      delete lp.className;
      let c;
      if (axis.orientation === 'top' || axis.orientation === 'bottom') { const need = +((axis.orientation === 'top' && !axis.mirror) || (axis.orientation === 'bottom' && axis.mirror)); c = { x1: x, y1: y + need * height, x2: x + width, y2: y + need * height }; } else { const need = +((axis.orientation === 'left' && !axis.mirror) || (axis.orientation === 'right' && axis.mirror)); c = { x1: x + need * width, y1: y, x2: x + need * width, y2: y + height }; }
      return h('line', Object.assign(A(lp), c, { class: 'recharts-cartesian-axis-line' }));
    })() : null;
    layers[Z.axis].push(h('g', { class: `recharts-layer recharts-cartesian-axis recharts-${typeName} ${typeName}` }, [
      axisLine,
      h('g', { class: `recharts-cartesian-axis-ticks recharts-${typeName}-ticks` }, [
        tickLines.length ? h('g', { class: `recharts-cartesian-axis-tick-lines recharts-${typeName}-tick-lines` }, tickLines) : null,
      ]),
    ]));
  }

  function seriesSvgProps(it) {
    const p = {};
    for (const k of Object.keys(it.props)) if (!SERIES_META.has(k)) p[k] = it.props[k];
    return p;
  }

  function renderBar(chart, m, it, layers, labelsLater, active) {
    const L = I();
    const { h, svgProps, Shape } = L;
    const p = it.props;
    const base = svgProps(seriesSvgProps(it));
    delete base.id;
    if (!('name' in base)) base.name = String(p.name);
    const rects = it.rects || [];
    if (p.background) {
      const bgProps = typeof p.background === 'object' ? svgProps(p.background) : {};
      layers[Z.barBackground].push(h('g', { class: 'recharts-layer' }, rects.map((entry, i) => {
        if (!entry.background) return null;
        const rest = Object.assign({}, entry); delete rest.value; delete rest.background; delete rest.tooltipPosition;
        const bp = Object.assign({}, rest, { fill: '#eee' }, entry.background, bgProps, { className: 'recharts-bar-background-rectangle' });
        return Shape('rectangle', p.background, Object.assign({}, svgProps(bp), { className: bp.className, isActive: false }), chart.ctx, { active: 'recharts-active-bar', inactive: 'recharts-inactive-bar' });
      })));
    }
    const rectEls = rects.map((entry, i) => {
      const props = Object.assign({}, base, svgProps(entry), { x: entry.x, y: entry.y, width: entry.width, height: entry.height, index: i, payload: entry.payload, isActive: false });
      if (p.radius !== undefined) props.radius = p.radius;
      const option = p.shape;
      const shape = option ? Shape('rectangle', option, Object.assign({}, props, { payload: entry.payload, fill: props.fill, index: i }), chart.ctx, { active: 'recharts-active-bar', inactive: 'recharts-inactive-bar' })
        : Shape('rectangle', null, props, chart.ctx, { active: 'recharts-active-bar', inactive: 'recharts-inactive-bar' });
      return h('g', { class: 'recharts-layer recharts-bar-rectangle' }, [shape]);
    });
    layers[Z.bar].push(h('g', { class: 'recharts-layer recharts-bar', id: `recharts-bar-${chart.uid}-${it.index}` }, [
      h('g', { class: 'recharts-layer recharts-bar-rectangles' }, [h('g', { class: 'recharts-layer' }, rectEls)]),
    ]));
    const entries = rects.map((e) => {
      const vb = { x: e.x, y: e.y, width: e.width, lowerWidth: e.width, upperWidth: e.width, height: e.height };
      return Object.assign({}, vb, { value: e.value, payload: e.payload, parentViewBox: e.parentViewBox, viewBox: vb, fill: e.fill });
    });
    (it.spec.labelList || []).forEach((ll) => labelsLater.push(LabelList(ll, entries, chart.ctx)));
    if (p.label) labelsLater.push(LabelList(p.label === true ? {} : p.label, entries, chart.ctx));
  }

  function activePointLayer(chart, it, points, mainColor, active, layers) {
    const L = I();
    const { h, svgProps, Dot } = L;
    if (!active || !active.payloads || it.props.activeDot === false) return;
    const pt = points.find((q) => q && active.payloads.includes(q.payload));
    if (!pt || pt.x == null || pt.y == null) return;
    const ad = it.props.activeDot;
    const props = Object.assign({ index: active.index, dataKey: it.dataKey, cx: pt.x, cy: pt.y, r: 4, fill: mainColor != null ? mainColor : 'none', strokeWidth: 2, stroke: '#fff', payload: pt.payload, value: pt.value }, typeof ad === 'object' ? svgProps(ad) : {});
    layers[Z.activeDot].push(h('g', { class: 'recharts-layer recharts-active-dot' }, [Dot(props)]));
  }

  function dotsLayer(chart, it, points, cls, dotCls, baseProps, layers) {
    const L = I();
    const { h, svgProps, Dot } = L;
    const dot = it.props.dot;
    if (!points || !(dot || points.length === 1)) return;
    const custom = dot && typeof dot === 'object' && !dot.$fn ? svgProps(dot) : {};
    const dots = points.map((entry, i) => {
      const dp = Object.assign({ r: 3 }, baseProps, custom, { index: i, cx: entry.x == null ? undefined : entry.x, cy: entry.y == null ? undefined : entry.y, dataKey: it.dataKey, value: entry.value, payload: entry.payload });
      if (dot && dot.$fn) return fn(dot, chart.ctx)(dp, chart.ctx);
      return Dot(Object.assign({}, dp, { className: [dotCls, dot && typeof dot === 'object' ? dot.className : ''].filter(Boolean).join(' ') }));
    });
    layers[Z.scatter].push(h('g', { class: ['recharts-layer', cls].join(' ') }, dots));
  }

  function renderArea(chart, m, it, layers, labelsLater, active) {
    const L = I();
    const { h, svgProps, Curve } = L;
    const p = it.props;
    const points = it.points || [];
    if (!points.length) return;
    const geom = { height: m.offset.height, width: m.offset.width };
    const props = Object.assign(seriesSvgProps(it), geom);
    const all = svgProps(props);
    delete all.id;
    const kids = [];
    if (points.length > 1) {
      kids.push(h('g', { class: 'recharts-layer' }, [
        Curve(Object.assign({}, all, { id: `recharts-area-${chart.uid}-${it.index}`, points, connectNulls: p.connectNulls, type: p.type, baseLine: it.baseLine, layout: m.layout, stroke: 'none', className: 'recharts-area-area' })),
        p.stroke !== 'none' ? Curve(Object.assign({}, all, { className: 'recharts-area-curve', layout: m.layout, type: p.type, connectNulls: p.connectNulls, fill: 'none', points })) : null,
        p.stroke !== 'none' && it.isRange && Array.isArray(it.baseLine) ? Curve(Object.assign({}, all, { className: 'recharts-area-curve', layout: m.layout, type: p.type, connectNulls: p.connectNulls, fill: 'none', points: it.baseLine })) : null,
      ]));
    }
    layers[Z.area].push(h('g', { class: 'recharts-layer recharts-area' }, kids));
    dotsLayer(chart, it, points, 'recharts-area-dots', 'recharts-area-dot', all, layers);
    activePointLayer(chart, it, points, legendColor(p.stroke, p.fill), active, layers);
    const entries = points.map((pt) => { const vb = { x: pt.x == null ? 0 : pt.x, y: pt.y == null ? 0 : pt.y, width: 0, lowerWidth: 0, upperWidth: 0, height: 0 }; return Object.assign({}, vb, { value: pt.value, payload: pt.payload, parentViewBox: undefined, viewBox: vb, fill: undefined }); });
    (it.spec.labelList || []).forEach((ll) => labelsLater.push(LabelList(ll, entries, chart.ctx)));
  }

  function renderLine(chart, m, it, layers, labelsLater, active) {
    const L = I();
    const { h, svgProps, Curve, Shape } = L;
    const p = it.props;
    const points = it.points || [];
    const geom = { height: m.offset.height, width: m.offset.width };
    const others = Object.assign(seriesSvgProps(it), geom);
    const lineProps = svgProps(others);
    const kids = [];
    if (points.length > 1) {
      const curveProps = Object.assign({}, lineProps, { fill: 'none', className: 'recharts-line-curve', id: `recharts-line-${chart.uid}-${it.index}`, points, type: p.type, layout: m.layout, connectNulls: p.connectNulls });
      const d = L.curvePath(p.type, points, undefined, m.layout, p.connectNulls);
      const len = chart.pathLength(d);
      curveProps.strokeDasharray = p.strokeDasharray != null ? String(p.strokeDasharray) : `${len}px ${len}px`;
      kids.push(Shape('curve', null, curveProps, chart.ctx));
    }
    layers[Z.line].push(h('g', { class: 'recharts-layer recharts-line' }, kids));
    const dotBase = Object.assign({}, lineProps);
    delete dotBase.id;
    dotsLayer(chart, it, points, 'recharts-line-dots', 'recharts-line-dot', dotBase, layers);
    activePointLayer(chart, it, points, p.stroke, active, layers);
    const entries = points.map((pt) => { const vb = { x: pt.x == null ? 0 : pt.x, y: pt.y == null ? 0 : pt.y, width: 0, lowerWidth: 0, upperWidth: 0, height: 0 }; return Object.assign({}, vb, { value: pt.value, payload: pt.payload, viewBox: vb, parentViewBox: undefined, fill: undefined }); });
    (it.spec.labelList || []).forEach((ll) => labelsLater.push(LabelList(ll, entries, chart.ctx)));
  }

  function renderCursor(chart, m, active, layers) {
    const L = I();
    const { svgProps, Rectangle, Curve, polarToCartesian } = L;
    const cursor = chart.spec.tooltip.cursor;
    const extra = typeof cursor === 'object' && cursor ? svgProps(cursor) : {};
    const off = m.offset;
    const coord = active.coordinate;
    const base = { stroke: '#ccc', pointerEvents: 'none', width: off.width, height: off.height };
    if (m.chartName === 'BarChart') {
      const half = m.tooltipBandSize / 2;
      const r = { stroke: 'none', fill: '#ccc', x: m.layout === 'horizontal' ? coord.x - half : off.left + 0.5, y: m.layout === 'horizontal' ? off.top + 0.5 : coord.y - half, width: m.layout === 'horizontal' ? m.tooltipBandSize : off.width - 1, height: m.layout === 'horizontal' ? off.height - 1 : m.tooltipBandSize };
      layers[Z.cursorRectangle].push(Rectangle(Object.assign({}, base, r, extra, { className: ['recharts-tooltip-cursor', cursor && cursor.className].filter(Boolean).join(' ') })));
      return;
    }
    let points;
    if (m.layout === 'horizontal') points = [{ x: coord.x, y: off.top }, { x: coord.x, y: off.top + off.height }];
    else if (m.layout === 'vertical') points = [{ x: off.left, y: coord.y }, { x: off.left + off.width, y: coord.y }];
    else if (m.layout === 'centric') { const a = polarToCartesian(coord.cx, coord.cy, coord.innerRadius, coord.angle), b = polarToCartesian(coord.cx, coord.cy, coord.outerRadius, coord.angle); points = [a, b]; }
    if (!points) return;
    layers[Z.cursorLine].push(Curve(Object.assign({}, base, { points }, extra, { className: ['recharts-tooltip-cursor', cursor && cursor.className].filter(Boolean).join(' ') })));
  }

  /* ---------------------------------------------------------------- legend model */
  function buildLegendModel(spec, items, ctx, margin, W, H) {
    const lg = Object.assign({ align: 'center', iconSize: 14, inactiveColor: '#ccc', itemSorter: 'value', layout: 'horizontal', verticalAlign: 'bottom' }, resolveProps(spec.legend, ctx));
    const payload = legendPayload(spec, items, ctx);
    const maxWidth = W - (margin.left || 0) - (margin.right || 0);
    const style = { position: 'absolute', width: (lg.layout === 'horizontal' ? (lg.width || maxWidth) : lg.width) || 'auto', height: lg.height || 'auto' };
    if (lg.layout === 'horizontal' || lg.width) style.width = (lg.width || maxWidth) + 'px';
    if (style.height !== 'auto') style.height += 'px';
    const pos = {};
    if (lg.align === 'center' && lg.layout === 'vertical') pos.left = 'calc'; else if (lg.align === 'right') pos.right = (margin.right || 0) + 'px'; else pos.left = (margin.left || 0) + 'px';
    if (lg.verticalAlign === 'middle') pos.top = 'calc'; else if (lg.verticalAlign === 'bottom') pos.bottom = (margin.bottom || 0) + 'px'; else pos.top = (margin.top || 0) + 'px';
    return { settings: { layout: lg.layout, align: lg.align, verticalAlign: lg.verticalAlign }, props: lg, payload, style: Object.assign(style, pos) };
  }

  /* ---------------------------------------------------------------- tooltip */
  function calculateActiveTickIndex(coordinate, ticks, unsortedTicks, axisType, rangeV) {
    const { mathSign } = I();
    const len = ticks ? ticks.length : 0;
    if (len <= 1 || coordinate == null) return 0;
    if (axisType === 'angleAxis' && rangeV != null && Math.abs(Math.abs(rangeV[1] - rangeV[0]) - 360) <= 1e-6) {
      for (let i = 0; i < len; i++) {
        const before = i > 0 ? unsortedTicks[i - 1].coordinate : unsortedTicks[len - 1].coordinate;
        const cur = unsortedTicks[i].coordinate;
        const after = i >= len - 1 ? unsortedTicks[0].coordinate : unsortedTicks[i + 1].coordinate;
        let same;
        if (mathSign(cur - before) !== mathSign(after - cur)) {
          const diff = [];
          if (mathSign(after - cur) === mathSign(rangeV[1] - rangeV[0])) {
            same = after;
            const curInRange = cur + rangeV[1] - rangeV[0];
            diff[0] = Math.min(curInRange, (curInRange + before) / 2);
            diff[1] = Math.max(curInRange, (curInRange + before) / 2);
          } else {
            same = before;
            const afterInRange = after + rangeV[1] - rangeV[0];
            diff[0] = Math.min(cur, (afterInRange + cur) / 2);
            diff[1] = Math.max(cur, (afterInRange + cur) / 2);
          }
          const sameInterval = [Math.min(cur, (same + cur) / 2), Math.max(cur, (same + cur) / 2)];
          if ((coordinate > sameInterval[0] && coordinate <= sameInterval[1]) || (coordinate >= diff[0] && coordinate <= diff[1])) return unsortedTicks[i].index;
        } else {
          const mn = Math.min(before, after), mx = Math.max(before, after);
          if (coordinate > (mn + cur) / 2 && coordinate <= (mx + cur) / 2) return unsortedTicks[i].index;
        }
      }
    } else if (ticks) {
      for (let i = 0; i < len; i++) {
        const curr = ticks[i], next = ticks[i + 1], prev = ticks[i - 1];
        if (i === 0 && next != null && coordinate <= (curr.coordinate + next.coordinate) / 2) return curr.index;
        if (i === len - 1 && prev != null && coordinate > (curr.coordinate + prev.coordinate) / 2) return curr.index;
        if (i > 0 && i < len - 1 && prev != null && next != null && coordinate > (curr.coordinate + prev.coordinate) / 2 && coordinate <= (curr.coordinate + next.coordinate) / 2) return curr.index;
      }
    }
    return -1;
  }

  NS.surface = {
    Z, Z_LAYERS, fn, resolveProps, stateValue, tooltipNameProp, legendColor, cartesianPosition, Label, LabelList,
    buildCartesian, renderCartesian, newLayers, calculateActiveTickIndex, buildLegendModel, legendPayload,
    dotsLayer, activePointLayer, seriesSvgProps, SERIES_DEFAULTS, margins, baseValueOfBar, truncateByDomain,
    barPositionList, isPolarVB,
  };
})();
