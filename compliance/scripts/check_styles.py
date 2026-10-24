"""Computed-style parity: our rendered pages versus the upstream golden pages, in a real browser.

Both documents are loaded in headless Chromium at the same viewport, in light and in dark mode. For every
data-slot element (paired in document order, like check_dom) a fixed list of computed CSS properties is read
and compared. Differences mean the stylesheet pipeline, the class set or the DOM diverge from upstream.
Closed floating content is skipped (it is not in the upstream static markup).

Chart pages (compliance/golden/out/charts/<name>.html against /basecoat/charts/<name>, and the `chart` component
example) are browser renders on the golden side, so our side is loaded with its runtime and read once the charts
are drawn. Besides the data-slot elements, every element inside each .recharts-wrapper (the SVG, the tooltip and
the legend) is paired in document order and its computed paint (fill, stroke, opacity, font, colour) and its box
relative to the wrapper are compared, light and dark.

Usage: python compliance/scripts/check_styles.py [name ...] [--json out.json] [--width 1280] [--props all]
"""
import json
import pathlib
import sys
import threading

from werkzeug.serving import make_server

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
GOLDEN = ROOT / 'compliance/golden/out'

PROPS = [
    'display', 'position', 'color', 'background-color', 'border-top-width', 'border-top-color', 'border-top-style', 'border-radius',
    'border-top-left-radius', 'border-bottom-right-radius', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
    'margin-top', 'margin-bottom', 'margin-left', 'margin-right', 'height', 'width', 'min-height', 'min-width', 'max-width', 'gap', 'row-gap', 'column-gap',
    'font-size', 'font-weight', 'line-height', 'letter-spacing', 'font-family', 'text-align', 'text-decoration-line', 'text-transform',
    'box-shadow', 'opacity', 'outline-style', 'outline-width', 'flex-direction', 'align-items', 'justify-content', 'flex-grow', 'flex-shrink',
    'overflow-x', 'overflow-y', 'cursor', 'white-space', 'transform', 'transition-property', 'visibility', 'z-index', 'grid-template-columns',
]
# Properties that legitimately depend on text metrics or layout width and are compared with tolerance.
NUMERIC_TOLERANCE_PX = 1.0

CHART_PROPS = ['display', 'visibility', 'fill', 'fill-opacity', 'stroke', 'stroke-width', 'stroke-opacity', 'stroke-dasharray',
               'opacity', 'color', 'background-color', 'border-top-color', 'border-top-width', 'border-top-style', 'font-size',
               'font-weight', 'font-family', 'text-anchor', 'dominant-baseline', 'mix-blend-mode', 'text-transform']
CHART_SCRIPT = """
(props) => {
  const out = [];
  document.querySelectorAll('.recharts-wrapper').forEach((w, wi) => {
    const wr = w.getBoundingClientRect();
    [w, ...w.querySelectorAll('*')].forEach((el) => {
      if (el.matches('style, script')) return;
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      const rec = { wrapper: wi, tag: el.tagName.toLowerCase(), cls: el.getAttribute('class') || '',
                    box: [r.left - wr.left, r.top - wr.top, r.width, r.height] };
      props.forEach((p) => { rec[p] = cs.getPropertyValue(p); });
      out.push(rec);
    });
  });
  return out;
}
"""
READY = """() => Array.from(document.querySelectorAll('[data-slot="chart"]')).every((c) => { const s = c.querySelector('svg.recharts-surface'); return s && s.getBoundingClientRect().width > 0; })"""

SCRIPT = """
(props) => {
  const skip = (el) => {
    let n = el;
    while (n) {
      const s = n.getAttribute && n.getAttribute('data-slot') || '';
      if (n.getAttribute && n.getAttribute('data-state') === 'closed' && /-(content|overlay|viewport)$/.test(s) && !/^(accordion|collapsible|trace|tabs)/.test(s)) return true;
      if (s === 'toast-viewport' || s === 'toast') return true;
      n = n.parentElement;
    }
    return false;
  };
  const out = [];
  document.querySelectorAll('[data-slot]').forEach((el) => {
    if (skip(el)) return;
    const cs = getComputedStyle(el);
    const rec = { slot: el.getAttribute('data-slot'), tag: el.tagName.toLowerCase(), rect: el.getBoundingClientRect().toJSON() };
    props.forEach((p) => { rec[p] = cs.getPropertyValue(p); });
    out.push(rec);
  });
  return out;
}
"""


