"""Run every shadcn/ui compliance check and write the report.

Checks (each is a standalone script under compliance/scripts):
  coverage   every registry component and block has a macro file, a page and a barrel export
  dom        rendered pages match the upstream golden DOM (data-slot elements, classes, state attributes)
  recipes    every data-slot element carries exactly its upstream class recipe (tailwind-merge aware)
  tokens     the tokens shipped in the stylesheet equal the upstream neutral theme, light and dark
  ratchet    templates and stylesheets contain no raw colours, raw controls or legacy class API
  styles     computed styles equal the golden pages in headless Chromium, light and dark (--browser)
  a11y       axe-core: no accessibility regressions against the upstream pages (--browser)
  runtime    pages load without script errors; popups, tabs, toggles behave like Radix (--browser)
  tests      the pytest suite

Usage: python scripts/shadcn_compliance.py [--browser] [--json compliance/REPORT.json]
Exit status is non-zero when any check fails.
"""
import json
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'compliance' / 'scripts'
PY = sys.executable


def run(cmd, timeout=1800):
    t = time.time()
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding='utf8', errors='replace', timeout=timeout)
    out = (p.stdout or '') + (p.stderr or '')
    return p.returncode, out, round(time.time() - t, 1)


def summary_line(out):
    m = re.findall(r'^(\d+)/(\d+) (?:pass|files clean.*)$', out, re.M)
    if m:
        a, b = m[-1]
        return f'{a}/{b}'
    m = re.search(r'(\d+) passed', out)
    if m:
        return f'{m.group(1)} passed' + (f", {re.search(r'(\d+) failed', out).group(1)} failed" if 'failed' in out else '')
    return out.strip().splitlines()[-1][:80] if out.strip() else ''


def check_tokens():
    """Compare the tokens compiled into the shipped stylesheet with the upstream neutral theme."""
    neutral = json.loads((ROOT / 'compliance/upstream/shadcn/neutral.json').read_text(encoding='utf8'))['cssVars']
    css = (ROOT / 'flask_basecoat/static/css/flask-basecoat.min.css').read_text(encoding='utf8')

    def norm(v):
        v = v.strip().replace(' ', '')
        v = re.sub(r'(\d+(?:\.\d+)?)%', lambda m: str(float(m.group(1)) / 100).rstrip('0').rstrip('.'), v)
        v = re.sub(r'(?<![\d.])0?\.(\d+)', r'0.\1', v)
        return v

    problems = []
    for mode, selector in (('light', ':root'), ('dark', '.dark')):
        block = re.search(re.escape(selector) + r'\{([^}]*)\}', css)
        if not block:
            problems.append(f'{mode}: no {selector} block in the shipped stylesheet')
            continue
        found = dict(re.findall(r'--([\w-]+):([^;]+)', block.group(1)))
        for k, v in neutral[mode].items():
            if k not in found:
                problems.append(f'{mode}: --{k} missing')
            elif norm(found[k]) != norm(v):
                problems.append(f'{mode}: --{k} is {found[k].strip()!r}, upstream {v!r}')
    return {'status': 'pass' if not problems else 'fail', 'problems': problems, 'compared': sum(len(neutral[m]) for m in ('light', 'dark'))}


def main(argv):
    browser = '--browser' in argv
    out_json = ROOT / 'compliance' / 'REPORT.json'
    if '--json' in argv:
        out_json = pathlib.Path(argv[argv.index('--json') + 1])
    report = {'generated': time.strftime('%Y-%m-%d %H:%M:%S'), 'checks': {}}
    steps = [
        ('coverage', [PY, '-m', 'pytest', 'tests/test_shadcn_components.py', '-q', '-k', 'covered or barrel', '-p', 'no:cacheprovider']),
        ('dom', [PY, str(SCRIPTS / 'check_dom.py')]),
        ('recipes', [PY, str(SCRIPTS / 'check_recipes.py')]),
        ('ratchet', [PY, str(SCRIPTS / 'check_ratchet.py')]),
    ]
    if browser:
        steps += [
            ('styles', [PY, str(SCRIPTS / 'check_styles.py')]),
            ('a11y', [PY, str(SCRIPTS / 'check_a11y.py')]),
            ('runtime', [PY, str(SCRIPTS / 'check_runtime.py')]),
        ]
    steps.append(('tests', [PY, '-m', 'pytest', 'tests', '-q', '-p', 'no:cacheprovider']))

    tokens = check_tokens()
    report['checks']['tokens'] = tokens
    print(f"{'PASS' if tokens['status'] == 'pass' else 'FAIL'} tokens ({tokens['compared']} variables)")
    for p in tokens['problems'][:10]:
        print('      ', p)

    for name, cmd in steps:
        code, out, secs = run(cmd)
        status = 'pass' if code == 0 else 'fail'
        report['checks'][name] = {'status': status, 'summary': summary_line(out), 'seconds': secs, 'output_tail': out.strip().splitlines()[-40:]}
        print(f"{'PASS' if status == 'pass' else 'FAIL'} {name}: {summary_line(out)} ({secs}s)")
        if status != 'pass':
            for line in [l for l in out.strip().splitlines() if l.startswith(('FAIL', 'ERR', '      ', 'FAILED'))][:15]:
                print('      ', line[:160])
    failed = [n for n, c in report['checks'].items() if c['status'] != 'pass']
    report['status'] = 'pass' if not failed else 'fail'
    out_json.write_text(json.dumps(report, indent=2), encoding='utf8')
    print(f"\n{'ALL CHECKS PASS' if not failed else 'FAILED: ' + ', '.join(failed)}  -> {out_json.relative_to(ROOT)}")
    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
