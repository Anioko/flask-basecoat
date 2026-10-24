"""Browser golden for the shadcn charts.

Recharts only draws after a real layout pass, so the chart goldens are taken from React + Recharts running in
headless Chromium rather than from ReactDOMServer. For every chart in the pinned charts page grouping
(compliance/upstream/shadcn/charts-app/charts.tsx) this script

  1. opens charts/harness.html?name=<chart> at a 1280x900 viewport (the golden directory is served over a local
     http.server thread; file:// breaks script and stylesheet loading),
  2. waits for window.__ready (every chart surface has a size), then for the DOM to stop changing
     (Recharts' entry animations run to the end; no upstream prop is changed to switch them off),
  3. saves out/charts/<name>.html with the document skeleton render.tsx uses,
  4. for charts that render a ChartTooltip, moves the real pointer to the canonical hover point and saves
     out/charts/<name>.hover.html once the tooltip content is in the DOM,
  5. writes out/charts/manifest.json (group, fullWidth, width, height, slots, rechartsClasses, hover point).

It also regenerates out/chart.html (the radix `chart` component example) through the same browser path, and the
charts that live inside blocks (BLOCK_CHARTS, e.g. `blocks/dashboard-01`): at a 1440x900 viewport, inside a frame as
wide as the card is in the block's layout, saved as out/blocks/<block>.chart.html, .chart.hover.html and one
.chart.<value>.html per range variant (the upstream ToggleGroupItem clicked by the real pointer). Their manifest
entries are keyed `blocks/<block>`; the hover point is also recorded relative to the chart surface (dx, dy).

Canonical hover point (replayed by check_runtime from the manifest):
  cartesian charts  the horizontal centre of the third category (vertical centre of the plot area); for
                    layout="vertical" charts the vertical centre of the third category. Category bounds are
                    found by sweeping the pointer across the plot area and watching the tooltip change.
  pie / radial      a point inside the second sector (the interior point nearest its bounding-box centre).
  radar             halfway from the chart centre towards the second angle-axis tick (the second polygon
                    vertex when the chart has no angle axis).

--extra renders the oracle charts in charts/extra (the forms shadcn has no original for: R18 matrix and scatter,
R19 cost bridge) instead, into out/charts-extra with their own manifest, so the 70-chart set stays as it is. A chart
with item tooltips (scatter) is hovered on its third symbol.

Usage (from anywhere):  python compliance/golden/charts/render_charts.py [--extra] [name ...]
Prerequisites: node charts/build.mjs (bundle.js) and the golden stylesheet (npm run css) in compliance/golden.
"""
import functools
import hashlib
import http.server
import json
import pathlib
import re
import sys
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
GOLDEN = HERE.parent
OUT = GOLDEN / 'out'
OUT_CHARTS = OUT / 'charts'
OUT_EXTRA = OUT / 'charts-extra'
CHART_SRC = GOLDEN.parent / 'upstream' / 'shadcn' / 'charts'
EXTRA_SRC = HERE / 'extra'
VIEWPORT = {'width': 1280, 'height': 900}
TOOLTIP_SELECTOR = '.recharts-tooltip-wrapper .cn-chart-tooltip'


def wrap(name, body, stylesheet):
    # Same skeleton as render.tsx wrap(); only the stylesheet path differs for pages one level down.
    return f"""<!doctype html>
<html lang="en" class="style-vega">
<head>
<meta charset="utf-8">
<title>golden: {name}</title>
<link rel="stylesheet" href="{stylesheet}">
</head>
<body data-golden="{name}">
{body}
</body>
</html>
"""


class Quiet(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        '': 'application/octet-stream', '.html': 'text/html', '.js': 'text/javascript',
        '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml',
        '.woff2': 'font/woff2', '.png': 'image/png',
    }

    def log_message(self, *args):
        pass


def serve():
    handler = functools.partial(Quiet, directory=str(GOLDEN))
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


HASH_JS = """() => { const s = document.body.innerHTML; let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return s.length + ':' + h }"""


