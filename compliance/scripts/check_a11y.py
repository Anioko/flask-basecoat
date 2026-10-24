"""Accessibility check: axe-core (WCAG 2.1 A/AA) on every component and block page, light and dark.

Pages are ports of the upstream examples, so the upstream golden page is audited the same way and a page
passes when it introduces no violation that upstream does not have: for every rule, our violation count must
not exceed the golden count. Rules that only apply to a whole document (landmarks, headings, skip links)
are disabled. Both lists are reported so upstream-origin findings stay visible.

Usage: python compliance/scripts/check_a11y.py [name ...] [--json out.json] [--strict]
--strict requires zero violations instead of parity with upstream.
"""
import json
import pathlib
import sys
import threading
from collections import Counter

from werkzeug.serving import make_server

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
GOLDEN = ROOT / 'compliance/golden/out'
AXE = ROOT / 'compliance/golden/node_modules/axe-core/axe.min.js'
DISABLED = ['region', 'landmark-one-main', 'page-has-heading-one', 'bypass']

AXE_RUN = """async (disabled) => {
    const rules = {}; disabled.forEach((r) => { rules[r] = { enabled: false }; });
    const r = await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] }, rules });
    return r.violations.map((v) => ({ id: v.id, impact: v.impact, help: v.help, count: v.nodes.length, nodes: v.nodes.slice(0, 60).map((n) => n.target.join(' ')) }));
}"""


def main(argv):
    out_json, strict = None, False
    if '--json' in argv:
        i = argv.index('--json'); out_json = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    if '--strict' in argv:
        strict = True; argv.remove('--strict')
    from playwright.sync_api import sync_playwright
    from flask import send_from_directory
    from flask_basecoat.testing import make_app
    app = make_app()

    @app.route('/golden/<path:path>')
    def golden(path):
        return send_from_directory(str(GOLDEN), path)

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

        def audit(url, mode):
            page.goto(base + url, wait_until='load')
            page.evaluate(f"document.documentElement.classList.toggle('dark', {str(mode == 'dark').lower()})")
            page.add_script_tag(content=axe_src)
            return page.evaluate(AXE_RUN, DISABLED)

        for kind, name in targets:
            entry = {'name': name, 'kind': kind, 'modes': {}}
            for mode in ('light', 'dark'):
                gold = audit(f'/golden/{"blocks/" if kind == "blocks" else ""}{name}.html', mode)
                ours = audit(f'/basecoat/{kind}/{name}', mode)
                gcount = Counter({v['id']: v['count'] for v in gold})
                ocount = Counter({v['id']: v['count'] for v in ours})
                regressions = [v for v in ours if (0 if strict else gcount.get(v['id'], 0)) < v['count']]
                entry['modes'][mode] = {'golden': gold, 'ours': ours, 'regressions': regressions}
            entry['status'] = 'pass' if not any(m['regressions'] for m in entry['modes'].values()) else 'fail'
            results.append(entry)
            upstream = sum(len(m['golden']) for m in entry['modes'].values())
            print(f"{'PASS' if entry['status'] == 'pass' else 'FAIL'} {kind}/{name} (upstream findings: {upstream})")
            for mode, m in entry['modes'].items():
                for v in m['regressions'][:5]:
                    print(f"      [{mode}] {v['id']} ({v['impact']}) x{v['count']}: {v['help']} -> {v['nodes'][:2]}")
        browser.close()
    srv.shutdown()
    failed = sum(r['status'] != 'pass' for r in results)
    print(f'\n{len(results) - failed}/{len(results)} pass')
    if out_json:
        pathlib.Path(out_json).write_text(json.dumps(results, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
