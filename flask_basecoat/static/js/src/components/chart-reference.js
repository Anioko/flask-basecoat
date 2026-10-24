/* Chart reference elements: a port of Recharts 3.8's ReferenceLine and ReferenceArea (cartesian/ReferenceLine.tsx,
   cartesian/ReferenceArea.tsx, util/scale/RechartsScale.ts, util/scale/CartesianScaleHelper.ts).

   A spec lists them in `references`, in the order they appear in the chart's JSX:
     {"component": "ReferenceLine", "x": 200 | "y": 50 | "segment": [{"x": "Jan", "y": 4800}, {"x": "Feb", "y": 4800}],
      "stroke", "strokeDasharray", "ifOverflow", "position", "label", ...every other prop}
     {"component": "ReferenceArea", "x1", "x2", "y1", "y2", "fill", "fillOpacity", "stroke", "ifOverflow", "label", ...}
   Coordinates are data values of the first X and Y axis, as in Recharts. A line is drawn at zIndex 400 and an area at
   zIndex 100; their labels (a Label prop, as an object) are drawn at the label layer, 2000. */
(function () {
  'use strict';
  const NS = (window.FlaskBasecoatChart = window.FlaskBasecoatChart || {});

  function I() { return NS.internal; }

  const LINE_DEFAULTS = { ifOverflow: 'discard', xAxisId: 0, yAxisId: 0, fill: 'none', label: false, stroke: '#ccc', fillOpacity: 1, strokeWidth: 1, position: 'middle' };
  const AREA_DEFAULTS = { ifOverflow: 'discard', xAxisId: 0, yAxisId: 0, radius: 0, fill: '#ccc', label: false, fillOpacity: 0.5, stroke: 'none', strokeWidth: 1 };

  /* RechartsScale: map() with the band position, isInRange(), rangeMin()/rangeMax() over an axis scale. */
  function scaleOf(axis) {
    const sc = axis && axis.scale;
    if (!sc) return null;
    const r = sc.range();
    const range = [Math.min(r[0], r[1]), Math.max(r[0], r[1])];
    return {
      rangeMin: () => range[0],
      rangeMax: () => range[1],
      isInRange(v) { return v >= range[0] && v <= range[1]; },
      map(input, position) {
        let base = sc(input);
        if (base == null) return undefined;
        if (sc.bandwidth && position) {
          const bw = sc.bandwidth();
          if (position === 'middle') base += bw / 2; else if (position === 'end') base += bw;
        }
        return base;
      },
    };
  }

  /* CartesianScaleHelperImpl.mapWithFallback for one segment end. */
  function mapWithFallback(xs, ys, value, position, fallback) {
    const fx = fallback === 'rangeMin' ? xs.rangeMin() : fallback === 'rangeMax' ? xs.rangeMax() : 0;
    const fy = fallback === 'rangeMin' ? ys.rangeMin() : fallback === 'rangeMax' ? ys.rangeMax() : 0;
    const x = xs.map(value.x, position), y = ys.map(value.y, position);
    return { x: x != null ? x : fx, y: y != null ? y : fy };
  }

  /* ReferenceLine getEndPoints: [{x, y}, {x, y}] in pixels, or null when the line is not drawn. */
  function lineEndPoints(xs, ys, vb, props, xAxis, yAxis) {
    const { isNumOrStr, isWellBehaved } = I();
    const { x, y, segment, ifOverflow, position } = props;
    if (isNumOrStr(y)) {
      const coord = ys.map(y, position);
      if (!isWellBehaved(coord)) return null;
      if (ifOverflow === 'discard' && !ys.isInRange(coord)) return null;
      const points = [{ x: vb.x + vb.width, y: coord }, { x: vb.x, y: coord }];
      return yAxis.orientation === 'left' ? points.reverse() : points;
    }
    if (isNumOrStr(x)) {
      const coord = xs.map(x, position);
      if (!isWellBehaved(coord)) return null;
      if (ifOverflow === 'discard' && !xs.isInRange(coord)) return null;
      const points = [{ x: coord, y: vb.y + vb.height }, { x: coord, y: vb.y }];
      return xAxis.orientation === 'top' ? points.reverse() : points;
    }
    if (segment != null && segment.length === 2) {
      const points = [mapWithFallback(xs, ys, segment[0], position, 'rangeMin'), mapWithFallback(xs, ys, segment[1], position, 'rangeMax')];
      if (ifOverflow === 'discard' && points.some((p) => !(xs.isInRange(p.x) && ys.isInRange(p.y)))) return null;
      return points;
    }
    return null;
  }

  /* util/CartesianUtils rectWithPoints */
  function rectWithPoints(p1, p2) {
    return { x: Math.min(p1.x, p2.x), y: Math.min(p1.y, p2.y), width: Math.abs(p2.x - p1.x), height: Math.abs(p2.y - p1.y) };
  }

  /* ReferenceArea getRect: {x, y, width, height} in pixels, or null when the area is not drawn. */
  function areaRect(xs, ys, props, has) {
    const p1 = {
      x: has.x1 ? (xs.map(props.x1, 'start') != null ? xs.map(props.x1, 'start') : null) : xs.rangeMin(),
      y: has.y1 ? (ys.map(props.y1, 'start') != null ? ys.map(props.y1, 'start') : null) : ys.rangeMin(),
    };
    const p2 = {
      x: has.x2 ? (xs.map(props.x2, 'end') != null ? xs.map(props.x2, 'end') : null) : xs.rangeMax(),
      y: has.y2 ? (ys.map(props.y2, 'end') != null ? ys.map(props.y2, 'end') : null) : ys.rangeMax(),
    };
    const inRange = (p) => (p.x == null || xs.isInRange(p.x)) && (p.y == null || ys.isInRange(p.y));
    if (props.ifOverflow === 'discard' && (!inRange(p1) || !inRange(p2))) return null;
    return rectWithPoints(p1, p2);
  }

  /* The pixel geometry of every reference of the spec, from the resolved axes of the model. */
  function build(chart, m) {
    const refs = chart.spec.references || [];
    if (!refs.length) return [];
    const { isNumOrStr } = I();
    const S = NS.surface;
    const xs = scaleOf(m.xAxis), ys = scaleOf(m.yAxis);
    if (!xs || !ys) return [];
    const vb = { x: m.offset.left, y: m.offset.top, width: m.offset.width, height: m.offset.height };
    return refs.map((raw) => {
      const isLine = raw.component === 'ReferenceLine';
      const props = Object.assign({}, S.resolveProps(raw, chart.ctx));
      const withDefaults = Object.assign({}, props);
      Object.keys(isLine ? LINE_DEFAULTS : AREA_DEFAULTS).forEach((k) => { if (withDefaults[k] === undefined) withDefaults[k] = (isLine ? LINE_DEFAULTS : AREA_DEFAULTS)[k]; });
      if (isLine) {
        const pts = lineEndPoints(xs, ys, vb, withDefaults, m.xAxis, m.yAxis);
        if (!pts || pts[0] == null || pts[1] == null) return { kind: 'line', props: withDefaults, hidden: true };
        const [p1, p2] = pts;
        return { kind: 'line', props: withDefaults, x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y, rect: rectWithPoints(p1, p2) };
      }
      const has = { x1: isNumOrStr(props.x1), x2: isNumOrStr(props.x2), y1: isNumOrStr(props.y1), y2: isNumOrStr(props.y2) };
      if (!has.x1 && !has.x2 && !has.y1 && !has.y2) return { kind: 'area', props: withDefaults, hidden: true };
      const rect = areaRect(xs, ys, withDefaults, has);
      return rect ? { kind: 'area', props: withDefaults, rect } : { kind: 'area', props: withDefaults, hidden: true };
    });
  }

  function labelOf(chart, ref) {
    const label = ref.props.label;
    if (!label || label === true) return null;
    const rect = ref.rect;
    const viewBox = { x: rect.x, y: rect.y, width: rect.width, height: rect.height, lowerWidth: rect.width, upperWidth: rect.width };
    const lp = typeof label === 'object' ? label : { value: label };
    return NS.surface.Label(Object.assign({}, lp, { viewBox }), chart.ctx);
  }

  function render(chart, m, layers) {
    const { h, svgProps, A, Rectangle } = I();
    const S = NS.surface;
    (m.references || []).forEach((ref) => {
      if (ref.hidden) return;
      const p = ref.props;
      const base = svgProps(p);
      const clipPath = p.ifOverflow === 'hidden' ? `url(#${chart.clipId})` : undefined;
      let shape;
      if (ref.kind === 'line') {
        const { isWellBehaved } = I();
        if (![ref.x1, ref.y1, ref.x2, ref.y2].every(isWellBehaved)) return;
        shape = h('line', Object.assign(A(Object.assign({ clipPath }, base)), { x1: ref.x1, y1: ref.y1, x2: ref.x2, y2: ref.y2, class: 'recharts-reference-line-line' }));
        layers[S.Z.line].push(h('g', { class: ['recharts-layer', 'recharts-reference-line', p.className].filter(Boolean).join(' ') }, [shape]));
      } else {
        const rp = Object.assign({ clipPath }, base, ref.rect, { className: 'recharts-reference-area-rect' });
        shape = Rectangle(rp);
        layers[S.Z.area].push(h('g', { class: ['recharts-layer', 'recharts-reference-area', p.className].filter(Boolean).join(' ') }, [shape]));
      }
      const label = labelOf(chart, ref);
      if (label) layers[S.Z.label].push(label);
    });
  }

  NS.reference = { build, render, scaleOf, lineEndPoints, areaRect };
})();
