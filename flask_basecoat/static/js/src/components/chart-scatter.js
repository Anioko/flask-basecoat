/* ScatterChart: a port of Recharts 3.8's Scatter (cartesian/Scatter.tsx, util/ScatterUtils.tsx, shape/Symbols.tsx)
   and ZAxis (cartesian/ZAxis.tsx). Both axes are number axes of the chart; a ZAxis is a virtual axis that maps a data
   value to the symbol's area. A spec draws it as

     "component": "ScatterChart",
     "series": [{"component": "Scatter", "fill": "var(--color-value)", "shape": "circle", "labelList": [...]}],
     "axes": [{"component": "XAxis", "type": "number", "dataKey": "cost", "name": "Cost"}, {... YAxis}, {"component": "ZAxis", "dataKey": "effort", "range": [60, 400], "name": "Effort"}]

   The tooltip of a scatter chart is an item tooltip: it lists the x value, the y value and the z value of the point under
   the pointer (Recharts' tooltipPayload), not the values of a category.

   Beyond Recharts (ruling R9, accessibility outranks the original): each point is a focusable image with a label that
   names it and gives its values; one point is in the tab order, the arrow keys, Home and End move between points, and
   the tooltip follows the focus. */
(function () {
  'use strict';
  const NS = (window.FlaskBasecoatChart = window.FlaskBasecoatChart || {});

  function I() { return NS.internal; }

  const IMPLICIT_Z = { domain: [0, 'auto'], range: [64, 64], scale: 'auto', type: 'number', name: '', unit: '' };

  /* The ZAxis of the spec with its scale: domain [0, 'auto'] over the data, mapped onto `range` (the symbol area). */
  function zAxisOf(chart) {
    const { isNil, isNum, isWellBehaved, getValue, d3 } = Object.assign({}, I(), { d3: NS.d3 });
    const raw = chart.spec.axes.find((a) => a.component === 'ZAxis');
    if (!raw) return null;
    const z = Object.assign({}, IMPLICIT_Z, NS.surface.resolveProps(raw, chart.ctx));
    const values = chart.ctx.data.map((d) => (isNil(z.dataKey) ? undefined : getValue(d, z.dataKey))).filter((v) => isWellBehaved(Number(v)) && v !== null && v !== '');
    const nums = values.map(Number);
    const dataDomain = nums.length ? [Math.min(...nums), Math.max(...nums)] : undefined;
    let domain = dataDomain;
    if (dataDomain && Array.isArray(z.domain) && z.domain.length === 2) {
      const lo = z.domain[0] === 'auto' ? dataDomain[0] : isNum(z.domain[0]) ? z.domain[0] : dataDomain[0];
      const hi = z.domain[1] === 'auto' ? dataDomain[1] : isNum(z.domain[1]) ? z.domain[1] : dataDomain[1];
      domain = [Math.min(lo, dataDomain[0]), Math.max(hi, dataDomain[1])];
    }
    z.scale = domain ? d3.linear(domain, z.range) : null;
    return z;
  }

  /* computeScatterPoints */
  function points(chart, m, it, zAxis) {
    const { isNil, getValue, bandSizeOfAxis } = I();
    const { xAxis, yAxis } = m;
    const cells = it.spec.cells;
    const xKey = isNil(xAxis.dataKey) ? it.dataKey : xAxis.dataKey;
    const yKey = isNil(yAxis.dataKey) ? it.dataKey : yAxis.dataKey;
    const zKey = zAxis && zAxis.dataKey;
    const defaultZ = (zAxis ? zAxis.range : IMPLICIT_Z.range)[0];
    const xBand = xAxis.scale.bandwidth ? xAxis.scale.bandwidth() : 0;
    const yBand = yAxis.scale.bandwidth ? yAxis.scale.bandwidth() : 0;
    const entryOf = (axis, key) => ({ name: isNil(axis.dataKey) ? it.props.name : axis.name || String(axis.dataKey), unit: axis.unit || '', dataKey: key, type: it.props.tooltipType });
    return m.data.map((entry, index) => {
      const x = getValue(entry, xKey);
      const y = getValue(entry, yKey);
      const z = (!isNil(zKey) && getValue(entry, zKey)) || '-';
      const tooltipPayload = [Object.assign(entryOf(xAxis, xKey), { value: x, payload: entry }), Object.assign(entryOf(yAxis, yKey), { value: y, payload: entry })];
      if (z !== '-' && zAxis != null) tooltipPayload.push({ name: zAxis.name || zAxis.dataKey, unit: zAxis.unit || '', value: z, payload: entry, dataKey: zKey, type: it.props.tooltipType });
      const cx = cateCoord(xAxis, xAxis.itemTicks, xBand, entry, index, xKey);
      const cy = cateCoord(yAxis, yAxis.itemTicks, yBand, entry, index, yKey);
      const size = z !== '-' && zAxis != null && zAxis.scale ? zAxis.scale(z) : defaultZ;
      const radius = size == null ? 0 : Math.sqrt(Math.max(size, 0) / Math.PI);
      return Object.assign({}, entry, {
        cx, cy, x: cx == null ? undefined : cx - radius, y: cy == null ? undefined : cy - radius, width: 2 * radius, height: 2 * radius, size,
        node: { x, y, z }, tooltipPayload, tooltipPosition: { x: cx, y: cy }, payload: entry,
      }, cells && cells[index] ? NS.surface.resolveProps(cells[index], m) : {});
    });
  }

  /* getCateCoordinateOfLine, as the line chart's helper in chart-surface.js has it */
  function cateCoord(axis, ticks, bandSize, entry, index, dataKey) {
    const { isNil, getValue, isNum } = I();
    if (axis.type === 'category') {
      if (!axis.allowDuplicatedCategory && axis.dataKey && !isNil(entry[axis.dataKey])) {
        const t = ticks.find((tk) => tk.value === entry[axis.dataKey]);
        if (t) return t.coordinate + bandSize / 2;
      }
      return ticks[index] ? ticks[index].coordinate + bandSize / 2 : null;
    }
    const sc = axis.scale(getValue(entry, !isNil(dataKey) ? dataKey : axis.dataKey));
    return isNum(sc) ? sc : null;
  }

  /* The text a screen reader hears for one point: its name (the label list's data key) and every tooltip value. */
  function pointLabel(it, pt) {
    const key = ((it.spec.labelList || [])[0] || {}).dataKey;
    const name = key && pt.payload ? pt.payload[key] : null;
    const values = pt.tooltipPayload.map((e) => `${e.name} ${typeof e.value === 'number' ? e.value.toLocaleString() : e.value}${e.unit || ''}`).join(', ');
    return name ? `${name}: ${values}` : values;
  }

  function render(chart, m, it, layers, labelsLater) {
    const { h, svgProps, A, Shape } = I();
    const S = NS.surface;
    const p = it.props;
    const pts = it.points || [];
    if (!pts.length) return;
    const id = it.domId;
    const base = svgProps(S.seriesSvgProps(it));
    delete base.id;
    const shape = typeof p.shape === 'string' ? p.shape : 'circle';
    const symbols = pts.map((pt, i) => {
      const sp = Object.assign({}, base, svgProps(pt), { 'data-recharts-item-id': id });
      let path = null;
      if (typeof sp.cx === 'number' && typeof sp.cy === 'number' && typeof pt.size === 'number') {
        const attrs = A(sp);
        attrs.class = 'recharts-symbols';
        attrs.transform = `translate(${sp.cx}, ${sp.cy})`;
        attrs.d = NS.d3.symbol(shape, pt.size);
        path = h('path', attrs);
      }
      const gAttrs = { class: 'recharts-layer recharts-scatter-symbol', 'data-recharts-item-index': i, 'data-recharts-item-id': id };
      if (chart.accessibilityLayer()) Object.assign(gAttrs, { role: 'img', 'aria-label': pointLabel(it, pt), tabindex: i === chart.scatterFocus(it) ? 0 : -1 });
      return h('g', gAttrs, [h('g', { class: 'recharts-layer recharts-shape' }, [path])]);
    });
    layers[S.Z.scatter].push(h('g', { class: ['recharts-layer', 'recharts-scatter', p.className].filter(Boolean).join(' '), id }, [
      h('g', { class: 'recharts-layer' }, [h('g', { class: 'recharts-layer' }, symbols)]),
    ]));
    const entries = pts.map((pt) => {
      const vb = { x: pt.x == null ? 0 : pt.x, y: pt.y == null ? 0 : pt.y, width: pt.width, height: pt.height, lowerWidth: pt.width, upperWidth: pt.width };
      return Object.assign({}, vb, { value: undefined, payload: pt.payload, viewBox: vb, parentViewBox: { x: m.offset.left, y: m.offset.top, width: m.offset.width, height: m.offset.height }, fill: undefined });
    });
    (it.spec.labelList || []).forEach((ll) => labelsLater.push(S.LabelList(ll, entries, chart.ctx)));
  }

  /* The payload Recharts' item tooltip shows for point `index` of scatter item `it` (combineTooltipPayload). */
  function itemPayload(it, index) {
    const pt = it.points[index];
    const p = it.props;
    const settings = { stroke: p.stroke, strokeWidth: p.strokeWidth, fill: p.fill, nameKey: undefined, dataKey: p.dataKey, name: NS.surface.tooltipNameProp(p.name, p.dataKey), hide: p.hide, type: p.tooltipType, color: p.fill, unit: '' };
    return pt.tooltipPayload.map((e) => Object.assign({}, settings, e, { payload: e.payload }));
  }

  NS.scatter = { zAxisOf, points, render, itemPayload, pointLabel, IMPLICIT_Z };
})();
