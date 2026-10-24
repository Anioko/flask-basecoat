"""Recipe check: every data-slot element on a page carries exactly the class set its upstream recipe produces.

For each element with a data-slot the expected class set is computed the way the macro computes it: the
recipe's base classes, the cva option classes for the element's data-variant/data-size (or the options whose
classes are present when upstream emits no data-* mirror), merged with tailwind-merge semantics against the
caller's extra classes. The element passes when its class set equals that expectation, so a class that was
dropped, duplicated or hand-written outside the recipe is reported. Unknown slot names are reported too.

Usage: python compliance/scripts/check_recipes.py [name ...] [--json out.json] [--url /path ...]
"""
import json
import pathlib
import sys

from lxml import html as lxml_html

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from flask_basecoat import slots as S  # noqa: E402

GOLDEN = ROOT / 'compliance/golden/out'
UNCHECKED_SLOTS = {'example', 'example-wrapper', 'example-content', 'direction'}


def expected_for(el, slot_name):
    have = set((el.get('class') or '').split())
    kw = {}
    for cname, comp in S.COMPOSITES.items():
        if slot_name == comp['outer'] and comp['marker'] in have:
            slot_name = cname
    rec = S.recipe(slot_name, el.tag if el.tag != S.tag_for(slot_name, el.get('href')) else None)
    if not rec and slot_name not in S.VIRTUAL:
        return None, slot_name
    if el.tag != S.tag_for(slot_name, el.get('href')) and el.tag != 'svg':
        kw['tag'] = el.tag
    # asChild detection
    best = None
    for cand in ('button', 'sidebar-menu-button', 'sidebar-menu-sub-button', 'sidebar-menu-action', 'item', 'badge', 'card', 'label', 'toggle', 'marker', 'breadcrumb-link', 'navigation-menu-link'):
        crec = S.recipe(cand)
        cbase = set(crec.get('base_classes', '').split()) | set(((crec.get('variants') or {}).get('base', '')).split())
        cbase.discard('')
        if cbase and cbase <= have and (best is None or len(cbase) > best[1]):
            best = (cand, len(cbase))
    default_as = 'button' if slot_name in S.AS_BUTTON else None
    chosen_as = best[0] if best else None
    if chosen_as != default_as:
        kw['as_'] = chosen_as
    as_name = S.as_slot_for(slot_name, kw)
    groups = set(((rec.get('variants') or {}).get('variants') or {}).keys())
    if as_name:
        groups |= set(((S.recipe(as_name).get('variants') or {}).get('variants') or {}).keys())
    for g in groups | {'variant', 'size', 'spacing'}:
        if el.get(f'data-{g}') is not None and not (slot_name == 'sidebar' and g == 'collapsible'):
            kw[g] = el.get(f'data-{g}')
    for source in (rec, S.recipe(as_name) if as_name else {}):
        for g, options in ((source.get('variants') or {}).get('variants') or {}).items():
            if g in kw:
                continue
            default = (source.get('variants') or {}).get('defaults', {}).get(g)
            scored = sorted(((len(set(c.split()) & have) / len(c.split()), o) for o, c in options.items() if c.split()), reverse=True)
            if scored and scored[0][0] >= 0.5:
                if scored[0][1] != default:
                    kw[g] = scored[0][1]
            else:
                kw[g] = None
    if el.tag == 'svg':
        icon = next((c[len('lucide-'):] for c in have if c.startswith('lucide-')), None)
        if icon:
            kw['icon'] = icon
    base_want, _ = S.classes_for(slot_name, kw)
    base_set = set(base_want)
    if el.tag == 'svg':
        base_set |= {'lucide', f"lucide-{kw.get('icon', S.SVG_ICON.get(slot_name, 'square'))}"}
    extra = [c for c in (el.get('class') or '').split() if c not in base_set]
    want, _ = S.classes_for(slot_name, kw, ' '.join(extra))
    want = set(want)
    if el.tag == 'svg':
        want |= {'lucide', f"lucide-{kw.get('icon', S.SVG_ICON.get(slot_name, 'square'))}"}
    return want, slot_name


def check_html(text, label):
    doc = lxml_html.fromstring(text)
    problems, checked = [], 0
    for el in doc.iter():
        if not isinstance(el.tag, str):
            continue
        slot_name = el.get('data-slot')
        if not slot_name or slot_name in UNCHECKED_SLOTS:
            continue
        want, resolved = expected_for(el, slot_name)
        if want is None:
            problems.append(f'unknown slot {slot_name!r} (no upstream recipe)')
            continue
        have = set((el.get('class') or '').split())
        if have != want:
            problems.append(f'{resolved}: missing={sorted(want - have)[:6]} extra={sorted(have - want)[:6]}')
        checked += 1
    return {'name': label, 'status': 'pass' if not problems else 'fail', 'checked': checked, 'problems': problems}


def check_page(kind, name):
    from flask_basecoat.testing import make_app
    app = make_app()
    with app.test_client() as c:
        r = c.get(f'/basecoat/{kind}/{name}')
    if r.status_code != 200:
        return {'name': f'{kind}/{name}', 'status': 'page-error', 'error': f'HTTP {r.status_code}'}
    return check_html(r.get_data(as_text=True), f'{kind}/{name}')


def main(argv):
    out_json = None
    if '--json' in argv:
        i = argv.index('--json'); out_json = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    comps = sorted(p.stem for p in GOLDEN.glob('*.html'))
    blocks = sorted(p.stem for p in (GOLDEN / 'blocks').glob('*.html'))
    targets = [('components', c) for c in comps] + [('blocks', b) for b in blocks]
    if argv:
        targets = [t for t in targets if t[1] in argv]
    results = [check_page(k, n) for k, n in targets]
    failed = 0
    for r in results:
        mark = {'pass': 'PASS', 'fail': 'FAIL', 'page-error': 'ERR '}[r['status']]
        print(f"{mark} {r['name']} {r.get('checked', '')} {r.get('error', '')}".rstrip())
        for p in r.get('problems', [])[:20]:
            print('     ', p)
        failed += r['status'] != 'pass'
    if out_json:
        pathlib.Path(out_json).write_text(json.dumps(results, indent=2))
    print(f"\n{len(results) - failed}/{len(results)} pass")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