class Server:
    def __init__(self):
        from flask import send_from_directory
        from flask_basecoat.testing import make_app
        app = make_app()

        @app.route('/golden/<path:path>')
        def golden(path):
            return send_from_directory(str(GOLDEN), path)

        self.srv = make_server('127.0.0.1', 0, app, threaded=True)
        self.port = self.srv.server_port
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.srv.shutdown()


import re

NUM = re.compile(r'-?\d+(?:\.\d+)?')
# Slots whose rendering is user-agent dependent (native option lists).
SKIP_SLOTS = {'native-select-option', 'native-select-optgroup'}


def px(v):
    try:
        return float(v.replace('px', ''))
    except Exception:
        return None


def numbers_close(a, b, tol):
    """Compare two strings token-wise, allowing |delta| <= tol on every number (colour-mix rounding noise)."""
    na, nb = NUM.findall(a), NUM.findall(b)
    if len(na) != len(nb) or NUM.sub('#', a) != NUM.sub('#', b):
        return False
    return all(abs(float(x) - float(y)) <= tol for x, y in zip(na, nb))


def compare(g, o):
    diffs = []
    if g.get('slot') in SKIP_SLOTS:
        return diffs
    for p in PROPS:
        a, b = g.get(p, ''), o.get(p, '')
        if a == b:
            continue
        na, nb = px(a), px(b)
        if na is not None and nb is not None and abs(na - nb) <= NUMERIC_TOLERANCE_PX:
            continue
        if numbers_close(a, b, 0.002 if 'color' in p or 'shadow' in p else NUMERIC_TOLERANCE_PX):
            continue
        if p == 'font-family':
            # same stack resolves identically; compare the first family only
            if a.split(',')[0].strip() == b.split(',')[0].strip():
                continue
        diffs.append(f'{p}: golden={a!r} ours={b!r}')
    return diffs


def has_drawn_chart(text):
    from chart_compare import has_drawn_chart as drawn
    return drawn(text)


def compare_chart(g, o):
    """Paint and box of one element inside a chart wrapper."""
    diffs = []
    if g['tag'] != o['tag'] or set(g['cls'].split()) != set(o['cls'].split()):
        return [f"element golden <{g['tag']} class=\"{g['cls']}\"> ours <{o['tag']} class=\"{o['cls']}\">"]
    for p in CHART_PROPS:
        a, b = g.get(p, ''), o.get(p, '')
        if a == b:
            continue
        na, nb = px(a), px(b)
        if na is not None and nb is not None and abs(na - nb) <= NUMERIC_TOLERANCE_PX:
            continue
        if numbers_close(a, b, 0.002 if 'color' in p or p in ('fill', 'stroke') else NUMERIC_TOLERANCE_PX):
            continue
        if p == 'font-family' and a.split(',')[0].strip() == b.split(',')[0].strip():
            continue
        diffs.append(f'{p}: golden={a!r} ours={b!r}')
    if any(abs(x - y) > NUMERIC_TOLERANCE_PX for x, y in zip(g['box'], o['box'])):
        diffs.append(f"box: golden={[round(v, 2) for v in g['box']]} ours={[round(v, 2) for v in o['box']]}")
    return diffs


def golden_url(kind, name):
    return f'/golden/{ {"blocks": "blocks/", "charts": "charts/"}.get(kind, "") }{name}.html'


