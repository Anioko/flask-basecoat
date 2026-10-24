"""Chart parity helpers shared by check_dom, check_runtime and check_styles.

Recharts only draws once it has measured its container, so the golden chart pages were taken in a browser
(see compliance/CHARTS-GOLDEN.md). Our chart pages are drawn by the runtime, so they are also read from a
browser. This module

  * serves our app and the golden directory on a local port and loads pages in headless Chromium
    (``ChartBrowser``), waiting until every ``[data-slot=chart]`` has drawn its ``svg.recharts-surface``;
  * reduces every ``.recharts-wrapper`` subtree (the SVG plus the tooltip and legend wrappers) to a flat list of
    element records and compares two such lists (``compare_wrappers``): element tags, class sets, text,
    and the geometry and presentation attributes. Numbers inside attributes (``x``, ``y``, ``width``, ``height``,
    ``cx``, ``cy``, ``r``, ``x1``..``y2``, path ``d``, ``points``, ``transform``, ``stroke-dasharray``) are parsed and
    compared with a tolerance of ``TOLERANCE_PX``; everything else must match exactly.

A chart page with an empty wrapper (no ``svg.recharts-surface``) never passes: the golden always has one.
"""
import pathlib
import re
import sys
import threading

from lxml import html as lxml_html

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
GOLDEN = ROOT / 'compliance/golden/out'
CHARTS = GOLDEN / 'charts'

TOLERANCE_PX = 0.5
NUMERIC_ATTRS = ['x', 'y', 'width', 'height', 'cx', 'cy', 'r', 'x1', 'y1', 'x2', 'y2', 'rx', 'ry']
PATH_ATTRS = ['d', 'points', 'transform', 'stroke-dasharray']
EXACT_ATTRS = ['fill', 'stroke', 'fill-opacity', 'stroke-opacity', 'stroke-width', 'opacity', 'text-anchor',
               'dominant-baseline', 'alignment-baseline', 'dy', 'dx', 'font-size', 'font-weight', 'viewbox', 'role',
               'orientation', 'radius']
NUM = re.compile(r'-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?', re.I)


def chart_names():
    """The 70 chart pages, in name order (hover pages excluded)."""
    return sorted(p.stem for p in CHARTS.glob('chart-*.html') if not p.name.endswith('.hover.html'))


def block_names():
    """The block goldens (out/blocks/<name>.html); the browser goldens of block charts (<name>.chart*.html) excluded."""
    return sorted(p.stem for p in (GOLDEN / 'blocks').glob('*.html') if '.' not in p.stem)


def block_chart(name):
    """The manifest entry of the chart inside block <name> (browser golden out/blocks/<name>.chart.html), or None.

    Keys used by the checks: viewport, golden (base page), hover {dx, dy relative to the chart surface, golden},
    state, initial, variants {<value>: {label, golden}}. See compliance/CHARTS-GOLDEN.md."""
    import json
    mpath = CHARTS / 'manifest.json'
    if not (GOLDEN / 'blocks' / f'{name}.chart.html').exists() or not mpath.exists():
        return None
    entry = json.loads(mpath.read_text(encoding='utf8')).get(f'blocks/{name}')
    return entry if entry and 'error' not in entry else None


SURFACE = re.compile(r'<svg[^>]*\brecharts-surface\b')


def has_drawn_chart(html_text):
    """True when the page holds a drawn chart (an <svg class="recharts-surface">), not just a ChartContainer."""
    return bool(SURFACE.search(html_text))


def tokens(value):
    """Split an attribute value into (shape, numbers): the text with numbers replaced by '#', and the numbers."""
    v = re.sub(r'\s+', ' ', value.strip())
    return NUM.sub('#', v).replace(' ', '').replace(',', ''), [float(n) for n in NUM.findall(v)]


def _direct_text(el):
    parts = [el.text or '']
    return re.sub(r'\s+', ' ', ''.join(parts)).strip()


