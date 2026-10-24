"""DOM parity check: our rendered component page versus the upstream golden markup.

For a component the golden file is compliance/golden/out/<name>.html (the pinned upstream example
rendered by React) and ours is GET /basecoat/components/<name> from a bare Flask app that only has
the extension installed. Both documents are reduced to their data-slot elements in document order
and compared on tag, data-slot, class set and the state attributes Radix emits. Blocks use
compliance/golden/out/blocks/<name>.html and /basecoat/blocks/<name>, charts use
compliance/golden/out/charts/<name>.html and /basecoat/charts/<name>.

Pages that contain charts (the 70 chart pages and the `chart` component example) are also read from headless
Chromium after the runtime has drawn them, because the golden charts are browser renders, and the inside of
every .recharts-wrapper of the drawn page is compared with the golden: element tags, classes, text, and the geometry and
presentation attributes, numbers within 0.5px (see chart_compare.py). A chart that draws nothing fails.
A block whose chart has a browser golden (out/blocks/<name>.chart.html, e.g. dashboard-01) is also drawn at the block
viewport recorded in the charts manifest (1440x900), and its .recharts-wrapper is compared with that golden the same way.

Usage: python compliance/scripts/check_dom.py [name ...] [--json out.json]
Exit status is non-zero when any requested component differs.
"""
import json
import pathlib
import sys

from lxml import html as lxml_html

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
GOLDEN = ROOT / 'compliance/golden/out'

STATE_ATTRS = [
    'role', 'type', 'dir', 'tabindex', 'disabled', 'hidden', 'checked', 'inert',
    'aria-expanded', 'aria-selected', 'aria-checked', 'aria-pressed', 'aria-haspopup', 'aria-disabled',
    'aria-invalid', 'aria-orientation', 'aria-hidden', 'aria-current', 'aria-modal', 'aria-live',
    'aria-valuemin', 'aria-valuemax', 'aria-valuenow', 'aria-autocomplete', 'aria-multiselectable',
    'data-state', 'data-variant', 'data-size', 'data-side', 'data-align', 'data-orientation', 'data-inset',
    'data-active', 'data-collapsible', 'data-sidebar', 'data-disabled', 'data-placeholder', 'data-selected',
    'data-highlighted', 'data-checked', 'data-open', 'data-closed', 'data-vertical', 'data-horizontal',
    'data-mobile', 'data-collapsed', 'data-swipe-direction', 'data-type', 'data-position', 'data-indicator', 'data-spacing',
    'data-mode', 'data-status', 'data-visible', 'data-hidden', 'data-outside', 'data-today', 'data-selected-single',
    'data-range-start', 'data-range-end', 'data-range-middle', 'data-wrap', 'data-numbered', 'data-shortcut', 'data-shortcuts',
]
PRESENCE_ATTRS = ['id', 'href', 'aria-label', 'aria-labelledby', 'aria-describedby', 'aria-controls', 'placeholder', 'value', 'name', 'for', 'src', 'alt', 'style']
IGNORED_CLASS_PREFIXES = ()  # class sets are compared in full


_BROWSER = None


def chart_browser():
    global _BROWSER
    if _BROWSER is None:
        from chart_compare import ChartBrowser
        _BROWSER = ChartBrowser()
    return _BROWSER


def load_ours(kind, name, browser=False, viewport=None):
    if browser:
        # one shared browser for a whole run (main), or a short-lived one for a single check (tests)
        if _BROWSER is not None:
            status, text = _BROWSER.load(f'/basecoat/{kind}/{name}', viewport=viewport)
        else:
            from chart_compare import ChartBrowser
            b = ChartBrowser()
            try:
                status, text = b.load(f'/basecoat/{kind}/{name}', viewport=viewport)
            finally:
                b.close()
        return (text, None) if status == 200 else (None, f'HTTP {status}')
    from flask_basecoat.testing import make_app
    app = make_app()
    with app.test_client() as c:
        r = c.get(f'/basecoat/{kind}/{name}')
        if r.status_code != 200:
            return None, f'HTTP {r.status_code}'
        return r.get_data(as_text=True), None


PORTALED = ('-content', '-overlay', '-viewport')


def in_closed_portal(el):
    """True when el sits inside closed floating content. React portals those parts only while open, so the
    upstream static markup never contains them; ours keeps them in the DOM (hidden) for the runtime."""
    node = el
    while node is not None:
        if isinstance(node.tag, str):
            s = node.get('data-slot') or ''
            if node.get('data-state') == 'closed' and s.endswith(PORTALED) and not s.startswith(('accordion', 'collapsible', 'trace', 'tabs')):
                return True
            if s == 'toast-viewport' or s == 'toast':
                return True
        node = node.getparent()
    return False


def reduce(doc_text):
    doc = lxml_html.fromstring(doc_text)
    out = []
    for el in doc.iter():
        if not isinstance(el.tag, str):
            continue
        slot = el.get('data-slot')
        if slot is None:
            continue
        if in_closed_portal(el):
            continue
        rec = {'tag': el.tag.lower(), 'slot': slot, 'classes': sorted(set((el.get('class') or '').split()))}
        for a in STATE_ATTRS:
            if a in el.attrib:
                rec[a] = el.attrib[a]
        for a in PRESENCE_ATTRS:
            if a in el.attrib:
                rec[a] = '<set>'
        out.append(rec)
    return out


