"""Concatenate the runtime core and every component module into flask_basecoat/static/js/flask-basecoat.js.

Order: core.js first, then components alphabetically. No bundler is required; each module is an IIFE
that registers itself with window.FlaskBasecoat.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'flask_basecoat' / 'static' / 'js' / 'src'
OUT = ROOT / 'flask_basecoat' / 'static' / 'js' / 'flask-basecoat.js'


RUNTIME_ICONS = ['check', 'circle', 'x', 'chevron-down', 'chevron-up', 'chevron-right', 'chevron-left', 'minus', 'loader-circle',
                 'search', 'circle-check', 'info', 'triangle-alert', 'octagon-x', 'ellipsis', 'chevrons-up-down']


def icons_module():
    import json
    import sys
    sys.path.insert(0, str(ROOT))
    from flask_basecoat.icons import svg
    icons = {name: str(svg(name, 'size-4', aria_hidden='true')) for name in RUNTIME_ICONS}
    header = '/* ---- icons (generated from flask_basecoat/icons.py) ---- */'
    return header + '\nwindow.FlaskBasecoatIcons = ' + json.dumps(icons) + ';\n'


def main():
    parts = [(SRC / 'core.js').read_text(encoding='utf8'), icons_module()]
    for p in sorted((SRC / 'components').glob('*.js')):
        parts.append(f'\n/* ---- {p.stem} ---- */\n' + p.read_text(encoding='utf8'))
    OUT.write_text('\n'.join(parts), encoding='utf8')
    print(f'{OUT.relative_to(ROOT)}: {OUT.stat().st_size} bytes, {len(parts) - 1} component modules')


if __name__ == '__main__':
    main()