def reduce_wrapper(wrapper):
    """Flatten one .recharts-wrapper subtree into records, in document order."""
    out = []
    for el in wrapper.iter():
        if not isinstance(el.tag, str):
            continue
        tag = el.tag.lower()
        if tag in ('style', 'script'):
            continue
        rec = {'tag': tag, 'classes': sorted(set((el.get('class') or '').split())), 'text': _direct_text(el), 'attrs': {}}
        if el.get('data-chart-spec') is not None:
            continue
        for a in NUMERIC_ATTRS + PATH_ATTRS + EXACT_ATTRS:
            if a in el.attrib:
                rec['attrs'][a] = el.attrib[a]
        out.append(rec)
    return out


def wrappers_of(doc_text):
    doc = lxml_html.fromstring(doc_text)
    return [el for el in doc.iter() if isinstance(el.tag, str) and 'recharts-wrapper' in (el.get('class') or '').split()]


def compare_records(g, o, where):
    problems = []
    if g['tag'] != o['tag'] or g['classes'] != o['classes']:
        problems.append(f'{where}: golden <{g["tag"]} class="{" ".join(g["classes"])}"> vs ours <{o["tag"]} class="{" ".join(o["classes"])}">')
        return problems
    if g['text'] != o['text']:
        problems.append(f'{where} <{g["tag"]}>: text golden={g["text"]!r} ours={o["text"]!r}')
    for a in sorted(set(g['attrs']) | set(o['attrs'])):
        gv, ov = g['attrs'].get(a), o['attrs'].get(a)
        if gv == ov:
            continue
        if gv is None or ov is None:
            problems.append(f'{where} <{g["tag"]}>: {a} golden={gv!r} ours={ov!r}')
            continue
        if a in NUMERIC_ATTRS or a in PATH_ATTRS:
            gs, gn = tokens(gv)
            os_, on = tokens(ov)
            if gs == os_ and len(gn) == len(on) and all(abs(x - y) <= TOLERANCE_PX for x, y in zip(gn, on)):
                continue
            short = lambda s: s if len(s) <= 120 else s[:117] + '...'  # noqa: E731
            problems.append(f'{where} <{g["tag"]}>: {a} golden={short(re.sub(chr(10), " ", gv))!r} ours={short(re.sub(chr(10), " ", ov))!r}')
        else:
            problems.append(f'{where} <{g["tag"]}>: {a} golden={gv!r} ours={ov!r}')
    return problems


def compare_wrappers(golden_text, ours_text, label='chart'):
    """Compare every .recharts-wrapper of two documents. Returns (golden_count, our_count, problems)."""
    gw, ow = wrappers_of(golden_text), wrappers_of(ours_text)
    problems = []
    if len(gw) != len(ow):
        problems.append(f'{label}: golden has {len(gw)} chart wrapper(s), ours {len(ow)}')
    for wi, (g, o) in enumerate(zip(gw, ow)):
        gr, orr = reduce_wrapper(g), reduce_wrapper(o)
        drawn = lambda recs: any(r['tag'] == 'svg' and 'recharts-surface' in r['classes'] for r in recs)  # noqa: E731
        if drawn(gr) and not drawn(orr):
            problems.append(f'{label}[{wi}]: no svg.recharts-surface drawn (golden has {len(gr)} elements, ours {len(orr)})')
            continue
        if len(gr) != len(orr):
            problems.append(f'{label}[{wi}]: golden has {len(gr)} elements inside the wrapper, ours {len(orr)}')
        for i in range(min(len(gr), len(orr))):
            p = compare_records(gr[i], orr[i], f'{label}[{wi}] #{i}')
            problems.extend(p)
            if p and (gr[i]['tag'] != orr[i]['tag'] or gr[i]['classes'] != orr[i]['classes']):
                # structure diverged: later pairs are meaningless
                problems.append(f'{label}[{wi}]: stopped comparing after the first structural difference')
                break
    return len(gw), len(ow), problems


def tooltip_html(doc_text):
    """The open tooltip content (.recharts-tooltip-wrapper .cn-chart-tooltip) of every wrapper, reduced."""
    out = []
    for w in wrappers_of(doc_text):
        tips = [el for el in w.iter() if isinstance(el.tag, str) and 'recharts-tooltip-wrapper' in (el.get('class') or '').split()]
        for t in tips:
            out.append({'classes': sorted(set((t.get('class') or '').split())), 'style': t.get('style') or '',
                        'records': reduce_wrapper(t), 'text': re.sub(r'\s+', ' ', t.text_content()).strip()})
    return out