def wait_stable(page, quiet_ms=300, confirm_ms=700, timeout_ms=20000):
    """Wait until body.innerHTML is unchanged for quiet_ms, then confirm it is still unchanged confirm_ms later
    (Pie starts its animation after a 400ms delay, longer than the quiet window)."""
    start = time.monotonic()
    last = page.evaluate(HASH_JS)
    changed = time.monotonic()
    while (time.monotonic() - start) * 1000 < timeout_ms:
        page.wait_for_timeout(50)
        h = page.evaluate(HASH_JS)
        if h != last:
            last, changed = h, time.monotonic()
            continue
        if (time.monotonic() - changed) * 1000 >= quiet_ms:
            page.wait_for_timeout(confirm_ms)
            h = page.evaluate(HASH_JS)
            if h == last:
                return True
            last, changed = h, time.monotonic()
    return False


INFO_JS = """(sel) => {
  const el = document.querySelector(sel);
  const r = el.getBoundingClientRect();
  const slots = new Set(), rc = new Set();
  [el, ...el.querySelectorAll('*')].forEach((n) => {
    const s = n.getAttribute('data-slot'); if (s) slots.add(s);
    const c = n.getAttribute('class') || '';
    c.split(/\\s+/).forEach((k) => { if (k.startsWith('recharts-')) rc.add(k); });
  });
  const svg = el.querySelector('svg.recharts-surface');
  const sr = svg ? svg.getBoundingClientRect() : null;
  return { width: Math.round(r.width * 100) / 100, height: Math.round(r.height * 100) / 100,
           surface: sr ? { width: Math.round(sr.width * 100) / 100, height: Math.round(sr.height * 100) / 100 } : null,
           slots: [...slots].sort(), rechartsClasses: [...rc].sort() };
}"""

# Plot area of the first chart in screen coordinates (the clip rect Recharts draws its series into).
PLOT_JS = """() => {
  const svg = document.querySelector('[data-slot=chart] svg.recharts-surface');
  const rect = svg.querySelector('defs clipPath rect');
  const sr = svg.getBoundingClientRect();
  if (!rect) return { x: sr.left, y: sr.top, width: sr.width, height: sr.height, clip: false };
  const m = svg.getScreenCTM();
  const p = (x, y) => { const q = new DOMPoint(x, y).matrixTransform(m); return [q.x, q.y]; };
  const x = +rect.getAttribute('x'), y = +rect.getAttribute('y'), w = +rect.getAttribute('width'), h = +rect.getAttribute('height');
  const [x0, y0] = p(x, y), [x1, y1] = p(x + w, y + h);
  return { x: x0, y: y0, width: x1 - x0, height: y1 - y0, clip: true };
}"""

SIG_JS = """() => new Promise((res) => requestAnimationFrame(() => requestAnimationFrame(() => {
  const t = document.querySelector('.recharts-tooltip-wrapper .cn-chart-tooltip');
  if (!t) return res('');
  const cur = document.querySelector('.recharts-tooltip-cursor');
  const dots = [...document.querySelectorAll('.recharts-active-dot')].map((d) => d.innerHTML).join('|');
  res(t.innerText + '#' + (cur ? cur.outerHTML : '') + '#' + dots);
})))"""

POLAR_KIND_JS = """() => {
  if (document.querySelector('.recharts-pie')) return 'pie';
  if (document.querySelector('.recharts-radial-bar-sectors, .recharts-radial-bar')) return 'radial';
  if (document.querySelector('.recharts-radar')) return 'radar';
  return null;
}"""

