"""DOM parity check: our rendered component page versus the upstream golden markup.

For a component the golden file is compliance/golden/out/<name>.html (the pinned upstream example
rendered by React) and ours is GET /basecoat/components/<name> from a bare Flask app that only has
the extension installed. Both documents are reduced to their data-slot elements in document order
and compared on tag, data-slot, class set and the state attributes Radix emits. Blocks use
compliance/golden/out/blocks/<name>.html and /basecoat/blocks/<name>.

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
    'data-mobile', 'data-collapsed', 'data-swipe-direction', 'data-type', 'data-position', 'data-indicator',
]
PRESENCE_ATTRS = ['id', 'href', 'aria-label', 'aria-labelledby', 'aria-describedby', 'aria-controls', 'placeholder', 'value', 'name', 'for', 'src', 'alt', 'style']
IGNORED_CLASS_PREFIXES = ()  # class sets are compared in full


def load_ours(kind, name):
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


def check(kind, name):
    gpath = GOLDEN / ('blocks' if kind == 'blocks' else '') / f'{name}.html'
    if not gpath.exists():
        return {'name': name, 'kind': kind, 'status': 'no-golden'}
    ours_text, err = load_ours(kind, name)
    if err:
        return {'name': name, 'kind': kind, 'status': 'page-error', 'error': err}
    gold = reduce(gpath.read_text(encoding='utf8'))
    ours = reduce(ours_text)
    problems = diff(gold, ours)
    return {
        'name': name, 'kind': kind,
        'status': 'pass' if not problems else 'fail',
        'golden_elements': len(gold), 'our_elements': len(ours),
        'problems': problems,
    }


def all_names():
    comps = sorted(p.stem for p in GOLDEN.glob('*.html'))
    blocks = sorted(p.stem for p in (GOLDEN / 'blocks').glob('*.html'))
    return [('components', c) for c in comps] + [('blocks', b) for b in blocks]


def main(argv):
    out_json = None
    if '--json' in argv:
        i = argv.index('--json')
        out_json = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    targets = all_names() if not argv else [(('blocks' if n.split('-')[0] in ('dashboard', 'login', 'signup', 'sidebar') and n[-1].isdigit() else 'components'), n) for n in argv]
    results = [check(k, n) for k, n in targets]
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