TRANSLATE = re.compile(r'translate\(\s*(-?[\d.]+)px,\s*(-?[\d.]+)px\)')


def compare_tooltips(golden_text, ours_text, label='tooltip'):
    """Tooltip DOM, text, visibility and position (translate within TOLERANCE_PX) of the hover pages."""
    g, o = tooltip_html(golden_text), tooltip_html(ours_text)
    problems = []
    if len(g) != len(o):
        problems.append(f'{label}: golden has {len(g)} tooltip wrapper(s), ours {len(o)}')
    for i, (a, b) in enumerate(zip(g, o)):
        if a['classes'] != b['classes']:
            problems.append(f'{label}[{i}]: wrapper classes golden={a["classes"]} ours={b["classes"]}')
        gvis = 'visibility: visible' in a['style']
        ovis = 'visibility: visible' in b['style']
        if gvis != ovis:
            problems.append(f'{label}[{i}]: golden visible={gvis} ours visible={ovis}')
        gt, ot = TRANSLATE.search(a['style']), TRANSLATE.search(b['style'])
        if bool(gt) != bool(ot):
            problems.append(f'{label}[{i}]: transform golden={gt and gt.group(0)} ours={ot and ot.group(0)}')
        elif gt and ot:
            if any(abs(float(x) - float(y)) > TOLERANCE_PX for x, y in zip(gt.groups(), ot.groups())):
                problems.append(f'{label}[{i}]: position golden={gt.group(0)} ours={ot.group(0)}')
        if a['text'] != b['text']:
            problems.append(f'{label}[{i}]: text golden={a["text"]!r} ours={b["text"]!r}')
        ra, rb = a['records'], b['records']
        if len(ra) != len(rb):
            problems.append(f'{label}[{i}]: golden tooltip has {len(ra)} elements, ours {len(rb)}')
        for j in range(min(len(ra), len(rb))):
            p = compare_records(ra[j], rb[j], f'{label}[{i}] #{j}')
            problems.extend(p)
            if p and (ra[j]['tag'] != rb[j]['tag'] or ra[j]['classes'] != rb[j]['classes']):
                break
    return problems


READY_JS = """() => {
  const charts = Array.from(document.querySelectorAll('[data-slot="chart"]'));
  return charts.every((c) => { const s = c.querySelector('svg.recharts-surface'); return s && s.getBoundingClientRect().width > 0; });
}"""


class ChartBrowser:
    """Our app plus /golden/<path> on a local port, and one Chromium page at the canonical 1280x900 viewport."""

    def __init__(self, width=1280, height=900):
        from flask import send_from_directory
        from playwright.sync_api import sync_playwright
        from werkzeug.serving import make_server
        import logging
        from flask_basecoat.testing import make_app
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        app = make_app()

        @app.route('/golden/<path:path>')
        def golden(path):
            return send_from_directory(str(GOLDEN), path)

        self.srv = make_server('127.0.0.1', 0, app, threaded=True)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f'http://127.0.0.1:{self.srv.server_port}'
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch()
        self.viewport = {'width': width, 'height': height}
        self.ctx = self.browser.new_context(viewport=dict(self.viewport), device_scale_factor=1)
        self.page = self.ctx.new_page()
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(f'pageerror: {e}'))
        self.page.on('console', lambda m: self.errors.append(f'console.{m.type}: {m.text}') if m.type == 'error' and 'favicon' not in m.text else None)

    def load(self, path, settle_ms=150, viewport=None):
        """Open a page of ours (at `viewport` when given, else the browser's own), wait for its charts, return (status, html)."""
        self.errors.clear()
        want = viewport or self.viewport
        if self.page.viewport_size != want:
            self.page.set_viewport_size(want)
        resp = self.page.goto(self.base + path, wait_until='load')
        if resp is None or resp.status != 200:
            return (resp.status if resp else 0), ''
        try:
            self.page.wait_for_function(READY_JS, timeout=5000)
        except Exception:  # noqa: BLE001 - an undrawn chart is reported by the comparison
            pass
        self.page.wait_for_timeout(settle_ms)
        return 200, self.page.content()

    def close(self):
        try:
            self.browser.close()
            self._pw.stop()
        finally:
            self.srv.shutdown()
