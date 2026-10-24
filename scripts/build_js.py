"""Concatenate the runtime core and every component module into flask_basecoat/static/js/flask-basecoat.js.

Order: core.js first, then components alphabetically. No bundler is required; each module is an IIFE
that registers itself with window.FlaskBasecoat.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'flask_basecoat' / 'static' / 'js' / 'src'
OUT = ROOT / 'flask_basecoat' / 'static' / 'js' / 'flask-basecoat.js'


def main():
    parts = [(SRC / 'core.js').read_text(encoding='utf8')]
    for p in sorted((SRC / 'components').glob('*.js')):
        parts.append(f'\n/* ---- {p.stem} ---- */\n' + p.read_text(encoding='utf8'))
    OUT.write_text('\n'.join(parts), encoding='utf8')
    print(f'{OUT.relative_to(ROOT)}: {OUT.stat().st_size} bytes, {len(parts) - 1} component modules')


if __name__ == '__main__':
    main()
