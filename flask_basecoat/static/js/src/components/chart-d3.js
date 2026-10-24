/* Chart geometry primitives: a port of the parts of d3-path 3.1, d3-shape 3.2, d3-scale 4 and d3-array 3
   that Recharts 3.8 draws with (paths rounded to 3 digits, the linear/natural/monotone/step curves, line and
   area generators, stacks with the none/expand/sign offsets, band/point/linear scales, linear ticks and the seven
   filled symbols).
   d3 is ISC-licensed (Copyright 2010-2023 Mike Bostock). Exposed on window.FlaskBasecoatChart.d3. */
(function () {
  'use strict';
  const NS = (window.FlaskBasecoatChart = window.FlaskBasecoatChart || {});

  /* ---- d3-path ---- */
  function Path(digits) {
    this._x0 = this._y0 = this._x1 = this._y1 = null;
    this._ = '';
    const k = digits == null ? null : Math.pow(10, Math.floor(digits));
    this._r = k == null ? (v) => v : (v) => Math.round(v * k) / k;
  }
  Path.prototype = {
    moveTo(x, y) { this._x0 = this._x1 = +x; this._y0 = this._y1 = +y; this._ += 'M' + this._r(this._x0) + ',' + this._r(this._y0); },
    closePath() { if (this._x1 !== null) { this._x1 = this._x0; this._y1 = this._y0; this._ += 'Z'; } },
    lineTo(x, y) { this._x1 = +x; this._y1 = +y; this._ += 'L' + this._r(this._x1) + ',' + this._r(this._y1); },
    bezierCurveTo(x1, y1, x2, y2, x, y) {
      this._x1 = +x; this._y1 = +y;
      this._ += 'C' + this._r(+x1) + ',' + this._r(+y1) + ',' + this._r(+x2) + ',' + this._r(+y2) + ',' + this._r(this._x1) + ',' + this._r(this._y1);
    },
    rect(x, y, w, h) { this._x0 = this._x1 = +x; this._y0 = this._y1 = +y; this._ += 'M' + this._r(this._x0) + ',' + this._r(this._y0) + 'h' + this._r(+w) + 'v' + this._r(+h) + 'h' + this._r(-w) + 'Z'; },
    /* arc(0, 0, r, 0, tau) from (r, 0): the only arc a symbol draws (a full circle, as two half arcs) */
    circle(r) {
      this._ += 'M' + this._r(r) + ',0A' + this._r(r) + ',' + this._r(r) + ',0,1,1,' + this._r(-r) + ',0A' + this._r(r) + ',' + this._r(r) + ',0,1,1,' + this._r(r) + ',0';
    },
    toString() { return this._; },
  };

  /* ---- symbols (d3-shape 3.2 symbol/*.js, the seven that are drawn filled; Recharts' Symbols uses them) ---- */
  const SQRT3 = Math.sqrt(3), TAU = 2 * Math.PI;
  const STAR = (() => { const kr = Math.sin(Math.PI / 10) / Math.sin(7 * Math.PI / 10); return { ka: 0.89081309152928522810, kx: Math.sin(TAU / 10) * kr, ky: -Math.cos(TAU / 10) * kr }; })();
  const WYE = { c: -0.5, s: SQRT3 / 2, k: 1 / Math.sqrt(12) };
  const SYMBOLS = {
    circle(p, size) { p.circle(Math.sqrt(size / Math.PI)); },
    cross(p, size) {
      const r = Math.sqrt(size / 5) / 2;
      [[-3 * r, -r], [-r, -r], [-r, -3 * r], [r, -3 * r], [r, -r], [3 * r, -r], [3 * r, r], [r, r], [r, 3 * r], [-r, 3 * r], [-r, r], [-3 * r, r]].forEach((q, i) => (i ? p.lineTo(q[0], q[1]) : p.moveTo(q[0], q[1])));
      p.closePath();
    },
    diamond(p, size) {
      const tan30 = Math.sqrt(1 / 3);
      const y = Math.sqrt(size / (tan30 * 2)), x = y * tan30;
      p.moveTo(0, -y); p.lineTo(x, 0); p.lineTo(0, y); p.lineTo(-x, 0); p.closePath();
    },
    square(p, size) { const w = Math.sqrt(size), x = -w / 2; p.rect(x, x, w, w); },
    star(p, size) {
      const r = Math.sqrt(size * STAR.ka), x = STAR.kx * r, y = STAR.ky * r;
      p.moveTo(0, -r); p.lineTo(x, y);
      for (let i = 1; i < 5; ++i) {
        const a = TAU * i / 5, c = Math.cos(a), s = Math.sin(a);
        p.lineTo(s * r, -c * r); p.lineTo(c * x - s * y, s * x + c * y);
      }
      p.closePath();
    },
    triangle(p, size) {
      const y = -Math.sqrt(size / (SQRT3 * 3));
      p.moveTo(0, y * 2); p.lineTo(-SQRT3 * y, -y); p.lineTo(SQRT3 * y, -y); p.closePath();
    },
    wye(p, size) {
      const { c, s, k } = WYE;
      const r = Math.sqrt(size / ((k / 2 + 1) * 3));
      const x0 = r / 2, y0 = r * k, x1 = x0, y1 = r * k + r, x2 = -x1, y2 = y1;
      p.moveTo(x0, y0); p.lineTo(x1, y1); p.lineTo(x2, y2);
      p.lineTo(c * x0 - s * y0, s * x0 + c * y0); p.lineTo(c * x1 - s * y1, s * x1 + c * y1); p.lineTo(c * x2 - s * y2, s * x2 + c * y2);
      p.lineTo(c * x0 + s * y0, c * y0 - s * x0); p.lineTo(c * x1 + s * y1, c * y1 - s * x1); p.lineTo(c * x2 + s * y2, c * y2 - s * x2);
      p.closePath();
    },
  };
  /* symbol(type, area): the path string d3 draws, rounded to 3 digits; an unknown type is a circle, as in Recharts. */
  function symbol(type, size) {
    const p = new Path(3);
    (SYMBOLS[type] || SYMBOLS.circle)(p, size == null ? 64 : +size);
    return p.toString() || null;
  }

  /* ---- curves ---- */
  function Linear(context) { this._context = context; }
  Linear.prototype = {
    areaStart() { this._line = 0; },
    areaEnd() { this._line = NaN; },
    lineStart() { this._point = 0; },
    lineEnd() { if (this._line || (this._line !== 0 && this._point === 1)) this._context.closePath(); this._line = 1 - this._line; },
    point(x, y) {
      x = +x; y = +y;
      switch (this._point) {
        case 0: this._point = 1; if (this._line) this._context.lineTo(x, y); else this._context.moveTo(x, y); break;
        case 1: this._point = 2; // falls through
        default: this._context.lineTo(x, y); break;
      }
    },
  };

  function Natural(context) { this._context = context; }
  function controlPoints(x) {
    let i; const n = x.length - 1; let m;
    const a = new Array(n), b = new Array(n), r = new Array(n);
    a[0] = 0; b[0] = 2; r[0] = x[0] + 2 * x[1];
    for (i = 1; i < n - 1; ++i) { a[i] = 1; b[i] = 4; r[i] = 4 * x[i] + 2 * x[i + 1]; }
    a[n - 1] = 2; b[n - 1] = 7; r[n - 1] = 8 * x[n - 1] + x[n];
    for (i = 1; i < n; ++i) { m = a[i] / b[i - 1]; b[i] -= m; r[i] -= m * r[i - 1]; }
    a[n - 1] = r[n - 1] / b[n - 1];
    for (i = n - 2; i >= 0; --i) a[i] = (r[i] - a[i + 1]) / b[i];
    b[n - 1] = (x[n] + a[n - 1]) / 2;
    for (i = 0; i < n - 1; ++i) b[i] = 2 * x[i + 1] - a[i + 1];
    return [a, b];
  }
  Natural.prototype = {
    areaStart() { this._line = 0; },
    areaEnd() { this._line = NaN; },
    lineStart() { this._x = []; this._y = []; },
    lineEnd() {
      const x = this._x, y = this._y, n = x.length;
      if (n) {
        if (this._line) this._context.lineTo(x[0], y[0]); else this._context.moveTo(x[0], y[0]);
        if (n === 2) {
          this._context.lineTo(x[1], y[1]);
        } else {
          const px = controlPoints(x), py = controlPoints(y);
          for (let i0 = 0, i1 = 1; i1 < n; ++i0, ++i1) {
            this._context.bezierCurveTo(px[0][i0], py[0][i0], px[1][i0], py[1][i0], x[i1], y[i1]);
          }
        }
      }
      if (this._line || (this._line !== 0 && n === 1)) this._context.closePath();
      this._line = 1 - this._line;
      this._x = this._y = null;
    },
    point(x, y) { this._x.push(+x); this._y.push(+y); },
  };

  function sign(x) { return x < 0 ? -1 : 1; }
  function slope3(that, x2, y2) {
    const h0 = that._x1 - that._x0, h1 = x2 - that._x1,
      s0 = (that._y1 - that._y0) / (h0 || (h1 < 0 && -0)),
      s1 = (y2 - that._y1) / (h1 || (h0 < 0 && -0)),
      p = (s0 * h1 + s1 * h0) / (h0 + h1);
    return (sign(s0) + sign(s1)) * Math.min(Math.abs(s0), Math.abs(s1), 0.5 * Math.abs(p)) || 0;
  }
  function slope2(that, t) { const h = that._x1 - that._x0; return h ? (3 * (that._y1 - that._y0) / h - t) / 2 : t; }
  function monoPoint(that, t0, t1) {
    const x0 = that._x0, y0 = that._y0, x1 = that._x1, y1 = that._y1, dx = (x1 - x0) / 3;
    that._context.bezierCurveTo(x0 + dx, y0 + dx * t0, x1 - dx, y1 - dx * t1, x1, y1);
  }
  function MonotoneX(context) { this._context = context; }
  MonotoneX.prototype = {
    areaStart() { this._line = 0; },
    areaEnd() { this._line = NaN; },
    lineStart() { this._x0 = this._x1 = this._y0 = this._y1 = this._t0 = NaN; this._point = 0; },
    lineEnd() {
      switch (this._point) {
        case 2: this._context.lineTo(this._x1, this._y1); break;
        case 3: monoPoint(this, this._t0, slope2(this, this._t0)); break;
      }
      if (this._line || (this._line !== 0 && this._point === 1)) this._context.closePath();
      this._line = 1 - this._line;
    },
    point(x, y) {
      let t1 = NaN;
      x = +x; y = +y;
      if (x === this._x1 && y === this._y1) return;
      switch (this._point) {
        case 0: this._point = 1; if (this._line) this._context.lineTo(x, y); else this._context.moveTo(x, y); break;
        case 1: this._point = 2; break;
        case 2: this._point = 3; monoPoint(this, slope2(this, t1 = slope3(this, x, y)), t1); break;
        default: monoPoint(this, this._t0, t1 = slope3(this, x, y)); break;
      }
      this._x0 = this._x1; this._x1 = x;
      this._y0 = this._y1; this._y1 = y;
      this._t0 = t1;
    },
  };
  function ReflectContext(context) { this._context = context; }
  ReflectContext.prototype = {
    moveTo(x, y) { this._context.moveTo(y, x); },
    closePath() { this._context.closePath(); },
    lineTo(x, y) { this._context.lineTo(y, x); },
    bezierCurveTo(x1, y1, x2, y2, x, y) { this._context.bezierCurveTo(y1, x1, y2, x2, y, x); },
  };
  function MonotoneY(context) { this._context = new ReflectContext(context); }
  MonotoneY.prototype = Object.create(MonotoneX.prototype);
  MonotoneY.prototype.point = function (x, y) { MonotoneX.prototype.point.call(this, y, x); };

  function Step(context, t) { this._context = context; this._t = t; }
  Step.prototype = {
    areaStart() { this._line = 0; },
    areaEnd() { this._line = NaN; },
    lineStart() { this._x = this._y = NaN; this._point = 0; },
    lineEnd() {
      if (0 < this._t && this._t < 1 && this._point === 2) this._context.lineTo(this._x, this._y);
      if (this._line || (this._line !== 0 && this._point === 1)) this._context.closePath();
      if (this._line >= 0) { this._t = 1 - this._t; this._line = 1 - this._line; }
    },
    point(x, y) {
      x = +x; y = +y;
      switch (this._point) {
        case 0: this._point = 1; if (this._line) this._context.lineTo(x, y); else this._context.moveTo(x, y); break;
        case 1: this._point = 2; // falls through
        default: {
          if (this._t <= 0) {
            this._context.lineTo(this._x, y);
            this._context.lineTo(x, y);
          } else {
            const x1 = this._x * (1 - this._t) + x * this._t;
            this._context.lineTo(x1, this._y);
            this._context.lineTo(x1, y);
          }
          break;
        }
      }
      this._x = x; this._y = y;
    },
  };

  const CURVES = {
    linear: (c) => new Linear(c),
    natural: (c) => new Natural(c),
    monotoneX: (c) => new MonotoneX(c),
    monotoneY: (c) => new MonotoneY(c),
    step: (c) => new Step(c, 0.5),
    stepBefore: (c) => new Step(c, 0),
    stepAfter: (c) => new Step(c, 1),
  };

  /* Recharts' getCurveFactory: 'monotone' resolves to monotoneX/Y by layout, unknown names fall back to linear. */
  function curveFactory(type, layout) {
    let name = type || 'linear';
    if (name === 'monotone') name = layout === 'vertical' ? 'monotoneY' : 'monotoneX';
    return CURVES[name] || CURVES.linear;
  }

  /* ---- line / area generators (accessors receive the datum) ---- */
  function line(opts) {
    const { x, y, defined, curve } = opts;
    return function (data) {
      const buffer = new Path(3);
      const output = curve(buffer);
      let defined0 = false;
      const n = data.length;
      for (let i = 0; i <= n; ++i) {
        const d = data[i];
        if (!(i < n && defined(d, i)) === defined0) {
          if ((defined0 = !defined0)) output.lineStart(); else output.lineEnd();
        }
        if (defined0) output.point(+x(d, i), +y(d, i));
      }
      return buffer + '' || null;
    };
  }

  function area(opts) {
    const { x0, y0, x1, y1, defined, curve } = opts;
    return function (data) {
      const buffer = new Path(3);
      const output = curve(buffer);
      const n = data.length;
      const x0z = new Array(n), y0z = new Array(n);
      let defined0 = false, j = 0;
      for (let i = 0; i <= n; ++i) {
        const d = data[i];
        if (!(i < n && defined(d, i)) === defined0) {
          if ((defined0 = !defined0)) {
            j = i;
            output.areaStart();
            output.lineStart();
          } else {
            output.lineEnd();
            output.lineStart();
            for (let k = i - 1; k >= j; --k) output.point(x0z[k], y0z[k]);
            output.lineEnd();
            output.areaEnd();
          }
        }
        if (defined0) {
          x0z[i] = +x0(d, i); y0z[i] = +y0(d, i);
          output.point(x1 ? +x1(d, i) : x0z[i], y1 ? +y1(d, i) : y0z[i]);
        }
      }
      return buffer + '' || null;
    };
  }

  /* ---- stack ---- */
  function offsetNone(series, order) {
    const n = series.length;
    if (!(n > 1)) return;
    let s1 = series[order[0]];
    const m = s1.length;
    for (let i = 1; i < n; ++i) {
      const s0 = s1; s1 = series[order[i]];
      for (let j = 0; j < m; ++j) {
        s1[j][1] += s1[j][0] = isNaN(s0[j][1]) ? s0[j][0] : s0[j][1];
      }
    }
  }
  function offsetExpand(series, order) {
    const n = series.length;
    if (!(n > 0)) return;
    for (let j = 0, m = series[0].length; j < m; ++j) {
      let y = 0;
      for (let i = 0; i < n; ++i) y += series[i][j][1] || 0;
      if (y) for (let i = 0; i < n; ++i) series[i][j][1] /= y;
    }
    offsetNone(series, order);
  }
  function offsetSign(series) {
    const n = series.length;
    if (n <= 0) return;
    const m = series[0] && series[0].length;
    if (!m) return;
    for (let j = 0; j < m; ++j) {
      let positive = 0, negative = 0;
      for (let i = 0; i < n; ++i) {
        const col = series[i][j];
        if (col == null) continue;
        const value = isNaN(col[1]) ? col[0] : col[1];
        if (value >= 0) { col[0] = positive; positive += value; col[1] = positive; } else { col[0] = negative; negative += value; col[1] = negative; }
      }
    }
  }
  function offsetPositive(series) {
    const n = series.length;
    if (n <= 0) return;
    const m = series[0] && series[0].length;
    if (!m) return;
    for (let j = 0; j < m; ++j) {
      let positive = 0;
      for (let i = 0; i < n; ++i) {
        const col = series[i][j];
        if (col == null) continue;
        const value = isNaN(col[1]) ? col[0] : col[1];
        if (value >= 0) { col[0] = positive; positive += value; col[1] = positive; } else { col[0] = 0; col[1] = 0; }
      }
    }
  }
  const OFFSETS = { none: offsetNone, expand: offsetExpand, sign: offsetSign, positive: offsetPositive };

  function stack(data, keys, value, offsetType) {
    const sz = keys.map((key) => { const s = []; s.key = key; return s; });
    data.forEach((d, j) => {
      for (let i = 0; i < sz.length; ++i) {
        const p = [0, +value(d, sz[i].key, j)];
        p.data = d;
        sz[i][j] = p;
      }
    });
    const order = sz.map((_, i) => i);
    order.forEach((o, i) => { sz[o].index = i; });
    (OFFSETS[offsetType] || offsetNone)(sz, order);
    return sz;
  }

  /* ---- scales ---- */
  function keyOf(v) { return v !== null && typeof v === 'object' ? v.valueOf() : v; }

  function band(domainValues, rangeValues, opts) {
    const o = Object.assign({ paddingInner: 0, paddingOuter: 0, align: 0.5 }, opts || {});
    const index = new Map();
    const domain = [];
    for (const v of domainValues) { const k = keyOf(v); if (!index.has(k)) { index.set(k, domain.length); domain.push(v); } }
    const r0 = +rangeValues[0], r1 = +rangeValues[1];
    const n = domain.length, reverse = r1 < r0;
    let start = reverse ? r1 : r0;
    const stop = reverse ? r0 : r1;
    const paddingInner = Math.min(1, o.paddingInner);
    const step = (stop - start) / Math.max(1, n - paddingInner + o.paddingOuter * 2);
    start += (stop - start - step * (n - paddingInner)) * o.align;
    const bandwidth = step * (1 - paddingInner);
    let values = [];
    for (let i = 0; i < n; i++) values.push(start + step * i);
    if (reverse) values = values.reverse();
    const scale = (v) => { const i = index.get(keyOf(v)); return i === undefined ? undefined : values[i % values.length]; };
    scale.domain = () => domain.slice();
    scale.range = () => [r0, r1];
    scale.bandwidth = () => bandwidth;
    scale.step = () => step;
    return scale;
  }

  function point(domainValues, rangeValues) {
    return band(domainValues, rangeValues, { paddingInner: 1, paddingOuter: 0, align: 0.5 });
  }

  function normalize(a, b) {
    a = +a; b -= a;
    return b ? (x) => (x - a) / b : () => (isNaN(b) ? NaN : 0.5);
  }
  function interpolateNumber(a, b) { a = +a; b = +b; return (t) => a * (1 - t) + b * t; }

  const e10 = Math.sqrt(50), e5 = Math.sqrt(10), e2 = Math.sqrt(2);
  function tickSpec(start, stop, count) {
    const step = (stop - start) / Math.max(0, count),
      power = Math.floor(Math.log10(step)),
      error = step / Math.pow(10, power),
      factor = error >= e10 ? 10 : error >= e5 ? 5 : error >= e2 ? 2 : 1;
    let i1, i2, inc;
    if (power < 0) {
      inc = Math.pow(10, -power) / factor;
      i1 = Math.round(start * inc); i2 = Math.round(stop * inc);
      if (i1 / inc < start) ++i1;
      if (i2 / inc > stop) --i2;
      inc = -inc;
    } else {
      inc = Math.pow(10, power) * factor;
      i1 = Math.round(start / inc); i2 = Math.round(stop / inc);
      if (i1 * inc < start) ++i1;
      if (i2 * inc > stop) --i2;
    }
    if (i2 < i1 && 0.5 <= count && count < 2) return tickSpec(start, stop, count * 2);
    return [i1, i2, inc];
  }
  function ticks(start, stop, count) {
    stop = +stop; start = +start; count = +count;
    if (!(count > 0)) return [];
    if (start === stop) return [start];
    const reverse = stop < start;
    const [i1, i2, inc] = reverse ? tickSpec(stop, start, count) : tickSpec(start, stop, count);
    if (!(i2 >= i1)) return [];
    const n = i2 - i1 + 1, out = new Array(n);
    if (reverse) {
      if (inc < 0) for (let i = 0; i < n; ++i) out[i] = (i2 - i) / -inc;
      else for (let i = 0; i < n; ++i) out[i] = (i2 - i) * inc;
    } else {
      if (inc < 0) for (let i = 0; i < n; ++i) out[i] = (i1 + i) / -inc;
      else for (let i = 0; i < n; ++i) out[i] = (i1 + i) * inc;
    }
    return out;
  }

  function linear(domainValues, rangeValues) {
    const d = [+domainValues[0], +domainValues[1]], r = [+rangeValues[0], +rangeValues[1]];
    let f;
    if (d[1] < d[0]) { const n = normalize(d[1], d[0]), i = interpolateNumber(r[1], r[0]); f = (x) => i(n(x)); } else { const n = normalize(d[0], d[1]), i = interpolateNumber(r[0], r[1]); f = (x) => i(n(x)); }
    const scale = (x) => (x == null || isNaN(+x) ? undefined : f(+x));
    scale.domain = () => d.slice();
    scale.range = () => r.slice();
    scale.ticks = (count) => ticks(d[0], d[d.length - 1], count == null ? 10 : count);
    return scale;
  }

  NS.d3 = { Path, curveFactory, line, area, stack, band, point, linear, ticks, symbol };
})();
