"""Accessibility check: axe-core (WCAG 2.1 A/AA rules) on every component and block page, light and dark.

Usage: python compliance/scripts/check_a11y.py [name ...] [--json out.json]
A page passes when axe reports no violations. Rules that cannot apply to an isolated component page
(page-level landmarks and headings) are disabled.
"""
import json
import pathlib
import sys
import threading

from werkzeug.serving import make_server

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
GOLDEN = ROOT / 'compliance/golden/out'
AXE = ROOT / 'compliance/golden/node_modules/axe-core/axe.min.js'
DISABLED = ['region', 'landmark-one-main', 'page-has-heading-one', 'bypass']


def main(argv):
    out_json = None
    if '--json' in argv:
        i = argv.index('--json'); out_json = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    from playwright.sync_api import sync_playwright
    from flask_basecoat.testing import make_app
    app = make_app()
    srv = make_server('127.0.0.1', 0, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{srv.server_port}'
    comps = sorted(p.stem for p in GOLDEN.glob('*.html'))
    blocks = sorted(p.stem for p in (GOLDEN / 'blocks').glob('*.html'))
    targets = [('components', c) for c in comps] + [('blocks', b) for b in blocks]
    if argv:
        targets = [t for t in targets if t[1] in argv]
    axe_src = AXE.read_text(encoding='utf8')
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_context(viewport={'width': 1280, 'height': 900}).new_page()
        for kind, name in targets:
            entry = {'name': name, 'kind': kind, 'violations': {}}
            for mode in ('light', 'dark'):
                page.goto(f'{base}/basecoat/{kind}/{name}', wait_until='load')
                page.evaluate(f"document.documentElement.classList.toggle('dark', {str(mode == 'dark').lower()})")
                page.add_script_tag(content=axe_src)
                res = page.evaluate("""async (disabled) => {
                    const rules = {}; disabled.forEach((r) => { rules[r] = { enabled: false }; });
                    const r = await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] }, rules });
                    return r.violations.map((v) => ({ id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.slice(0, 3).map((n) => n.target.join(' ')) }));
                }""", DISABLED)
                entry['violations'][mode] = res
            entry['status'] = 'pass' if not any(entry['violations'].values()) else 'fail'
            results.append(entry)
            print(f"{'PASS' if entry['status'] == 'pass' else 'FAIL'} {kind}/{name}")
            for mode, vs in entry['violations'].items():
                for v in vs[:5]:
                    print(f"      [{mode}] {v['id']} ({v['impact']}): {v['help']} -> {v['nodes'][:2]}")
        browser.close()
    srv.shutdown()
    failed = sum(r['status'] != 'pass' for r in results)
    print(f'\n{len(results) - failed}/{len(results)} pass')
    if out_json:
        pathlib.Path(out_json).write_text(json.dumps(results, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