# Interior point of the second data sector, nearest its bounding-box centre.
SECTOR_JS = """(kind) => {
  const all = [...document.querySelectorAll('[data-slot=chart] path.recharts-sector')]
    .filter((p) => !p.classList.contains('recharts-radial-bar-background-sector'));
  const el = all[1] || all[0];
  if (!el) return null;
  const bb = el.getBBox();
  const m = el.getScreenCTM();
  const cx = bb.x + bb.width / 2, cy = bb.y + bb.height / 2;
  let best = null;
  const N = 40;
  for (let i = 0; i <= N; i++) for (let j = 0; j <= N; j++) {
    const x = bb.x + bb.width * i / N, y = bb.y + bb.height * j / N;
    if (!el.isPointInFill(new DOMPoint(x, y))) continue;
    const d = (x - cx) ** 2 + (y - cy) ** 2;
    if (!best || d < best.d) best = { x, y, d };
  }
  if (!best) best = { x: cx, y: cy };
  const q = new DOMPoint(best.x, best.y).matrixTransform(m);
  return { x: q.x, y: q.y, target: 'sector[1]' };
}"""

RADAR_JS = """() => {
  const svg = document.querySelector('[data-slot=chart] svg.recharts-surface');
  const m = svg.getScreenCTM();
  const scr = (x, y) => { const q = new DOMPoint(x, y).matrixTransform(m); return [q.x, q.y]; };
  const ticks = [...svg.querySelectorAll('.recharts-polar-angle-axis-tick')];
  let pts = [], target = 'angle-tick[1]';
  if (ticks.length >= 2) {
    pts = ticks.map((t) => { const tx = t.querySelector('text'); return [+tx.getAttribute('x'), +tx.getAttribute('y')]; });
  } else {
    const poly = svg.querySelector('.recharts-radar-polygon path');
    if (!poly) return null;
    const d = poly.getAttribute('d');
    pts = [...d.matchAll(/[ML]\\s*(-?[\\d.]+)[ ,](-?[\\d.]+)/g)].map((x) => [+x[1], +x[2]]);
    target = 'polygon-vertex[1]';
  }
  // Centre: the polar grid spokes start there; without a grid, the mean of the evenly spaced points.
  let c = null;
  const spoke = svg.querySelector('.recharts-polar-grid-angle line');
  if (spoke) c = [+spoke.getAttribute('x1'), +spoke.getAttribute('y1')];
  if (!c) c = [pts.reduce((a, p) => a + p[0], 0) / pts.length, pts.reduce((a, p) => a + p[1], 0) / pts.length];
  const p = pts[1];
  const [x, y] = scr(c[0] + (p[0] - c[0]) * 0.5, c[1] + (p[1] - c[1]) * 0.5);
  return { x, y, target };
}"""


def sweep(page, plot, axis):
    """Move the pointer across the plot area along one axis; return the category segments in order."""
    step = 2
    segs = []
    if axis == 'x':
        fixed = plot['y'] + plot['height'] / 2
        lo, hi = plot['x'] + 0.5, plot['x'] + plot['width'] - 0.5
    else:
        fixed = plot['x'] + plot['width'] / 2
        lo, hi = plot['y'] + 0.5, plot['y'] + plot['height'] - 0.5
    pos = lo
    while pos <= hi:
        if axis == 'x':
            page.mouse.move(pos, fixed)
        else:
            page.mouse.move(fixed, pos)
        sig = page.evaluate(SIG_JS)
        if sig:
            if segs and segs[-1]['sig'] == sig:
                segs[-1]['end'] = pos
            else:
                segs.append({'sig': sig, 'start': pos, 'end': pos})
                if len(segs) >= 4:
                    break
        pos += step
    return segs, fixed


# Centre of the third scatter symbol (an item tooltip chart has no categories to sweep).
SCATTER_JS = """() => {
  const el = document.querySelectorAll('[data-slot=chart] .recharts-scatter-symbol')[2];
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { x: r.left + r.width / 2, y: r.top + r.height / 2, target: 'symbol[2]' };
}"""


