"""Anti-drift ratchet for templates and stylesheets.

Fails when a human-authored template or stylesheet contains anything the design system forbids:
  * raw Tailwind palette colours (bg-gray-100, text-blue-600, border-slate-200 ...) or hex/rgb/hsl literals
  * raw interactive elements (<button>, <input>, <select>, <textarea>) outside the component macros
  * legacy Basecoat class API (btn-primary, badge-outline ...) that no longer exists
Generated and pinned files (compliance/, the macro files themselves, icons) are out of scope.

Usage: python compliance/scripts/check_ratchet.py [--json out.json]
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

TEMPLATE_DIRS = [ROOT / 'app' / 'templates', ROOT / 'flask_basecoat' / 'templates']
CSS_FILES = [ROOT / 'app' / 'assets' / 'styles' / 'input.css', ROOT / 'app' / 'assets' / 'styles' / 'runtime.css',
             ROOT / 'flask_basecoat' / 'static' / 'css' / 'src' / 'flask-basecoat.css']
# Macro files render the raw elements by design.
MACRO_DIR = ROOT / 'flask_basecoat' / 'templates' / 'basecoat'

PALETTE = r'(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:50|[1-9]00|950)'
RAW_COLOR = re.compile(r'(?<![\w/-])(?:bg|text|border|ring|from|to|via|fill|stroke|divide|outline|shadow|decoration|accent|caret|placeholder)-' + PALETTE + r'\b|#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(')
RAW_ELEMENT = re.compile(r'<(button|input|select|textarea)\b', re.I)
LEGACY = re.compile(r'\b(?:btn|badge)-(?:primary|secondary|outline|ghost|link|destructive|sm|lg|icon)\b|\bbtn--|\bbtn\b(?!-)')
ALLOWED_RAW_ELEMENT = re.compile(r'type="hidden"|csrf_token|hidden_tag|data-fb-flash', re.I)


def scan_file(path):
    text = path.read_text(encoding='utf8', errors='ignore')
    problems = []
    for i, line in enumerate(text.splitlines(), 1):
        if 'data:image/svg+xml' in line or 'stroke="currentColor"' in line:
            pass
        for m in RAW_COLOR.finditer(line):
            # svg data URIs and oklch-free upstream tokens are not design drift
            if 'url(' in line and 'svg' in line:
                continue
            problems.append(f'{path.relative_to(ROOT)}:{i}: raw colour {m.group(0)!r}')
            break
        if path.suffix == '.html' and MACRO_DIR not in path.parents:
            m = RAW_ELEMENT.search(line)
            if m and not ALLOWED_RAW_ELEMENT.search(line):
                problems.append(f'{path.relative_to(ROOT)}:{i}: raw <{m.group(1).lower()}> outside the macros')
        if path.suffix == '.html' and LEGACY.search(line):
            problems.append(f'{path.relative_to(ROOT)}:{i}: legacy class API {LEGACY.search(line).group(0)!r}')
    return problems


def main(argv):
    out_json = None
    if '--json' in argv:
        i = argv.index('--json'); out_json = argv[i + 1]
    files = []
    for d in TEMPLATE_DIRS:
        files += sorted(d.rglob('*.html'))
    files += [f for f in CSS_FILES if f.exists()]
    results = {}
    total = 0
    for f in files:
        probs = scan_file(f)
        if probs:
            results[str(f.relative_to(ROOT))] = probs
            total += len(probs)
    for f, probs in results.items():
        print(f'FAIL {f} ({len(probs)})')
        for p in probs[:8]:
            print('     ', p)
    print(f'\n{len(files) - len(results)}/{len(files)} files clean, {total} findings')
    if out_json:
        pathlib.Path(out_json).write_text(json.dumps({'files': len(files), 'clean': len(files) - len(results), 'findings': results}, indent=2))
    return 1 if results else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