def diff(gold, ours):
    """Pair elements in order; return a list of human-readable differences."""
    problems = []
    n = max(len(gold), len(ours))
    for i in range(n):
        g = gold[i] if i < len(gold) else None
        o = ours[i] if i < len(ours) else None
        if g is None:
            problems.append(f'#{i}: extra element in ours <{o["tag"]} data-slot={o["slot"]}>')
            continue
        if o is None:
            problems.append(f'#{i}: missing element <{g["tag"]} data-slot={g["slot"]}>')
            continue
        if g['slot'] != o['slot'] or g['tag'] != o['tag']:
            problems.append(f'#{i}: golden <{g["tag"]} data-slot={g["slot"]}> vs ours <{o["tag"]} data-slot={o["slot"]}>')
            # do not try to compare attributes of mismatched elements
            continue
        gc, oc = set(g['classes']), set(o['classes'])
        if gc != oc:
            missing, extra = sorted(gc - oc), sorted(oc - gc)
            problems.append(f'#{i} {g["slot"]}: classes missing={missing} extra={extra}')
        for a in STATE_ATTRS + PRESENCE_ATTRS:
            if g.get(a) != o.get(a):
                problems.append(f'#{i} {g["slot"]}: {a} golden={g.get(a)!r} ours={o.get(a)!r}')
    return problems


def golden_path(kind, name):
    return GOLDEN / {'blocks': 'blocks', 'charts': 'charts'}.get(kind, '') / f'{name}.html'


def check(kind, name):
    gpath = golden_path(kind, name)
    if not gpath.exists():
        return {'name': name, 'kind': kind, 'status': 'no-golden'}
    golden_text = gpath.read_text(encoding='utf8')
    from chart_compare import has_drawn_chart
    charted = kind == 'charts' or has_drawn_chart(golden_text)
    # data-slot parts are compared on the server output, like every other page; the charts on the drawn page
    ours_text, err = load_ours(kind, name)
    if err:
        return {'name': name, 'kind': kind, 'status': 'page-error', 'error': err}
    gold = reduce(golden_text)
    ours = reduce(ours_text)
    problems = diff(gold, ours)
    if charted:
        from chart_compare import compare_wrappers
        drawn, err = load_ours(kind, name, browser=True)
        if err:
            return {'name': name, 'kind': kind, 'status': 'page-error', 'error': err}
        problems += compare_wrappers(golden_text, drawn, label='chart')[2]
    from chart_compare import block_chart
    bchart = block_chart(name) if kind == 'blocks' else None
    if bchart:
        # The block's SSR golden holds an empty Recharts shell; its chart is compared with the browser golden of the
        # chart (out/blocks/<name>.chart.html), our page drawn at the block viewport.
        from chart_compare import compare_wrappers
        drawn, err = load_ours(kind, name, browser=True, viewport=bchart['viewport'])
        if err:
            return {'name': name, 'kind': kind, 'status': 'page-error', 'error': err}
        chart_golden = (GOLDEN / bchart['golden']).read_text(encoding='utf8')
        problems += compare_wrappers(chart_golden, drawn, label='chart')[2]
    return {
        'name': name, 'kind': kind,
        'status': 'pass' if not problems else 'fail',
        'golden_elements': len(gold), 'our_elements': len(ours),
        'problems': problems,
    }


def all_names():
    comps = sorted(p.stem for p in GOLDEN.glob('*.html'))
    from chart_compare import block_names, chart_names
    blocks = block_names()
    return [('components', c) for c in comps] + [('blocks', b) for b in blocks] + [('charts', c) for c in chart_names()]


def kind_of(name):
    if name.startswith('chart-'):
        return 'charts'
    if name.split('-')[0] in ('dashboard', 'login', 'signup', 'sidebar') and name[-1].isdigit():
        return 'blocks'
    return 'components'


def main(argv):
    out_json = None
    if '--json' in argv:
        i = argv.index('--json')
        out_json = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    targets = all_names() if not argv else [(kind_of(n), n) for n in argv]
    if any(k == 'charts' or n == 'chart' for k, n in targets):
        chart_browser()
    try:
        results = [check(k, n) for k, n in targets]
    finally:
        if _BROWSER is not None:
            _BROWSER.close()
    failed = 0
    for r in results:
        mark = {'pass': 'PASS', 'fail': 'FAIL', 'no-golden': 'SKIP', 'page-error': 'ERR '}[r['status']]
        extra = ''
        if r['status'] in ('pass', 'fail'):
            extra = f" golden={r['golden_elements']} ours={r['our_elements']}"
        print(f"{mark} {r['kind']}/{r['name']}{extra}{(' ' + r.get('error', '')) if r.get('error') else ''}")
        for p in r.get('problems', [])[:25]:
            print('     ', p)
        if len(r.get('problems', [])) > 25:
            print(f"      ... {len(r['problems']) - 25} more")
        failed += r['status'] != 'pass'
    if out_json:
        pathlib.Path(out_json).write_text(json.dumps(results, indent=2))
    print(f"\n{len(results) - failed}/{len(results)} pass")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