def hover_point(page):
    if page.evaluate("!!document.querySelector('[data-slot=chart] .recharts-scatter')"):
        pt = page.evaluate(SCATTER_JS)
        return (dict(pt, kind='scatter') if pt else None), None
    kind = page.evaluate(POLAR_KIND_JS)
    if kind in ('pie', 'radial'):
        pt = page.evaluate(SECTOR_JS, kind)
        return (dict(pt, kind=kind) if pt else None), None
    if kind == 'radar':
        pt = page.evaluate(RADAR_JS)
        return (dict(pt, kind=kind) if pt else None), None
    plot = page.evaluate(PLOT_JS)
    segs, fixed = sweep(page, plot, 'x')
    axis = 'x'
    if len(segs) < 3:
        page.mouse.move(0, 0)
        segs_y, fixed_y = sweep(page, plot, 'y')
        if len(segs_y) > len(segs):
            segs, fixed, axis = segs_y, fixed_y, 'y'
    if not segs:
        return None, 'sweep found no tooltip'
    seg = segs[2] if len(segs) >= 3 else segs[-1]
    mid = (seg['start'] + seg['end']) / 2
    pt = {'x': mid, 'y': fixed} if axis == 'x' else {'x': fixed, 'y': mid}
    note = None if len(segs) >= 3 else f'only {len(segs)} categories found'
    return dict(pt, kind='cartesian', axis=axis, target='category[2]' if len(segs) >= 3 else f'category[{len(segs) - 1}]'), note


def load(page, base, name):
    page.mouse.move(0, 0)
    page.goto(f'{base}/charts/harness.html?name={name}', wait_until='load')
    page.wait_for_function('window.__ready === true || !!window.__error', timeout=20000)
    err = page.evaluate('window.__error || null')
    if err:
        raise RuntimeError(err)
    if not wait_stable(page):
        raise RuntimeError('DOM did not settle within 20s')


def has_tooltip(name):
    if name in BLOCK_CHARTS:
        return True
    path = EXTRA_SRC / f'{name}.tsx'
    src = (path if path.exists() else CHART_SRC / f'{name}.tsx').read_text(encoding='utf-8')
    return re.search(r'<ChartTooltip(?!Content)\b', src) is not None


# Charts inside blocks (entry.tsx BLOCK_CHARTS). Taken at the block viewport, inside a frame as wide as the card is in
# the block's layout, and saved next to the block's SSR golden as out/blocks/<block>.chart.html (+ .hover.html, and
# one page per range variant, reached by clicking the upstream ToggleGroupItem, the upstream state change).
BLOCK_VIEWPORT = {'width': 1440, 'height': 900}
BLOCK_CHARTS = {
    'blocks/dashboard-01': {
        'width': 1096,
        'state': 'timeRange', 'initial': '90d',
        'variants': [{'value': '30d', 'label': 'Last 30 days'}, {'value': '7d', 'label': 'Last 7 days'}],
    },
}

# Hover point relative to the top-left corner of the first svg.recharts-surface, so it can be replayed on a page
# where the chart sits elsewhere (a block scrolls).
SURFACE_JS = """() => { const r = document.querySelector('[data-slot=chart] svg.recharts-surface').getBoundingClientRect();
  return { left: r.left, top: r.top, width: r.width, height: r.height }; }"""


