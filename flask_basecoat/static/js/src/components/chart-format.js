/* Named formatters and render functions for chart specs.

   A chart spec cannot carry JavaScript, so every function-valued prop of an upstream chart (tickFormatter,
   labelFormatter, formatter, Label content, custom dot/shape/tick) is written as a reference
   {"$fn": "<name>", ...arguments}. The registry below maps each name to a function; Python builds the same
   references (flask_basecoat/charts.py, FORMATTERS) and documents them.

   Value formatters             return a value:   (value, ...) => any
     slice {start, end}                       String(value).slice(start, end)
     localeDate {locale, options}             new Date(value).toLocaleDateString(locale, options)
     configLabel                              chartConfig[value]?.label
     configLabelOfFirstDataKey                (_, payload) => chartConfig[payload[0].dataKey].label
   Tooltip row formatters       return HTML nodes for one tooltip row: (value, name, item, index, payload)
     unitValue {unit, wrap}                   label + value + unit ("kcal"), in a wrapper div when wrap is true
     unitValueWithTotal {unit, keys, after}   unitValue plus a "Total" row after the row with index `after`
   Label content                return an SVG element: (labelProps)
     centerText {lines, dominantBaseline}     <text> centred on the polar view box; lines = [{value, className, dy}],
                                              value = {"text": s} | {"sum": key} | {"pick": key, "index": n|{"state"}}
   Shapes / dots / ticks        return an SVG element: (props)
     activeRectangle {index, props}           Rectangle, extra props for the bar at `index`
     activeSector {index, grow}               Sector, outerRadius + grow for the sector at `index`
     activeSectorRing {index, grow, ring}     as activeSector plus a ring from outerRadius+ring[0] to +ring[1]
     payloadDot {r}                           Dot coloured with the data row's fill
     iconDot {icon, size, fill, stroke}       a lucide icon centred on the point
     payloadText {key, fill}                  <text> at the label position showing payload[key]
     stackedTick {keys, labelKey, firstDy}    polar tick text "a/b" with the category below
*/
(function () {
  'use strict';
  const NS = (window.FlaskBasecoatChart = window.FlaskBasecoatChart || {});
  const I = () => NS.internal;

  function idx(v, ctx) { return v && typeof v === 'object' && 'state' in v ? ctx.state[v.state] : v; }

  function valueOf(spec, ctx) {
    const { getValue } = I();
    if (spec == null) return '';
    if ('text' in spec) return spec.text;
    let v;
    if ('sum' in spec) v = ctx.data.reduce((acc, row) => acc + (Number(getValue(row, spec.sum)) || 0), 0);
    else if ('pick' in spec) { const row = ctx.data[idx(spec.index, ctx)]; v = row ? getValue(row, spec.pick) : undefined; }
    else if ('pickSum' in spec) { const row = ctx.data[idx(spec.index, ctx)]; v = row ? spec.pickSum.reduce((acc, k) => acc + (Number(getValue(row, k)) || 0), 0) : undefined; }
    return typeof v === 'number' ? v.toLocaleString() : String(v);
  }

  function el(tag, attrs, children) { return I().h(tag, attrs, children); }
  function tx(s) { return I().txt(s); }

  const VALUE = {
    slice: (o) => (value) => String(value).slice(o.start, o.end),
    localeDate: (o) => (value) => new Date(value).toLocaleDateString(o.locale || 'en-US', o.options || {}),
    configLabel: (o, ctx) => (value) => { const c = ctx.config[value]; return c ? c.label : undefined; },
    configLabelOfFirstDataKey: (o, ctx) => (_, payload) => { const k = payload && payload[0] && payload[0].dataKey; return ctx.config[k].label; },
  };

  /* Tooltip row formatters return a DocumentFragment (HTML). */
  function html(tag, cls, children, style) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (style) Object.keys(style).forEach((k) => n.style.setProperty(k, style[k]));
    (children || []).forEach((c) => n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c));
    return n;
  }
  function amount(value, unit) {
    return html('div', 'ml-auto flex items-baseline gap-0.5 font-mono font-medium text-foreground tabular-nums', [String(value), html('span', 'font-normal text-muted-foreground', [unit])]);
  }
  const ROW = {
    unitValue: (o, ctx) => (value, name) => {
      const label = (ctx.config[name] && ctx.config[name].label) || name;
      const inner = [String(label), amount(value, o.unit)];
      const frag = document.createDocumentFragment();
      if (o.wrap) frag.appendChild(html('div', 'flex min-w-[130px] items-center text-xs text-muted-foreground', inner));
      else inner.forEach((n) => frag.appendChild(typeof n === 'string' ? document.createTextNode(n) : n));
      return frag;
    },
    unitValueWithTotal: (o, ctx) => (value, name, item, index) => {
      const frag = document.createDocumentFragment();
      frag.appendChild(html('div', 'h-2.5 w-2.5 shrink-0 rounded-[2px] bg-(--color-bg)', [], { '--color-bg': `var(--color-${name})` }));
      frag.appendChild(document.createTextNode(String((ctx.config[name] && ctx.config[name].label) || name)));
      frag.appendChild(amount(value, o.unit));
      if (index === o.after) {
        const total = o.keys.reduce((acc, k) => acc + item.payload[k], 0);
        frag.appendChild(html('div', 'mt-1.5 flex basis-full items-center border-t pt-1.5 text-xs font-medium text-foreground', ['Total', amount(total, o.unit)]));
      }
      return frag;
    },
  };

  const CONTENT = {
    centerText: (o, ctx) => (props) => {
      const vb = props.viewBox;
      if (!(vb && 'cx' in vb && 'cy' in vb)) return null;
      const attrs = { x: vb.cx, y: vb.cy, 'text-anchor': 'middle' };
      if (o.dominantBaseline) attrs['dominant-baseline'] = o.dominantBaseline;
      return el('text', attrs, o.lines.map((line) => el('tspan', { x: vb.cx, y: (vb.cy || 0) + (line.dy || 0), class: line.className }, [tx(valueOf(line.value, ctx))])));
    },
  };

  const SHAPE = {
    activeRectangle: (o) => (props, ctx, S) => (props.index === o.index ? S.Rectangle(Object.assign({}, props, o.props, o.strokeFromPayload ? { stroke: props.payload[o.strokeFromPayload] } : {})) : S.Rectangle(props)),
    activeSector: (o) => (props, ctx, S) => {
      const outer = props.outerRadius || 0;
      return S.Sector(Object.assign({}, props, { outerRadius: props.index === idx(o.index, ctx) ? outer + o.grow : outer }));
    },
    activeSectorRing: (o) => (props, ctx, S) => {
      const outer = props.outerRadius || 0;
      if (props.index === idx(o.index, ctx)) {
        return S.h('g', {}, [
          S.Sector(Object.assign({}, props, { outerRadius: outer + o.grow })),
          S.Sector(Object.assign({}, props, { outerRadius: outer + o.ring[1], innerRadius: outer + o.ring[0] })),
        ]);
      }
      return S.Sector(Object.assign({}, props, { outerRadius: outer }));
    },
    payloadDot: (o) => (props) => I().Dot({ r: o.r, cx: props.cx, cy: props.cy, fill: props.payload.fill, stroke: props.payload.fill }),
    iconDot: (o, ctx) => (props) => {
      if (props.cx == null || props.cy == null) return null;
      const r = o.size;
      return { html: ctx.iconMarkup(o.icon, { x: props.cx - r / 2, y: props.cy - r / 2, width: r, height: r, fill: o.fill, stroke: o.stroke }) };
    },
    payloadText: (o) => (props) => el('text', { cx: props.cx, cy: props.cy, x: props.x, y: props.y, 'text-anchor': props.textAnchor, 'dominant-baseline': props.dominantBaseline, fill: o.fill }, [tx(props.payload[o.key])]),
    stackedTick: (o, ctx) => (props) => {
      const { svgProps, A } = I();
      const row = ctx.data[props.index];
      const y = typeof props.y === 'number' ? props.y : 0;
      const rest = Object.assign({}, props);
      ['x', 'y', 'textAnchor', 'index'].forEach((k) => delete rest[k]);
      const extra = A(svgProps(rest));
      // React passes the remaining tick props through as attributes, including the unknown ones
      if (rest.verticalAnchor != null) extra.verticalanchor = rest.verticalAnchor;
      if (rest.payload != null) extra.payload = '[object Object]';
      delete extra.class;
      const attrs = Object.assign({ x: props.x, y: y + (props.index === 0 ? o.firstDy : 0), 'text-anchor': props.textAnchor, 'font-size': 13, 'font-weight': 500 }, extra);
      if (rest.className) attrs.class = rest.className;
      return el('text', attrs, [
        el('tspan', {}, [tx(row[o.keys[0]])]),
        el('tspan', { class: 'fill-muted-foreground' }, [tx('/')]),
        el('tspan', {}, [tx(row[o.keys[1]])]),
        el('tspan', { x: props.x, dy: '1rem', 'font-size': 12, class: 'fill-muted-foreground' }, [tx(row[o.labelKey])]),
      ]);
    },
  };

  const ALL = Object.assign({}, VALUE, ROW, CONTENT, SHAPE);

  NS.formatters = {
    names: Object.keys(ALL),
    has: (name) => name in ALL,
    /* Resolve a {"$fn": ...} reference to a function bound to the chart context. */
    resolve(ref, ctx) {
      const make = ALL[ref.$fn];
      if (!make) throw new Error(`unknown chart formatter: ${ref.$fn}`);
      const f = make(ref, ctx);
      return SHAPE[ref.$fn] ? (props) => f(props, ctx, ctx.shapes) : f;
    },
    shape(ref, props, ctx) { return NS.formatters.resolve(ref, ctx)(props); },
    register(name, factory) { ALL[name] = factory; },
  };
})();
