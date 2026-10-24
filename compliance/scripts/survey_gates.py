"""Run every page gate on the library's own pages: `python compliance/scripts/check_page.py --survey out.md`.

  blocks     the 27 shadcn blocks (login-01..05, signup-01..05, sidebar-01..16, dashboard-01), each against its own
             golden render as a Tier A page: A2, A5, B9, R9, forms, help text
  examples   every example page the library serves (examples index, dashboards, ported screens, the reference
             portfolio): the gates that need no original (B9, R9, forms, help text), and A2 and A5 too where the
             page names its original with <meta name="shadcn-nearest">

  --only blocks|examples   one group        --no-browser   skip A5, R9 and the rendered chart check
  --json out.json          also write the raw results

A gate that does not apply to a page (no named original, no chart, no marked form region) is "n/a", not a pass.
"""
import json
import pathlib
import sys
import time

from lxml import html as lxml_html

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_page as cp  # noqa: E402
import page_gates as pg  # noqa: E402

GATES = ['A2', 'A5', 'B9', 'R9', 'forms', 'placeholders', 'icon-buttons', 'native-titles', 'R16']


def block_names():
    return sorted(p.stem for p in (pg.GOLDEN / 'blocks').glob('*.html') if '.' not in p.stem)


def example_paths():
    from flask_basecoat.examples import ported_examples
    paths = ['/examples/', '/examples/two-factor', '/examples/notifications', '/examples/reference/portfolio']
    paths += [f'/examples/dashboards/{n}' for n in ('analytics', 'insights', 'marketing', 'overview', 'pipeline', 'sales')]
    paths += [f"/examples/{m['id']}" for m in ported_examples()]
    return paths


def status(lines):
    return {'status': 'fail' if lines else 'pass', 'count': len(lines), 'lines': [l[:300] for l in lines[:6]]}


NA = {'status': 'n/a', 'count': 0, 'lines': []}


def survey_page(base, name, path, nearest_hint, tier, browser):
    from playwright.sync_api import sync_playwright  # noqa: F401
    text, _ = cp.load(path)
    doc = lxml_html.fromstring(text)
    nearest = nearest_hint or cp.nearest_from_page(doc)
    original = lxml_html.fromstring(cp.golden_path(nearest).read_text(encoding='utf8')) if nearest and cp.golden_path(nearest) else None
    golden_rel = cp.golden_path(nearest).relative_to(cp.GOLDEN).as_posix() if original is not None else None
    url, golden_url = base + path, (f'{base}/basecoat/golden/{golden_rel}' if golden_rel else None)
    out = {'page': name, 'path': path, 'nearest': nearest, 'tier': tier, 'gates': {}}
    g = out['gates']

    if original is not None:
        fails, info = pg.check_structure(doc, original, cp.content_roots, tier)
        g['A2'] = status(fails)
        g['A2']['percent'] = info['percent']
        g['A2']['frame_percent'] = info['frame_percent']
    else:
        g['A2'] = dict(NA)

    if original is not None and browser:
        fails, info = pg.check_pixels(url, golden_url, tier)
        g['A5'] = status(fails)
        g['A5']['info'] = info
    else:
        g['A5'] = dict(NA)

    fails, info = pg.check_charts_static(doc)
    if info or fails:
        if browser:
            fails += pg.check_charts_rendered(url)
        g['B9'] = status(fails)
        g['B9']['charts'] = len(info)
    else:
        g['B9'] = dict(NA)

    if browser:
        fails, info = pg.check_a11y_strict(url, golden_url, pg.load_departures(doc))
        g['R9'] = status(fails)
        g['R9']['info'] = info
    else:
        g['R9'] = dict(NA)

    fails, found = pg.check_forms(doc)
    g['forms'] = status(fails)
    g['forms']['regions'] = found

    for k, v in pg.check_help_text(doc).items():
        g[k] = status(v)
    return out


def main(out_md, argv=None):
    argv = argv or sys.argv[1:]
    only = argv[argv.index('--only') + 1] if '--only' in argv else None
    browser = '--no-browser' not in argv
    rows = []
    t0 = time.time()
    with pg.local_server() as base:
        todo = []
        if only in (None, 'blocks'):
            todo += [(f'blocks/{b}', f'/basecoat/blocks/{b}', b, 'A') for b in block_names()]
        if only in (None, 'examples'):
            todo += [(p.removeprefix('/examples/') or 'index', p, None, 'B') for p in example_paths()]
        for name, path, nearest, tier in todo:
            try:
                rows.append(survey_page(base, name, path, nearest, tier, browser))
            except Exception as e:  # noqa: BLE001 - one page must not stop the survey
                rows.append({'page': name, 'path': path, 'error': f'{type(e).__name__}: {e}'[:300], 'gates': {}})
            print(f"{name}: " + ' '.join(f"{k}={v['status']}" for k, v in rows[-1]['gates'].items()) + (f" ERROR {rows[-1]['error']}" if 'error' in rows[-1] else ''), flush=True)
    out_json = argv[argv.index('--json') + 1] if '--json' in argv else None
    if out_json:
        pathlib.Path(out_json).write_text(json.dumps(rows, indent=1), encoding='utf8')
    pathlib.Path(out_md).write_text(markdown(rows, time.time() - t0), encoding='utf8')
    print(f'wrote {out_md}')
    return 0


def markdown(rows, seconds):
    lines = [f'# Gate survey ({len(rows)} pages, {seconds / 60:.1f} minutes)', '']
    for group, pick in (('Blocks', lambda r: r['page'].startswith('blocks/')), ('Example pages', lambda r: not r['page'].startswith('blocks/'))):
        sel = [r for r in rows if pick(r)]
        if not sel:
            continue
        lines += [f'## {group} ({len(sel)})', '', '| gate | pass | fail | n/a |', '|---|---|---|---|']
        for gate in GATES:
            c = {'pass': 0, 'fail': 0, 'n/a': 0}
            for r in sel:
                c[r['gates'].get(gate, NA)['status']] += 1
            lines.append(f'| {gate} | {c["pass"]} | {c["fail"]} | {c["n/a"]} |')
        lines.append('')
        lines += ['| page | ' + ' | '.join(GATES) + ' |', '|---|' + '---|' * len(GATES)]
        mark = {'pass': 'pass', 'fail': 'FAIL', 'n/a': '-'}
        for r in sel:
            cells = [mark[r['gates'].get(g, NA)['status']] + (f" ({r['gates'][g]['count']})" if r['gates'].get(g, NA)['status'] == 'fail' else '') for g in GATES]
            lines.append(f"| {r['page']} | " + ' | '.join(cells) + ' |' + (f" ERROR {r['error']}" if 'error' in r else ''))
        lines.append('')
    return '\n'.join(lines)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'survey.md'))