def render_block_chart(page, base, name, conf):
    """Base page, hover page and range variants of one block chart. Returns the manifest entry."""
    frame = '[data-chart-frame]'
    golden_name = f'{name}.chart'
    page.set_viewport_size(BLOCK_VIEWPORT)
    load(page, base, name)
    info = page.evaluate(INFO_JS, frame)
    body = page.evaluate(f"document.querySelector('{frame}').outerHTML")
    (OUT / f'{golden_name}.html').write_text(wrap(golden_name, body, '../golden.css'), encoding='utf-8', newline='\n')
    entry = {'group': 'blocks', 'fullWidth': False, 'block': name.split('/', 1)[1], 'viewport': BLOCK_VIEWPORT,
             'frameWidth': conf['width'], 'width': info['width'], 'height': info['height'], 'surface': info['surface'],
             'slots': info['slots'], 'rechartsClasses': info['rechartsClasses'], 'golden': f'{golden_name}.html',
             'state': conf['state'], 'initial': conf['initial'], 'hover': None, 'variants': {}}
    pt, note = hover_point(page)
    if not pt:
        raise RuntimeError(f'no hover point ({note})')
    page.mouse.move(0, 0)
    page.wait_for_timeout(50)
    x, y = round(pt['x'], 1), round(pt['y'], 1)
    page.mouse.move(x, y)
    page.wait_for_selector(TOOLTIP_SELECTOR, state='attached', timeout=3000)
    wait_stable(page, quiet_ms=300, confirm_ms=300)
    hbody = page.evaluate(f"document.querySelector('{frame}').outerHTML")
    (OUT / f'{golden_name}.hover.html').write_text(wrap(golden_name + '.hover', hbody, '../golden.css'), encoding='utf-8', newline='\n')
    sr = page.evaluate(SURFACE_JS)
    hinfo = page.evaluate(INFO_JS, frame)
    entry['hover'] = {'x': x, 'y': y, 'relativeTo': 'surface', 'dx': round(x - sr['left'], 1), 'dy': round(y - sr['top'], 1),
                      'kind': pt['kind'], 'target': pt.get('target'), 'axis': pt.get('axis'), 'scrollY': 0,
                      'tooltipSelector': TOOLTIP_SELECTOR, 'slots': hinfo['slots'], 'golden': f'{golden_name}.hover.html'}
    if note:
        entry['hover']['note'] = note
    for v in conf['variants']:
        # a fresh page (no hover history), then the real pointer clicks the upstream ToggleGroupItem
        load(page, base, name)
        item = page.locator('[data-slot=toggle-group-item]', has_text=v['label'])
        item.click()
        page.mouse.move(0, 0)
        page.wait_for_function(
            "(label) => [...document.querySelectorAll('[data-slot=toggle-group-item]')].some((b) => b.textContent.trim() === label && b.getAttribute('data-state') === 'on')",
            arg=v['label'], timeout=3000)
        if not wait_stable(page):
            raise RuntimeError(f'variant {v["value"]}: DOM did not settle within 20s')
        vbody = page.evaluate(f"document.querySelector('{frame}').outerHTML")
        vname = f'{golden_name}.{v["value"]}'
        (OUT / f'{vname}.html').write_text(wrap(vname, vbody, '../golden.css'), encoding='utf-8', newline='\n')
        vinfo = page.evaluate(INFO_JS, frame)
        entry['variants'][v['value']] = {'label': v['label'], 'control': 'toggle-group-item', 'golden': f'{vname}.html',
                                         'surface': vinfo['surface']}
    page.set_viewport_size(VIEWPORT)
    return entry