def run(targets, width, out_json):
    from playwright.sync_api import sync_playwright
    server = Server()
    base = f'http://127.0.0.1:{server.port}'
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # The golden pages are React's static render (pre-hydration). Our pages are compared without their
        # runtime so both sides are the server output; behaviour is covered by check_runtime.py.
        ctx = browser.new_context(viewport={'width': width, 'height': 900}, device_scale_factor=1)
        page = ctx.new_page()
        page.route(lambda url: 'flask-basecoat.js' in url, lambda route: route.abort())
        # Chart goldens are browser renders: our chart pages are read with their runtime, on a second page.
        chart_page = ctx.new_page()
        for kind, name in targets:
            gpath = golden_url(kind, name)
            opath = f'/basecoat/{kind}/{name}'
            charted = kind == 'charts' or has_drawn_chart((GOLDEN / gpath[len('/golden/'):]).read_text(encoding='utf8'))
            entry = {'name': name, 'kind': kind, 'modes': {}}
            for mode in ('light', 'dark'):
                def grab(url, ours_side):
                    pg = chart_page if (charted and ours_side) else page
                    pg.goto(base + url, wait_until='load')
                    if charted and ours_side:
                        try:
                            pg.wait_for_function(READY, timeout=5000)
                        except Exception:  # noqa: BLE001 - an undrawn chart shows up as an element mismatch
                            pass
                    # Freeze transitions and animations so colours are sampled at their final values.
                    pg.add_style_tag(content='*, *::before, *::after { transition: none !important; animation: none !important; }')
                    pg.evaluate(f"document.documentElement.classList.toggle('dark', {str(mode == 'dark').lower()})")
                    pg.wait_for_timeout(100)
                    return pg.evaluate(SCRIPT, PROPS), (pg.evaluate(CHART_SCRIPT, CHART_PROPS) if charted else [])
                gold, gold_chart = grab(gpath, False)
                ours, ours_chart = grab(opath, True)
                problems = []
                n = max(len(gold), len(ours))
                for i in range(n):
                    g = gold[i] if i < len(gold) else None
                    o = ours[i] if i < len(ours) else None
                    if g is None or o is None or g['slot'] != o['slot']:
                        problems.append(f'#{i}: element mismatch golden={g and g["slot"]} ours={o and o["slot"]}')
                        continue
                    d = compare(g, o)
                    if d:
                        problems.append(f'#{i} {g["slot"]}: ' + '; '.join(d[:4]))
                if charted:
                    if len(gold_chart) != len(ours_chart):
                        problems.append(f'chart: golden has {len(gold_chart)} elements in its chart wrappers, ours {len(ours_chart)}')
                    for i, (g, o) in enumerate(zip(gold_chart, ours_chart)):
                        d = compare_chart(g, o)
                        if d:
                            problems.append(f"chart[{g['wrapper']}] #{i} <{g['tag']}>: " + '; '.join(d[:4]))
                            if d[0].startswith('element '):
                                break
                entry['modes'][mode] = {'elements': len(gold) + len(gold_chart), 'problems': problems}
            entry['status'] = 'pass' if not any(m['problems'] for m in entry['modes'].values()) else 'fail'
            results.append(entry)
            mark = 'PASS' if entry['status'] == 'pass' else 'FAIL'
            print(f"{mark} {kind}/{name} light={entry['modes']['light']['elements']} dark={entry['modes']['dark']['elements']}")
            for mode in ('light', 'dark'):
                for pr in entry['modes'][mode]['problems'][:6]:
                    print(f'      [{mode}] {pr}')
        browser.close()
    server.stop()
    failed = sum(r['status'] != 'pass' for r in results)
    print(f'\n{len(results) - failed}/{len(results)} pass')
    if out_json:
        pathlib.Path(out_json).write_text(json.dumps(results, indent=2))
    return 1 if failed else 0


def main(argv):
    out_json, width = None, 1280
    if '--json' in argv:
        i = argv.index('--json'); out_json = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    if '--width' in argv:
        i = argv.index('--width'); width = int(argv[i + 1]); argv = argv[:i] + argv[i + 2:]
    comps = sorted(p.stem for p in GOLDEN.glob('*.html'))
    blocks = sorted(p.stem for p in (GOLDEN / 'blocks').glob('*.html') if '.' not in p.stem)  # <name>.chart*.html are chart goldens
    charts = sorted(p.stem for p in (GOLDEN / 'charts').glob('chart-*.html') if not p.name.endswith('.hover.html'))
    targets = [('components', c) for c in comps] + [('blocks', b) for b in blocks] + [('charts', c) for c in charts]
    if argv:
        targets = [t for t in targets if t[1] in argv]
    return run(targets, width, out_json)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
