/* Chart renderer: draws a declarative chart spec into the same DOM Recharts 3.8 produces inside shadcn's
   ChartContainer (recharts-responsive-container > recharts-wrapper > svg.recharts-surface with the z-index
   layers, plus the tooltip and legend wrappers).

   The layout maths are ports of the Recharts sources (axis domains and nice ticks, band/point scales, tick
   thinning with measured label sizes, bar positions, stacks, curves, sectors, polar axes, label positions,
   tooltip placement), so the numbers match the upstream render. The spec format is documented in
   flask_basecoat/charts.py; function-valued props arrive as {"$fn": name, ...} and are looked up in
   window.FlaskBasecoatChart.formatters (chart-format.js).

   Exposed: window.FlaskBasecoatChart.Chart (one instance per [data-slot=chart]). */
(function () {
  'use strict';
  const NS = (window.FlaskBasecoatChart = window.FlaskBasecoatChart || {});
  const d3 = NS.d3;
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const XHTML_NS = 'http://www.w3.org/1999/xhtml';

  /* ------------------------------------------------------------------ utils */
  const isNil = (v) => v === null || v === undefined;
  const isNum = (v) => typeof v === 'number' && !Number.isNaN(v);
  const isWellBehaved = (v) => typeof v === 'number' && Number.isFinite(v);
  const isNumOrStr = (v) => isNum(v) || typeof v === 'string';
  const isPercent = (v) => typeof v === 'string' && v.length > 0 && v.indexOf('%') === v.length - 1;
  const mathSign = (v) => (v === 0 ? 0 : v > 0 ? 1 : -1);
  const RADIAN = Math.PI / 180;
  const range = (a, b) => { const out = []; for (let i = a; i < b; i++) out.push(i); return out; };

  function getPercentValue(percent, total, def, validate) {
    if (def === undefined) def = 0;
    if (!isNum(percent) && typeof percent !== 'string') return def;
    let value;
    if (isPercent(percent)) {
      if (total == null) return def;
      value = (total * parseFloat(percent.slice(0, -1))) / 100;
    } else {
      value = +percent;
    }
    if (Number.isNaN(value)) value = def;
    if (validate && total != null && value > total) value = total;
    return value;
  }

  function getValue(obj, key, def) {
    if (isNil(obj) || isNil(key)) return def;
    if (typeof key === 'function') return key(obj);
    if (typeof obj !== 'object') return def;
    const parts = String(key).split('.');
    let cur = obj;
    for (const p of parts) {
      if (cur == null || typeof cur !== 'object' || !(p in cur)) return def;
      cur = cur[p];
    }
    return cur === undefined ? def : cur;
  }

  function round(num, precision) {
    const k = Math.pow(10, precision === undefined ? 4 : precision);
    const r = Math.round(num * k) / k;
    return Object.is(r, -0) ? 0 : r;
  }
  /* roundTemplateLiteral: every interpolated number is rounded to 4 decimals. */
  function rt(strings, ...values) {
    return strings.reduce((acc, s, i) => {
      const v = values[i - 1];
      if (typeof v === 'string') return acc + v + s;
      if (v !== undefined) return acc + round(v) + s;
      return acc + s;
    });
  }

  function polarToCartesian(cx, cy, radius, angle) {
    return { x: cx + Math.cos(-RADIAN * angle) * radius, y: cy + Math.sin(-RADIAN * angle) * radius };
  }

  function hasDuplicate(arr) {
    const seen = new Set();
    for (const v of arr) { const k = v != null && typeof v === 'object' ? v.valueOf() : v; if (seen.has(k)) return true; seen.add(k); }
    return false;
  }

  function sortByKey(list, key) {
    return list.map((v, i) => [v, i]).sort((a, b) => {
      const av = a[0] == null ? undefined : a[0][key];
      const bv = b[0] == null ? undefined : b[0][key];
      if (av === bv) return a[1] - b[1];
      if (av === undefined) return 1;
      if (bv === undefined) return -1;
      return av > bv ? 1 : av < bv ? -1 : a[1] - b[1];
    }).map((p) => p[0]);
  }

  function uniqBy(list, fn) {
    const seen = new Set();
    return list.filter((e) => { const k = fn(e); if (seen.has(k)) return false; seen.add(k); return true; });
  }

  /* ------------------------------------------------------------------ text measurement (getStringSize) */
  const sizeCache = new Map();
  function getStringSize(text, style) {
    if (text === undefined || text === null) return { width: 0, height: 0 };
    style = style || {};
    const key = [text, style.fontSize || '', style.fontFamily || '', style.fontWeight || '', style.fontStyle || '', style.letterSpacing || '', style.textTransform || ''].join('|');
    if (sizeCache.has(key)) return sizeCache.get(key);
    let span = document.getElementById('recharts_measurement_span');
    if (!span) {
      span = document.createElement('span');
      span.setAttribute('id', 'recharts_measurement_span');
      span.setAttribute('aria-hidden', 'true');
      document.body.appendChild(span);
    }
    Object.assign(span.style, { position: 'absolute', top: '-20000px', left: 0, padding: 0, margin: 0, border: 'none', whiteSpace: 'pre' }, style);
    span.textContent = String(text);
    const rect = span.getBoundingClientRect();
    const out = { width: rect.width, height: rect.height };
    if (sizeCache.size > 2000) sizeCache.clear();
    sizeCache.set(key, out);
    return out;
  }

  /* ------------------------------------------------------------------ reduceCSSCalc */
  const CSS_UNIT = /^(px|cm|vh|vw|em|rem|%|mm|in|pt|pc|ex|ch|vmin|vmax|Q)$/;
  function cssNum(str) {
    const m = /(-?\d+(?:\.\d+)?)([a-zA-Z%]+)?/.exec(str);
    if (!m) return { num: NaN, unit: '' };
    let num = parseFloat(m[1]); let unit = m[2] || '';
    if (unit !== '' && !CSS_UNIT.test(unit)) { num = NaN; unit = ''; }
    const RATES = { cm: 96 / 2.54, mm: 96 / 25.4, pt: 96 / 72, pc: 96 / 6, in: 96, Q: 96 / (2.54 * 40), px: 1 };
    if (unit in RATES) { num *= RATES[unit]; unit = 'px'; }
    return { num, unit };
  }
  const cssStr = (v) => '' + v.num + v.unit;
  function cssArith(expr) {
    if (expr == null || expr.includes('NaN')) return 'NaN';
    const MUL = /(-?\d+(?:\.\d+)?[a-zA-Z%]*)([*/])(-?\d+(?:\.\d+)?[a-zA-Z%]*)/;
    const ADD = /(-?\d+(?:\.\d+)?[a-zA-Z%]*)([+-])(-?\d+(?:\.\d+)?[a-zA-Z%]*)/;
    let e = expr;
    while (e.includes('*') || e.includes('/')) {
      const m = MUL.exec(e) || [];
      const l = cssNum(m[1] || ''), r = cssNum(m[3] || '');
      if (l.unit !== '' && r.unit !== '' && l.unit !== r.unit) return 'NaN';
      const res = { num: m[2] === '*' ? l.num * r.num : l.num / r.num, unit: l.unit || r.unit };
      if (Number.isNaN(res.num)) return 'NaN';
      e = e.replace(MUL, cssStr(res));
    }
    while (e.includes('+') || /.-\d+(?:\.\d+)?/.test(e)) {
      const m = ADD.exec(e) || [];
      const l = cssNum(m[1] || ''), r = cssNum(m[3] || '');
      if (l.unit !== r.unit) return 'NaN';
      const res = { num: m[2] === '+' ? l.num + r.num : l.num - r.num, unit: l.unit };
      if (Number.isNaN(res.num)) return 'NaN';
      e = e.replace(ADD, cssStr(res));
    }
    return e;
  }
  function reduceCSSCalc(expression) {
    try {
      let e = expression.slice(5, -1).replace(/\s+/g, '');
      const PAREN = /\(([^()]*)\)/;
      let m;
      while ((m = PAREN.exec(e)) != null) e = e.replace(PAREN, cssArith(m[1]));
      e = cssArith(e);
      return e === 'NaN' ? '' : e;
    } catch (err) {
      return '';
    }
  }

  /* ------------------------------------------------------------------ element tree */
  function h(tag, attrs, children) {
    const kids = [];
    (function add(list) {
      for (const c of list) {
        if (c == null || c === false) continue;
        if (Array.isArray(c)) add(c); else kids.push(c);
      }
    })(children || []);
    return { tag, attrs: attrs || {}, children: kids };
  }
  const txt = (s) => ({ text: String(s) });

  /* React's SVG attribute names for the camelCase props Recharts spreads (svgPropertiesNoEvents). */
  const SVG_KEYS = new Set(('className color height id lang max media method min name style target width role tabIndex alignmentBaseline baselineShift clip clipPath clipRule colorInterpolation cursor cx cy d direction display dominantBaseline dx dy fill fillOpacity fillRule filter floodColor floodOpacity fontFamily fontSize fontSizeAdjust fontStretch fontStyle fontVariant fontWeight from fx fy gradientTransform gradientUnits href in letterSpacing lightingColor markerEnd markerMid markerStart mask offset opacity orient orientation overflow paintOrder pathLength pointerEvents points r radius rotate rx ry shapeRendering stopColor stopOpacity stroke strokeDasharray strokeDashoffset strokeLinecap strokeLinejoin strokeMiterlimit strokeOpacity strokeWidth textAnchor textDecoration textLength textRendering to transform vectorEffect visibility wordSpacing writingMode x1 x2 x y1 y2 y z angle').split(' '));
  const CAMEL_ATTRS = { className: 'class', tabIndex: 'tabindex', viewBox: 'viewBox', gradientTransform: 'gradientTransform', gradientUnits: 'gradientUnits', pathLength: 'pathLength', textLength: 'textLength', xlinkHref: 'xlink:href' };
  function attrName(k) {
    if (CAMEL_ATTRS[k]) return CAMEL_ATTRS[k];
    if (k.startsWith('data-') || k.startsWith('aria-')) return k;
    return k.replace(/[A-Z]/g, (c) => '-' + c.toLowerCase());
  }
  /* Filter an arbitrary props object to its SVG attributes, as React would render them (insertion order kept). */
  function svgProps(obj) {
    const out = {};
    if (!obj || typeof obj !== 'object') return out;
    for (const k of Object.keys(obj)) {
      const v = obj[k];
      if (!(SVG_KEYS.has(k) || k.startsWith('data-'))) continue;
      if (v === undefined || v === null || typeof v === 'function' || typeof v === 'boolean' && !k.startsWith('data-')) continue;
      if (typeof v === 'object') continue;
      out[k] = v;
    }
    return out;
  }
  /* props (camelCase) -> attrs (DOM names) */
  function A(props) {
    const out = {};
    for (const k of Object.keys(props)) {
      const v = props[k];
      if (v === undefined || v === null || v === false) continue;
      out[attrName(k)] = v === true ? '' : v;
    }
    return out;
  }

  function toDom(node, parentNs) {
    if (node.text !== undefined) return document.createTextNode(node.text);
    if (node.html !== undefined) { const tpl = document.createElementNS(SVG_NS, 'g'); tpl.innerHTML = node.html; return tpl.firstChild; }
    const el = document.createElementNS(parentNs || SVG_NS, node.tag);
    for (const k of Object.keys(node.attrs)) {
      const v = node.attrs[k];
      if (v === undefined || v === null) continue;
      if (k === 'xlink:href') el.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', String(v));
      else el.setAttribute(k, String(v));
    }
    for (const c of node.children) el.appendChild(toDom(c, parentNs));
    return el;
  }

  /* ------------------------------------------------------------------ Text (recharts/component/Text) */
  const BREAKING = /[ \f\n\r\t\v\u2028\u2029]+/;
  function wordsByLines(p, content) {
    const children = content;
    const plain = () => [{ words: isNil(children) ? [] : String(children).split(BREAKING), width: undefined }];
    if (!(p.width || p.scaleToFit)) return plain();
    const words = isNil(children) ? [] : (p.breakAll ? String(children).split('') : String(children).split(BREAKING));
    const ww = words.map((w) => ({ word: w, width: getStringSize(w, p.style).width }));
    const spaceWidth = p.breakAll ? 0 : getStringSize(' ', p.style).width;
    const lineWidth = p.width;
    const lines = [];
    for (const { word, width } of ww) {
      const cur = lines[lines.length - 1];
      if (cur && width != null && (lineWidth == null || p.scaleToFit || cur.width + width + spaceWidth < Number(lineWidth))) {
        cur.words.push(word);
        cur.width += width + spaceWidth;
      } else {
        lines.push({ words: [word], width });
      }
    }
    return lines;
  }

  const TEXT_OMIT = new Set(['x', 'y', 'lineHeight', 'capHeight', 'fill', 'scaleToFit', 'textAnchor', 'verticalAnchor', 'dx', 'dy', 'angle', 'className', 'breakAll', 'maxLines', 'style', 'index', 'payload', 'visibleTicksCount', 'tickFormatter', 'padding', 'viewBox', 'value', 'position', 'children', 'content', 'parentViewBox', 'labelRef', 'textBreakAll', 'zIndex']);
  function Text(props, content) {
    const p = Object.assign({ angle: 0, breakAll: false, capHeight: '0.71em', fill: '#808080', lineHeight: '1em', scaleToFit: false, textAnchor: 'start', verticalAnchor: 'end', x: 0, y: 0 }, stripUndef(props));
    const lines = wordsByLines(p, content);
    if (!isNumOrStr(p.x) || !isNumOrStr(p.y) || lines.length === 0) return null;
    const x = Number(p.x) + (isNum(p.dx) ? p.dx : 0);
    const y = Number(p.y) + (isNum(p.dy) ? p.dy : 0);
    if (!isWellBehaved(x) || !isWellBehaved(y)) return null;
    let startDy;
    if (p.verticalAnchor === 'start') startDy = reduceCSSCalc(`calc(${p.capHeight})`);
    else if (p.verticalAnchor === 'middle') startDy = reduceCSSCalc(`calc(${(lines.length - 1) / 2} * -${p.lineHeight} + (${p.capHeight} / 2))`);
    else startDy = reduceCSSCalc(`calc(${lines.length - 1} * -${p.lineHeight})`);
    const rest = {};
    for (const k of Object.keys(p)) if (!TEXT_OMIT.has(k)) rest[k] = p[k];
    const textProps = svgProps(rest);
    const transforms = [];
    if (p.angle) transforms.push(`rotate(${p.angle}, ${x}, ${y})`);
    if (transforms.length) textProps.transform = transforms.join(' ');
    const fill = String(p.fill).includes('url') ? '#808080' : p.fill;
    const attrs = Object.assign(A(textProps), { x, y, class: ['recharts-text', p.className].filter(Boolean).join(' '), 'text-anchor': p.textAnchor, fill });
    return h('text', attrs, lines.map((line, i) => h('tspan', { x, dy: i === 0 ? startDy : p.lineHeight }, [txt(line.words.join(p.breakAll ? '' : ' '))])));
  }
  function stripUndef(o) { const out = {}; for (const k of Object.keys(o)) if (o[k] !== undefined) out[k] = o[k]; return out; }

  /* ------------------------------------------------------------------ shapes */
  function rectanglePath(x, y, width, height, radius) {
    const rw = round(width), rh = round(height);
    const maxRadius = Math.min(Math.abs(rw) / 2, Math.abs(rh) / 2);
    const ySign = rh >= 0 ? 1 : -1, xSign = rw >= 0 ? 1 : -1;
    const clockWise = (rh >= 0 && rw >= 0) || (rh < 0 && rw < 0) ? 1 : 0;
    let path;
    if (maxRadius > 0 && Array.isArray(radius)) {
      const nr = [0, 0, 0, 0];
      for (let i = 0; i < 4; i++) { const r = radius[i] == null ? 0 : radius[i]; nr[i] = r > maxRadius ? maxRadius : r; }
      path = rt`M${x},${y + ySign * nr[0]}`;
      if (nr[0] > 0) path += rt`A ${nr[0]},${nr[0]},0,0,${clockWise},${x + xSign * nr[0]},${y}`;
      path += rt`L ${x + width - xSign * nr[1]},${y}`;
      if (nr[1] > 0) path += rt`A ${nr[1]},${nr[1]},0,0,${clockWise},
        ${x + width},${y + ySign * nr[1]}`;
      path += rt`L ${x + width},${y + height - ySign * nr[2]}`;
      if (nr[2] > 0) path += rt`A ${nr[2]},${nr[2]},0,0,${clockWise},
        ${x + width - xSign * nr[2]},${y + height}`;
      path += rt`L ${x + xSign * nr[3]},${y + height}`;
      if (nr[3] > 0) path += rt`A ${nr[3]},${nr[3]},0,0,${clockWise},
        ${x},${y + height - ySign * nr[3]}`;
      path += 'Z';
    } else if (maxRadius > 0 && radius === +radius && radius > 0) {
      const r = Math.min(maxRadius, radius);
      path = rt`M ${x},${y + ySign * r}
            A ${r},${r},0,0,${clockWise},${x + xSign * r},${y}
            L ${x + width - xSign * r},${y}
            A ${r},${r},0,0,${clockWise},${x + width},${y + ySign * r}
            L ${x + width},${y + height - ySign * r}
            A ${r},${r},0,0,${clockWise},${x + width - xSign * r},${y + height}
            L ${x + xSign * r},${y + height}
            A ${r},${r},0,0,${clockWise},${x},${y + height - ySign * r} Z`;
    } else {
      path = rt`M ${x},${y} h ${width} v ${height} h ${-width} Z`;
    }
    return path;
  }

  /* Rectangle: <path class="recharts-rectangle"> with rounded x/y/width/height attributes. */
  function Rectangle(props) {
    const p = Object.assign({ x: 0, y: 0, width: 0, height: 0, radius: 0 }, stripUndef(props));
    const { x, y, width, height, radius } = p;
    if (x !== +x || y !== +y || width !== +width || height !== +height || width === 0 || height === 0) return null;
    const rest = svgProps(p);
    delete rest.radius; delete rest.className;
    const attrs = Object.assign(A(rest), { x: round(x), y: round(y), width: round(width), height: round(height) });
    if (typeof radius === 'number') attrs.radius = radius;
    attrs.class = ['recharts-rectangle', p.className].filter(Boolean).join(' ');
    attrs.d = rectanglePath(x, y, width, height, radius);
    return h('path', attrs);
  }

  function sectorDeltaAngle(s, e) { const sign = mathSign(e - s); return sign * Math.min(Math.abs(e - s), 359.999); }
  function sectorPath(cx, cy, innerRadius, outerRadius, startAngle, endAngle) {
    const angle = sectorDeltaAngle(startAngle, endAngle);
    const tempEnd = startAngle + angle;
    const os = polarToCartesian(cx, cy, outerRadius, startAngle), oe = polarToCartesian(cx, cy, outerRadius, tempEnd);
    let path = rt`M ${os.x},${os.y}
    A ${outerRadius},${outerRadius},0,
    ${+(Math.abs(angle) > 180)},${+(startAngle > tempEnd)},
    ${oe.x},${oe.y}
  `;
    if (innerRadius > 0) {
      const is = polarToCartesian(cx, cy, innerRadius, startAngle), ie = polarToCartesian(cx, cy, innerRadius, tempEnd);
      path += rt`L ${ie.x},${ie.y}
            A ${innerRadius},${innerRadius},0,
            ${+(Math.abs(angle) > 180)},${+(startAngle <= tempEnd)},
            ${is.x},${is.y} Z`;
    } else {
      path += rt`L ${cx},${cy} Z`;
    }
    return path;
  }
  function tangentCircle(cx, cy, radius, angle, sign, isExternal, cornerRadius, cornerIsExternal) {
    const centerRadius = cornerRadius * (isExternal ? 1 : -1) + radius;
    const theta = Math.asin(cornerRadius / centerRadius) / RADIAN;
    const centerAngle = cornerIsExternal ? angle : angle + sign * theta;
    const center = polarToCartesian(cx, cy, centerRadius, centerAngle);
    const circleTangency = polarToCartesian(cx, cy, radius, centerAngle);
    const lineTangencyAngle = cornerIsExternal ? angle - sign * theta : angle;
    const lineTangency = polarToCartesian(cx, cy, centerRadius * Math.cos(theta * RADIAN), lineTangencyAngle);
    return { center, circleTangency, lineTangency, theta };
  }
  function sectorWithCorner(o) {
    const { cx, cy, innerRadius, outerRadius, cornerRadius, forceCornerRadius, cornerIsExternal, startAngle, endAngle } = o;
    const sign = mathSign(endAngle - startAngle);
    const s = tangentCircle(cx, cy, outerRadius, startAngle, sign, false, cornerRadius, cornerIsExternal);
    const e = tangentCircle(cx, cy, outerRadius, endAngle, -sign, false, cornerRadius, cornerIsExternal);
    const outerArcAngle = cornerIsExternal ? Math.abs(startAngle - endAngle) : Math.abs(startAngle - endAngle) - s.theta - e.theta;
    if (outerArcAngle < 0) {
      if (forceCornerRadius) {
        return rt`M ${s.lineTangency.x},${s.lineTangency.y}
        a${cornerRadius},${cornerRadius},0,0,1,${cornerRadius * 2},0
        a${cornerRadius},${cornerRadius},0,0,1,${-cornerRadius * 2},0
      `;
      }
      return sectorPath(cx, cy, innerRadius, outerRadius, startAngle, endAngle);
    }
    let path = rt`M ${s.lineTangency.x},${s.lineTangency.y}
    A${cornerRadius},${cornerRadius},0,0,${+(sign < 0)},${s.circleTangency.x},${s.circleTangency.y}
    A${outerRadius},${outerRadius},0,${+(outerArcAngle > 180)},${+(sign < 0)},${e.circleTangency.x},${e.circleTangency.y}
    A${cornerRadius},${cornerRadius},0,0,${+(sign < 0)},${e.lineTangency.x},${e.lineTangency.y}
  `;
    if (innerRadius > 0) {
      const si = tangentCircle(cx, cy, innerRadius, startAngle, sign, true, cornerRadius, cornerIsExternal);
      const ei = tangentCircle(cx, cy, innerRadius, endAngle, -sign, true, cornerRadius, cornerIsExternal);
      const innerArcAngle = cornerIsExternal ? Math.abs(startAngle - endAngle) : Math.abs(startAngle - endAngle) - si.theta - ei.theta;
      if (innerArcAngle < 0 && cornerRadius === 0) return `${path}L${cx},${cy}Z`;
      path += rt`L${ei.lineTangency.x},${ei.lineTangency.y}
      A${cornerRadius},${cornerRadius},0,0,${+(sign < 0)},${ei.circleTangency.x},${ei.circleTangency.y}
      A${innerRadius},${innerRadius},0,${+(innerArcAngle > 180)},${+(sign > 0)},${si.circleTangency.x},${si.circleTangency.y}
      A${cornerRadius},${cornerRadius},0,0,${+(sign < 0)},${si.lineTangency.x},${si.lineTangency.y}Z`;
    } else {
      path += rt`L${cx},${cy}Z`;
    }
    return path;
  }
  function Sector(props) {
    const p = Object.assign({ cx: 0, cy: 0, innerRadius: 0, outerRadius: 0, startAngle: 0, endAngle: 0, cornerRadius: 0, forceCornerRadius: false, cornerIsExternal: false }, stripUndef(props));
    const { cx, cy, innerRadius, outerRadius, cornerRadius, forceCornerRadius, cornerIsExternal, startAngle, endAngle } = p;
    if (outerRadius < innerRadius || startAngle === endAngle) return null;
    const deltaRadius = outerRadius - innerRadius;
    const cr = getPercentValue(cornerRadius, deltaRadius, 0, true);
    let d;
    if (cr > 0 && Math.abs(startAngle - endAngle) < 360) {
      d = sectorWithCorner({ cx, cy, innerRadius, outerRadius, cornerRadius: Math.min(cr, deltaRadius / 2), forceCornerRadius, cornerIsExternal, startAngle, endAngle });
    } else {
      d = sectorPath(cx, cy, innerRadius, outerRadius, startAngle, endAngle);
    }
    const rest = svgProps(p);
    delete rest.className;
    const attrs = A(rest);
    attrs.class = ['recharts-sector', p.className].filter(Boolean).join(' ');
    attrs.d = d;
    return h('path', attrs);
  }

  function Dot(props) {
    const p = stripUndef(props);
    if (!(isNum(p.cx) && isNum(p.cy) && isNum(p.r))) return null;
    const rest = svgProps(p);
    delete rest.className; delete rest.cx; delete rest.cy; delete rest.r;
    const attrs = A(rest);
    attrs.class = ['recharts-dot', p.className].filter(Boolean).join(' ');
    attrs.cx = p.cx; attrs.cy = p.cy; attrs.r = p.r;
    return h('circle', attrs);
  }

  const validPoint = (pt) => pt != null && pt.x === +pt.x && pt.y === +pt.y;
  function polygonPath(points, connectNulls) {
    let segs = [[]];
    points.forEach((e) => {
      const last = segs[segs.length - 1];
      if (validPoint(e)) last.push(e); else if (last.length > 0) segs.push([]);
    });
    if (validPoint(points[0])) segs[segs.length - 1].push(points[0]);
    if (segs[segs.length - 1].length <= 0) segs = segs.slice(0, -1);
    if (connectNulls) segs = [segs.flat()];
    const path = segs.map((sp) => sp.reduce((acc, pt, i) => rt`${acc}${i === 0 ? 'M' : 'L'}${pt.x},${pt.y}`, '')).join('');
    return segs.length === 1 ? `${path}Z` : path;
  }
  function Polygon(props) {
    const p = stripUndef(props);
    if (!p.points || !p.points.length) return null;
    const others = svgProps(p);
    delete others.points; delete others.className;
    const d = polygonPath(p.points, p.connectNulls);
    const attrs = A(others);
    attrs.fill = d.slice(-1) === 'Z' ? p.fill : 'none';
    if (attrs.fill === undefined) delete attrs.fill;
    attrs.class = ['recharts-polygon', p.className].filter(Boolean).join(' ');
    attrs.d = d;
    return h('path', attrs);
  }

  /* Curve: <path class="recharts-curve"> from points with a d3 curve, optional baseline (area). */
  function curvePath(type, points, baseLine, layout, connectNulls) {
    const curve = d3.curveFactory(type, layout);
    const defined = (pt) => pt != null && isWellBehaved(pt.x) && isWellBehaved(pt.y);
    const fmt = connectNulls ? points.filter(defined) : points;
    if (Array.isArray(baseLine)) {
      const areaPoints = points.map((e, i) => Object.assign({}, e, { base: baseLine[i] }));
      const areaDefined = (d) => d.base != null && defined(d.base) && defined(d);
      const gen = layout === 'vertical'
        ? d3.area({ x0: (d) => d.base.x, x1: (d) => d.x, y0: (d) => d.y, y1: null, defined: areaDefined, curve })
        : d3.area({ x0: (d) => d.x, x1: null, y0: (d) => d.base.y, y1: (d) => d.y, defined: areaDefined, curve });
      return gen(connectNulls ? areaPoints.filter(areaDefined) : areaPoints);
    }
    let gen;
    if (layout === 'vertical' && isNum(baseLine)) gen = d3.area({ x0: () => baseLine, x1: (d) => d.x, y0: (d) => d.y, y1: null, defined, curve });
    else if (isNum(baseLine)) gen = d3.area({ x0: (d) => d.x, x1: null, y0: () => baseLine, y1: (d) => d.y, defined, curve });
    else gen = d3.line({ x: (d) => d.x, y: (d) => d.y, defined, curve });
    return gen(fmt);
  }
  function Curve(props) {
    const p = stripUndef(props);
    if (!p.points || !p.points.length) return null;
    const d = curvePath(p.type || 'linear', p.points, p.baseLine, p.layout, p.connectNulls);
    const rest = svgProps(p);
    delete rest.className; delete rest.points;
    const attrs = A(rest);
    attrs.class = ['recharts-curve', p.className].filter(Boolean).join(' ');
    if (d != null) attrs.d = d;
    return h('path', attrs);
  }

  /* Shape(): user option (object props / custom fn / default) wrapped in its active/inactive layer. */
  function Shape(shapeType, option, props, ctx, classes) {
    let shape;
    const fnRef = option && typeof option === 'object' && option.$fn;
    if (fnRef) {
      shape = NS.formatters.shape(option, props, ctx, { Rectangle, Sector, Curve, h });
    } else if (option && typeof option === 'object') {
      shape = SHAPES[shapeType](Object.assign({}, props, option));
    } else {
      shape = SHAPES[shapeType](props);
    }
    const c = classes || {};
    return h('g', { class: 'recharts-layer ' + (props.isActive ? (c.active || 'recharts-active-shape') : (c.inactive || 'recharts-shape')) }, [shape]);
  }
  const SHAPES = { rectangle: Rectangle, sector: Sector, curve: Curve };

  /* ------------------------------------------------------------------ nice ticks (recharts/util/scale/getNiceTickValues) */
  /* Decimal.js is emulated by rounding intermediate results to 12 significant digits. */
  const dec = (v) => (v === 0 ? 0 : parseFloat(v.toPrecision(12)));
  function digitCount(value) { return value === 0 ? 1 : Math.floor(Math.log10(Math.abs(value))) + 1; }
  function adaptiveStep(roughStep, allowDecimals, correction) {
    if (roughStep <= 0) return 0;
    const dc = digitCount(roughStep);
    const dcv = Math.pow(10, dc);
    const ratio = dec(roughStep / dcv);
    const ratioScale = dc !== 1 ? 0.05 : 0.1;
    const amend = dec((Math.ceil(dec(ratio / ratioScale)) + correction) * ratioScale);
    const formatStep = dec(amend * dcv);
    return allowDecimals ? formatStep : Math.ceil(formatStep);
  }
  function calculateStep(min, max, tickCount, allowDecimals, correction) {
    correction = correction || 0;
    if (!Number.isFinite((max - min) / (tickCount - 1))) return { step: 0, tickMin: 0, tickMax: 0 };
    const step = adaptiveStep(dec((max - min) / (tickCount - 1)), allowDecimals, correction);
    let middle;
    if (min <= 0 && max >= 0) middle = 0;
    else { middle = dec((min + max) / 2); middle = dec(middle - (middle % step)); }
    let below = Math.ceil(dec((middle - min) / step));
    let up = Math.ceil(dec((max - middle) / step));
    const scaleCount = below + up + 1;
    if (scaleCount > tickCount) return calculateStep(min, max, tickCount, allowDecimals, correction + 1);
    if (scaleCount < tickCount) {
      up = max > 0 ? up + (tickCount - scaleCount) : up;
      below = max > 0 ? below : below + (tickCount - scaleCount);
    }
    return { step, tickMin: dec(middle - below * step), tickMax: dec(middle + up * step) };
  }
  function rangeStep(start, end, step) {
    const out = []; let num = start, i = 0;
    while (num < end && i < 100000) { out.push(num); num = dec(num + step); i++; }
    return out;
  }
  function tickOfSingleValue(value, tickCount, allowDecimals) {
    let step = 1, middle = value;
    if (!Number.isInteger(value) && allowDecimals) {
      const abs = Math.abs(value);
      if (abs < 1) { step = Math.pow(10, digitCount(value) - 1); middle = dec(Math.floor(value / step) * step); } else if (abs > 1) middle = Math.floor(value);
    } else if (value === 0) middle = Math.floor((tickCount - 1) / 2);
    else if (!allowDecimals) middle = Math.floor(value);
    const mi = Math.floor((tickCount - 1) / 2);
    return range(0, tickCount).map((i) => dec(middle + (i - mi) * step));
  }
  function getNiceTickValues(domain, tickCount, allowDecimals) {
    const [min, max] = domain;
    const count = Math.max(tickCount, 2);
    const cmin = Math.min(min, max), cmax = Math.max(min, max);
    if (cmin === cmax) return tickOfSingleValue(cmin, tickCount, allowDecimals);
    const { step, tickMin, tickMax } = calculateStep(cmin, cmax, count, allowDecimals, 0);
    const values = rangeStep(tickMin, dec(tickMax + 0.1 * step), step);
    return min > max ? values.reverse() : values;
  }
  function getTickValuesFixedDomain(domain, tickCount, allowDecimals) {
    const [min, max] = domain;
    const cmin = Math.min(min, max), cmax = Math.max(min, max);
    if (cmin === cmax) return [cmin];
    const count = Math.max(tickCount, 2);
    const step = adaptiveStep(dec((cmax - cmin) / (count - 1)), allowDecimals, 0);
    let values = [...rangeStep(cmin, cmax, step), cmax];
    if (allowDecimals === false) values = values.map((v) => Math.round(v));
    return min > max ? values.reverse() : values;
  }

  /* ------------------------------------------------------------------ axis domain & scale */
  const isCategoricalAxis = (layout, axisType) => (layout === 'horizontal' && axisType === 'xAxis') || (layout === 'vertical' && axisType === 'yAxis') || (layout === 'centric' && axisType === 'angleAxis') || (layout === 'radial' && axisType === 'radiusAxis');
  const isWellFormedDomain = (v) => Array.isArray(v) && v.length === 2 && isWellBehaved(v[0]) && isWellBehaved(v[1]);
  function makeNumber(v) { if (isNumOrStr(v) || v instanceof Date) { const n = Number(v); if (isWellBehaved(n)) return n; } return undefined; }
  function makeDomain(v) {
    if (Array.isArray(v)) { const a = [makeNumber(v[0]), makeNumber(v[1])]; return isWellFormedDomain(a) ? a : undefined; }
    const n = makeNumber(v);
    return n == null ? undefined : [n, n];
  }
  function mergeDomains(...domains) {
    const all = domains.filter(Boolean);
    if (!all.length) return undefined;
    const flat = all.flat();
    return [Math.min(...flat), Math.max(...flat)];
  }
  function getDomainDefinition(axis) {
    if (axis.domain != null) return axis.domain;
    if (axis.ticks != null) {
      if (axis.type === 'number') { const v = axis.ticks.map(makeNumber).filter((x) => x != null); return [Math.min(...v), Math.max(...v)]; }
      if (axis.type === 'category') return axis.ticks.map(String);
    }
    return [0, 'auto'];
  }
  function parseNumericalUserDomain(userDomain, dataDomain, allowDataOverflow) {
    if (!allowDataOverflow && dataDomain == null) return undefined;
    if (Array.isArray(userDomain) && userDomain.length === 2) {
      const [pmin, pmax] = userDomain;
      let fmin, fmax;
      if (pmin === 'auto') { if (dataDomain != null) fmin = Math.min(...dataDomain); } else if (isNum(pmin)) fmin = pmin;
      else fmin = dataDomain && dataDomain[0];
      if (pmax === 'auto') { if (dataDomain != null) fmax = Math.max(...dataDomain); } else if (isNum(pmax)) fmax = pmax;
      else fmax = dataDomain && dataDomain[1];
      const cand = [fmin, fmax];
      if (isWellFormedDomain(cand)) {
        if (dataDomain == null || allowDataOverflow) return cand;
        return [Math.min(cand[0], dataDomain[0]), Math.max(cand[1], dataDomain[1])];
      }
    }
    return undefined;
  }
  function realScaleType(axis, hasBar, chartName) {
    if (axis.scale === 'auto' || axis.scale == null) {
      if (axis.type === 'category' && (chartName === 'LineChart' || chartName === 'AreaChart' || (chartName === 'ComposedChart' && !hasBar))) return 'point';
      if (axis.type === 'category') return 'band';
      return 'linear';
    }
    return ['band', 'point', 'linear'].includes(axis.scale) ? axis.scale : 'point';
  }
  function makeScale(type, domain, rangeV) {
    if (type === 'band') return d3.band(domain, rangeV);
    if (type === 'point') return d3.point(domain, rangeV);
    return d3.linear(domain, rangeV);
  }
  function bandSizeOfAxis(axis, ticks, isBar) {
    if (axis && axis.scale && axis.scale.bandwidth) {
      const bw = axis.scale.bandwidth();
      if (!isBar || bw > 0) return bw;
    }
    if (axis && ticks && ticks.length >= 2) {
      const ordered = ticks.slice().sort((a, b) => a.coordinate - b.coordinate);
      let bs = Infinity;
      for (let i = 1; i < ordered.length; i++) bs = Math.min((ordered[i].coordinate || 0) - (ordered[i - 1].coordinate || 0), bs);
      return bs === Infinity ? 0 : bs;
    }
    return isBar ? undefined : 0;
  }

  /* Resolve an axis: domain, nice ticks, scale and the three tick lists Recharts keeps. */
  function resolveAxis(axis, ctx) {
    const { layout, data, items, stackGroups, stackOffset, chartName, hasBar } = ctx;
    const isCat = isCategoricalAxis(layout, axis.axisType);
    const applied = !isNil(axis.dataKey)
      ? data.map((e) => getValue(e, axis.dataKey))
      : (items.length ? items.flatMap((it) => data.map((e) => getValue(e, it.dataKey))) : data.slice());
    let domain;
    if (isCat && isNil(axis.dataKey)) {
      domain = range(0, data.length);
    } else if (axis.type === 'category') {
      const cd = applied.filter((v) => isNumOrStr(v) || v instanceof Date);
      if (isCat && (isNil(axis.dataKey) || (axis.allowDuplicatedCategory && hasDuplicate(cd)))) domain = range(0, applied.length);
      else if (axis.allowDuplicatedCategory) domain = cd;
      else domain = uniqBy(cd, (v) => v);
    } else if (stackOffset === 'expand' && axis.axisType !== 'angleAxis' && axis.axisType !== 'radiusAxis') {
      domain = [0, 1];
    } else {
      const def = getDomainDefinition(axis);
      const includeStack = (layout === 'vertical' && axis.axisType === 'xAxis') || (layout === 'horizontal' && axis.axisType === 'yAxis');
      let stackDomain;
      if (includeStack && stackGroups) {
        let lo = Infinity, hi = -Infinity;
        for (const g of Object.values(stackGroups)) {
          for (const series of g.stackedData) {
            for (const pt of series) for (const v of [pt[0], pt[1]]) if (isNum(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
          }
        }
        stackDomain = [lo === Infinity ? 0 : lo, hi === -Infinity ? 0 : hi];
        if (stackDomain[0] === 0 && stackDomain[1] === 0) stackDomain = undefined;
      }
      let lower, upper;
      const unstacked = ctx.polar ? items : items.filter((it) => it.stackId == null);
      data.forEach((e) => {
        unstacked.forEach((it) => {
          const dd = makeDomain(getValue(e, isNil(axis.dataKey) ? it.dataKey : axis.dataKey));
          if (dd) { lower = lower == null ? dd[0] : Math.min(lower, dd[0]); upper = upper == null ? dd[1] : Math.max(upper, dd[1]); }
        });
      });
      if (!isNil(axis.dataKey)) {
        data.forEach((e) => {
          const dd = makeDomain(getValue(e, axis.dataKey));
          if (dd) { lower = lower == null ? dd[0] : Math.min(lower, dd[0]); upper = upper == null ? dd[1] : Math.max(upper, dd[1]); }
        });
      }
      const dataDomain = isWellBehaved(lower) && isWellBehaved(upper) ? [lower, upper] : undefined;
      const merged = includeStack ? mergeDomains(stackDomain, dataDomain) : mergeDomains(dataDomain);
      domain = parseNumericalUserDomain(def, merged, axis.allowDataOverflow);
    }
    const scaleType = realScaleType(axis, hasBar, chartName);
    let niceTicks;
    if ((axis.niceTicks || 'auto') !== 'none' && scaleType === 'linear' && axis.tickCount) {
      const def = getDomainDefinition(axis);
      const hasAuto = Array.isArray(def) && (def[0] === 'auto' || def[1] === 'auto');
      if (hasAuto && isWellFormedDomain(domain)) niceTicks = getNiceTickValues(domain, axis.tickCount, axis.allowDecimals);
      else if (axis.type === 'number' && isWellFormedDomain(domain)) niceTicks = getTickValuesFixedDomain(domain, axis.tickCount, axis.allowDecimals);
    }
    let fullDomain = domain;
    if (axis.axisType !== 'angleAxis' && axis.type === 'number' && isWellFormedDomain(domain) && niceTicks && niceTicks.length) {
      fullDomain = [Math.min(domain[0], niceTicks[0]), Math.max(domain[1], niceTicks[niceTicks.length - 1])];
    }
    if (scaleType === 'linear' && fullDomain && !isWellFormedDomain(fullDomain)) {
      const nums = fullDomain.filter(isWellBehaved);
      fullDomain = nums.length ? [Math.min(...nums), Math.max(...nums)] : undefined;
    }
    const rangeV = axis.reversed ? [axis.range[1], axis.range[0]] : axis.range;
    const scale = fullDomain ? makeScale(scaleType, fullDomain, rangeV) : null;
    const categoricalDomain = isCat && !isNil(axis.dataKey) && (axis.type === 'number' || (axis.scale && axis.scale !== 'auto')) ? applied : undefined;
    const duplicateDomain = !isNil(axis.dataKey) && isCat && axis.type === 'category' && axis.allowDuplicatedCategory && hasDuplicate(applied) ? applied : undefined;
    Object.assign(axis, { isCategorical: isCat, domain: fullDomain, niceTicks, realScaleType: scaleType, scale, categoricalDomain, duplicateDomain });
    if (!scale) { axis.ticks_ = []; axis.itemTicks = []; axis.tooltipTicks = []; return axis; }
    const bw = scale.bandwidth ? scale.bandwidth() : 0;
    let offset = axis.type === 'category' && scale.bandwidth ? bw / 2 : 0;
    if (axis.axisType === 'angleAxis' && rangeV && rangeV.length >= 2) offset = mathSign(rangeV[0] - rangeV[1]) * 2 * offset;
    const mk = (list, off, valueOf) => list.map((entry, index) => {
      const sc = scale(valueOf ? valueOf(entry) : entry);
      return isWellBehaved(sc) ? { coordinate: sc + off, value: entry, index, offset: off } : null;
    }).filter(Boolean);
    // combineAxisTicks (axis labels, grid, polar grid)
    const userTicks = axis.ticksProp || niceTicks;
    if (userTicks) axis.ticks_ = mk(userTicks, offset, (e) => (duplicateDomain ? duplicateDomain.indexOf(e) : e));
    else if (isCat && categoricalDomain) axis.ticks_ = mk(categoricalDomain, offset);
    else if (scale.ticks) axis.ticks_ = mk(scale.ticks(axis.tickCount), offset);
    else axis.ticks_ = scale.domain().map((entry, index) => { const sc = scale(entry); return isWellBehaved(sc) ? { coordinate: sc + offset, value: duplicateDomain ? duplicateDomain[entry] : entry, index, offset } : null; }).filter(Boolean);
    // combineGraphicalItemTicks (positions of bars, points)
    let goff = 0;
    if (isCat && categoricalDomain) axis.itemTicks = mk(categoricalDomain, goff);
    else if (scale.ticks) axis.itemTicks = mk(scale.ticks(axis.tickCount), goff);
    else axis.itemTicks = scale.domain().map((entry, index) => { const sc = scale(entry); return isWellBehaved(sc) ? { coordinate: sc + goff, value: duplicateDomain ? duplicateDomain[entry] : entry, index, offset: goff } : null; }).filter(Boolean);
    // combineTicksOfTooltipAxis
    if (isCat && categoricalDomain) axis.tooltipTicks = mk(categoricalDomain, offset);
    else axis.tooltipTicks = scale.domain().map((entry, index) => { const sc = scale(entry); return isWellBehaved(sc) ? { coordinate: sc + offset, value: duplicateDomain ? duplicateDomain[entry] : entry, index, offset } : null; }).filter(Boolean);
    return axis;
  }

  /* ------------------------------------------------------------------ cartesian axis tick thinning (getTicks) */
  function isVisible(sign, pos, getSize, start, end) {
    if (sign * pos < sign * start || sign * pos > sign * end) return false;
    const size = getSize();
    return sign * (pos - (sign * size) / 2 - start) >= 0 && sign * (pos + (sign * size) / 2 - end) <= 0;
  }
  function getTicks(props, fontSize, letterSpacing) {
    const { tick, ticks, viewBox, minTickGap, orientation, interval, tickFormatter, unit, angle } = props;
    if (!ticks || !ticks.length || !tick) return [];
    if (isNum(interval)) return ticks.filter((_, i) => i % (interval + 1) === 0);
    const sizeKey = orientation === 'top' || orientation === 'bottom' ? 'width' : 'height';
    const style = { fontSize, letterSpacing };
    const unitSize = unit && sizeKey === 'width' ? getStringSize(unit, style) : { width: 0, height: 0 };
    const getTickSize = (content, index) => {
      const value = typeof tickFormatter === 'function' ? tickFormatter(content.value, index) : content.value;
      if (sizeKey === 'width') {
        const s = getStringSize(value, style);
        return angledWidth({ width: s.width + unitSize.width, height: s.height + unitSize.height }, angle);
      }
      return getStringSize(value, style)[sizeKey];
    };
    const sign = ticks.length >= 2 ? mathSign(ticks[1].coordinate - ticks[0].coordinate) : 1;
    const isW = sizeKey === 'width';
    const b = sign === 1
      ? { start: isW ? viewBox.x : viewBox.y, end: isW ? viewBox.x + viewBox.width : viewBox.y + viewBox.height }
      : { start: isW ? viewBox.x + viewBox.width : viewBox.y + viewBox.height, end: isW ? viewBox.x : viewBox.y };
    let candidates;
    if (interval === 'equidistantPreserveStart') return equidistantTicks(sign, b, getTickSize, ticks, minTickGap);
    if (interval === 'preserveStart' || interval === 'preserveStartEnd') candidates = ticksStart(sign, b, getTickSize, ticks, minTickGap, interval === 'preserveStartEnd');
    else candidates = ticksEnd(sign, b, getTickSize, ticks, minTickGap);
    return candidates.filter((e) => e.isShow);
  }
  function angledWidth(size, angle) {
    const a = (((angle || 0) % 180) + 180) % 180 * RADIAN;
    const th = Math.atan(size.height / size.width);
    const w = a > th && a < Math.PI - th ? size.height / Math.sin(a) : size.width / Math.cos(a);
    return Math.abs(w);
  }
  function ticksEnd(sign, b, getTickSize, ticks, minTickGap) {
    const result = ticks.slice();
    const len = result.length;
    let { start, end } = b;
    for (let i = len - 1; i >= 0; i--) {
      let entry = result[i];
      let size;
      const getSize = () => { if (size === undefined) size = getTickSize(ticks[i], i); return size; };
      if (i === len - 1) {
        const gap = sign * (entry.coordinate + (sign * getSize()) / 2 - end);
        entry = result[i] = Object.assign({}, entry, { tickCoord: gap > 0 ? entry.coordinate - gap * sign : entry.coordinate });
      } else {
        entry = result[i] = Object.assign({}, entry, { tickCoord: entry.coordinate });
      }
      if (isVisible(sign, entry.tickCoord, getSize, start, end)) {
        end = entry.tickCoord - sign * (getSize() / 2 + minTickGap);
        result[i] = Object.assign({}, entry, { isShow: true });
      }
    }
    return result;
  }
  function ticksStart(sign, b, getTickSize, ticks, minTickGap, preserveEnd) {
    const result = ticks.slice();
    const len = result.length;
    let { start, end } = b;
    if (preserveEnd) {
      let tail = ticks[len - 1];
      const tailSize = getTickSize(tail, len - 1);
      const tailGap = sign * (tail.coordinate + (sign * tailSize) / 2 - end);
      tail = result[len - 1] = Object.assign({}, tail, { tickCoord: tailGap > 0 ? tail.coordinate - tailGap * sign : tail.coordinate });
      if (isVisible(sign, tail.tickCoord, () => tailSize, start, end)) {
        end = tail.tickCoord - sign * (tailSize / 2 + minTickGap);
        result[len - 1] = Object.assign({}, tail, { isShow: true });
      }
    }
    const count = preserveEnd ? len - 1 : len;
    for (let i = 0; i < count; i++) {
      let entry = result[i];
      let size;
      const getSize = () => { if (size === undefined) size = getTickSize(ticks[i], i); return size; };
      if (i === 0) {
        const gap = sign * (entry.coordinate - (sign * getSize()) / 2 - start);
        entry = result[i] = Object.assign({}, entry, { tickCoord: gap < 0 ? entry.coordinate - gap * sign : entry.coordinate });
      } else {
        entry = result[i] = Object.assign({}, entry, { tickCoord: entry.coordinate });
      }
      if (isVisible(sign, entry.tickCoord, getSize, start, end)) {
        start = entry.tickCoord + sign * (getSize() / 2 + minTickGap);
        result[i] = Object.assign({}, entry, { isShow: true });
      }
    }
    return result;
  }
  function equidistantTicks(sign, b, getTickSize, ticks, minTickGap) {
    let stepsize = 1, index = 0, start = b.start;
    while (stepsize <= ticks.length) {
      const entry = ticks[index];
      if (entry === undefined) return ticks.filter((_, i) => i % stepsize === 0);
      let size;
      const i = index;
      const getSize = () => { if (size === undefined) size = getTickSize(entry, i); return size; };
      const isShow = index === 0 || isVisible(sign, entry.coordinate, getSize, start, b.end);
      if (!isShow) { index = 0; start = b.start; stepsize += 1; } else { start = entry.coordinate + sign * (getSize() / 2 + minTickGap); index += stepsize; }
    }
    return [];
  }

  /* ------------------------------------------------------------------ exports for the chart module */
  NS.internal = {
    isNil, isNum, isWellBehaved, isNumOrStr, isPercent, mathSign, range, getPercentValue, getValue, round, rt,
    polarToCartesian, sortByKey, uniqBy, getStringSize, reduceCSSCalc, h, txt, svgProps, A, toDom, Text,
    Rectangle, Sector, Dot, Polygon, Curve, Shape, curvePath, rectanglePath, sectorPath,
    getNiceTickValues, getTickValuesFixedDomain, isCategoricalAxis, resolveAxis, bandSizeOfAxis, getTicks,
    SVG_NS, XHTML_NS, stripUndef,
  };
})();