def main(argv):
    from playwright.sync_api import sync_playwright
    extra = '--extra' in argv
    only = {a for a in argv if a != '--extra'}
    out_dir = OUT_EXTRA if extra else OUT_CHARTS
    out_dir.mkdir(parents=True, exist_ok=True)
    mpath = out_dir / 'manifest.json'
    manifest = json.loads(mpath.read_text(encoding='utf-8')) if (only and mpath.exists()) else {}
    srv = serve()
    base = f'http://127.0.0.1:{srv.server_address[1]}'
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=1)
        page = ctx.new_page()
        console = []
        page.on('pageerror', lambda e: console.append(f'pageerror: {e}'))
        page.on('console', lambda m: m.type == 'error' and console.append(f'console.error: {m.text}'))

        # The `chart` component example: body is the example wrapper, as the SSR goldens have it.
        if not extra and (not only or 'chart' in only):
            try:
                console.clear()
                load(page, base, 'chart')
                body = page.evaluate("document.getElementById('root').innerHTML")
                (OUT / 'chart.html').write_text(wrap('chart', body, 'golden.css'), encoding='utf-8', newline='\n')
                n = page.evaluate("document.querySelectorAll('svg.recharts-surface').length")
                print(f'chart: rendered ({n} chart surfaces)' + (f' [{"; ".join(console[:3])}]' if console else ''))
            except Exception as e:
                errors.append(f'chart: {e}')
                print(f'chart: ERROR {e}')

        for name, conf in ({} if extra else BLOCK_CHARTS).items():
            if only and name not in only:
                continue
            try:
                console.clear()
                entry = render_block_chart(page, base, name, conf)
                if console:
                    entry['consoleErrors'] = console[:5]
                manifest[name] = entry
                print(f'{name}: rendered+hover+{"+".join(entry["variants"])} {entry["width"]}x{entry["height"]} '
                      f'hover=({entry["hover"]["dx"]},{entry["hover"]["dy"]}) from the surface')
            except Exception as e:
                page.set_viewport_size(VIEWPORT)
                manifest[name] = {'group': 'blocks', 'error': str(e).split('\n')[0]}
                errors.append(f'{name}: {manifest[name]["error"]}')
                print(f'{name}: ERROR {manifest[name]["error"]}')

        page.goto(f'{base}/charts/harness.html?name=chart', wait_until='load')
        registry = page.evaluate('window.__extraCharts' if extra else 'window.__charts')
        names = [n for n in registry if not only or n in only]
        for name in names:
            meta = registry[name]
            entry = {'group': meta['group'], 'fullWidth': meta.get('fullWidth', False)}
            try:
                console.clear()
                load(page, base, name)
                frame = '[data-chart-frame]'
                info = page.evaluate(INFO_JS, frame)
                body = page.evaluate(f"document.querySelector('{frame}').outerHTML")
                golden_name = f'{out_dir.name}/{name}'
                (out_dir / f'{name}.html').write_text(wrap(golden_name, body, '../golden.css'), encoding='utf-8', newline='\n')
                entry.update(width=info['width'], height=info['height'], surface=info['surface'],
                             slots=info['slots'], rechartsClasses=info['rechartsClasses'], hover=None)
                status = 'rendered'
                if has_tooltip(name):
                    pt, note = hover_point(page)
                    if not pt:
                        raise RuntimeError(f'no hover point ({note})')
                    page.mouse.move(0, 0)
                    page.wait_for_timeout(50)
                    x, y = round(pt['x'], 1), round(pt['y'], 1)
                    if not (0 <= x < VIEWPORT['width'] and 0 <= y < VIEWPORT['height']):
                        raise RuntimeError(f'hover point outside viewport: {x},{y}')
                    page.mouse.move(x, y)
                    try:
                        page.wait_for_selector(TOOLTIP_SELECTOR, state='attached', timeout=3000)
                    except Exception:
                        raise RuntimeError(f'tooltip did not appear at {x},{y}')
                    wait_stable(page, quiet_ms=300, confirm_ms=300)
                    hbody = page.evaluate(f"document.querySelector('{frame}').outerHTML")
                    (out_dir / f'{name}.hover.html').write_text(
                        wrap(golden_name + '.hover', hbody, '../golden.css'), encoding='utf-8', newline='\n')
                    hinfo = page.evaluate(INFO_JS, frame)
                    entry['hover'] = {'x': x, 'y': y, 'kind': pt['kind'], 'target': pt.get('target'),
                                      'axis': pt.get('axis'), 'scrollY': 0,
                                      'tooltipSelector': TOOLTIP_SELECTOR, 'slots': hinfo['slots']}
                    if note:
                        entry['hover']['note'] = note
                    status = 'rendered+hover'
                if console:
                    entry['consoleErrors'] = console[:5]
                print(f'{name}: {status} {info["width"]}x{info["height"]}' + (f' hover=({entry["hover"]["x"]},{entry["hover"]["y"]})' if entry.get('hover') else ''))
            except Exception as e:
                entry['error'] = str(e).split('\n')[0]
                errors.append(f'{name}: {entry["error"]}')
                print(f'{name}: ERROR {entry["error"]}')
            manifest[name] = entry
        browser.close()
    srv.shutdown()
    mpath.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    rendered = sum(1 for m in manifest.values() if 'error' not in m)
    hovers = sum(1 for m in manifest.values() if m.get('hover'))
    tips = sum(1 for n in manifest if has_tooltip(n))
    print(f'\ncharts rendered: {rendered}/{len(manifest)}; hover goldens: {hovers}/{tips} charts with a ChartTooltip')
    for e in errors:
        print('  FAILED', e)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
