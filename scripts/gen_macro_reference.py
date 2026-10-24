"""Generate docs/MACROS.md: one entry per shadcn/ui component with every macro (part), its variant options, the state
arguments it understands, and real usage lines taken from the component's upstream example port.

The reference is generated from the same data the macros render with (flask_basecoat/data/recipes.json and
flask_basecoat/slots.py), so it cannot drift from what the macros emit. Run: python scripts/gen_macro_reference.py
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flask_basecoat import slots as S  # noqa: E402

RECIPES = json.loads((ROOT / 'flask_basecoat/data/recipes.json').read_text(encoding='utf8'))
PAGES = ROOT / 'flask_basecoat/templates/basecoat/pages'
MACROS = ROOT / 'flask_basecoat/templates/basecoat'
REGISTRY = json.loads((ROOT / 'compliance/upstream/shadcn/registry/index.json').read_text(encoding='utf8'))


def snake(slot):
    return slot.replace('-', '_')


def macro_names(component):
    f = MACROS / f'{component}.html'
    if not f.exists():
        return []
    return re.findall(r'\{% macro ([a-z_]+)\(', f.read_text(encoding='utf8'))


def slot_for_macro(name):
    return name.replace('_', '-')


def variants(slot):
    rec = RECIPES.get(slot) or {}
    cva = rec.get('variants') or {}
    out = {}
    for group, options in (cva.get('variants') or {}).items():
        out[group] = (list(options), (cva.get('defaults') or {}).get(group))
    return out


def states(slot):
    st = []
    rec = RECIPES.get(slot) or {}
    groups = set(((rec.get('variants') or {}).get('variants') or {}))
    for d in rec.get('data_attrs') or []:
        key = d[len('data-'):] if d.startswith('data-') else d
        if key not in groups and key not in ('slot', 'state'):
            st.append(f'{key.replace("-", "_")}= (sets {d})')
    if slot in S.OPEN_SLOTS:
        st.append('open=true|false')
    if slot in S.CHECKED_SLOTS:
        st.append('checked=true|false')
    if slot in S.PRESSED_SLOTS:
        st.append('pressed=true|false')
    if slot in S.ACTIVE_SLOTS:
        st.append('active=true (the selected tab), value=')
    if slot in S.ACTIVE_FLAG_SLOTS:
        st.append('active=true|false')
    if slot in S.LINK_SLOTS:
        st.append('href= (renders an <a>)')
    if slot in getattr(S, 'AS_BUTTON', {}):
        st.append("as_=<slot> (asChild: render as another part, e.g. as_='sidebar-menu-button'); variant/size of Button")
    return st


def usage_lines(component, names, limit=4):
    """Shortest distinct calls of the component's macros in its upstream example port."""
    f = PAGES / 'components' / f'{component}.html'
    if not f.exists():
        return []
    text = re.sub(r'<svg.*?</svg>', '', f.read_text(encoding='utf8'), flags=re.S)
    found = []
    for n in names:
        calls = re.findall(r'\{\{ ui\.' + n + r'\([^{}]*?\) \}\}|\{% call ui\.' + n + r'\([^{}%]*?\) %\}', text)
        calls = [c for c in calls if 'radix-' not in c and '_R_' not in c]
        if calls:
            found.append(min(calls, key=len))
        if len(found) >= limit:
            break
    return found


# Macros the library adds to shadcn's set. They are not upstream components, so their entries are written here.
LIBRARY_ADDITIONS = '''## harvey_ball

A Harvey ball for a comparison table cell (R20): a 16px inline SVG, no chart runtime. The ring and the wedge use the
foreground token. Live example: `/basecoat/components/harvey-ball`.

| Macro | Arguments | Renders |
|---|---|---|
| `ui.harvey_ball(value)` | `value`: 0, 25, 50, 75 or 100 (anything else raises `ValueError`); `class=`, `id=` | `<svg role="img" aria-label="75 per cent" data-harvey-ball data-value="75">` |

```jinja
{% call ui.table_cell(class='text-center') %}{{ ui.harvey_ball(75) }}{% endcall %}
```

## document

The reading layout for long-form documents (R17): the blog detail screen's column, a cover, and the body that the
print stylesheet (`app/assets/styles/print.css`, part of the library CSS build) turns into a PDF. Live example:
`/examples/document/solution-document`; print it or save it as PDF.

| Macro | Arguments | Renders |
|---|---|---|
| `ui.document()` | `class=`, `attrs=`; takes children | the blog detail column (`mx-auto max-w-4xl px-6 py-12`), marked `data-document` |
| `ui.document_cover(title, organisation, date, version, author)` | all five required; `class=`, `id=`, `attrs=` | the title block on screen and page 1 in print: version badge, organisation, title (h1), author and date |
| `ui.document_body()` | `class=`, `attrs=`; takes children | the article, marked `data-document-body`; every `h2` inside the document starts a page |
| `ui.document_title_style(title)` | the title | the value of `<html style="...">` that sets `--document-title`, the running header in print |

```jinja
{% call ui.document() %}
  {{ ui.document_cover(title='Claims Platform Modernisation', organisation='Harbourline', date='24 October 2026', version='1.2', author='Amara Okafor') }}
  {% call ui.document_body() %}
    <section class="space-y-6"><h2 class="text-foreground text-2xl font-bold">Executive summary</h2> ... </section>
  {% endcall %}
{% endcall %}
```

On the page: `<html class="print-a4">` or `<html class="print-letter">` (A4 is the default) and
`<html style="{{ ui.document_title_style(title) }}">`. In print the running header is the title (not on page 1), the footer
reads "Page n of m", each `h2` starts a page, charts, figures, tables and cards are kept whole and fit the column, the
light tokens apply whatever the screen theme, navigation, sidebars, buttons and toasts are hidden, and links print their
text only. Chart series stay apart in greyscale through a dash per line series, a hollow marker on every second line
series and an outline per bar series; give each series a `labelList` so its value is also text.
'''


def main():
    components = sorted(i['name'] for i in REGISTRY if i.get('type') == 'registry:ui')
    out = ['# Flask-Basecoat macro reference', '',
           'Generated by `scripts/gen_macro_reference.py` from the recipes the macros render with. Import every macro with',
           "`{% import 'basecoat/index.html' as ui %}`. Every macro takes `text=`, `class=` (merged with tailwind-merge rules),",
           '`id=` and `attrs={...}`, plus the variant and state arguments listed. Call with `{% call ui.x() %}...{% endcall %}`',
           'to pass children. The live example of each component is at `/basecoat/components/<name>`; compare it with the',
           'upstream render at `/basecoat/compare/<name>`.', '']
    for comp in components:
        names = macro_names(comp)
        if not names:
            continue
        out.append(f'## {comp}')
        out.append('')
        out.append('| Macro | Part (`data-slot`) | Variants (default first) | State and other arguments |')
        out.append('|---|---|---|---|')
        for n in names:
            slot = slot_for_macro(n)
            v = variants(slot)
            vtxt = '; '.join(f"{g}: " + ', '.join(([d] if d in opts else []) + [o for o in opts if o != d]) for g, (opts, d) in v.items()) or ''
            stxt = '; '.join(states(slot))
            virtual = ' (groups its parts; renders no element)' if slot in S.VIRTUAL else ''
            out.append(f'| `ui.{n}` | `{slot}`{virtual} | {vtxt} | {stxt} |')
        ex = usage_lines(comp, names)
        if ex:
            out.append('')
            out.append('From the upstream example:')
            out.append('')
            out.append('```jinja')
            out += ex
            out.append('```')
        out.append('')
    out += LIBRARY_ADDITIONS
    (ROOT / 'docs').mkdir(exist_ok=True)
    (ROOT / 'docs' / 'MACROS.md').write_text('\n'.join(out) + '\n', encoding='utf8')
    print(f'docs/MACROS.md: {len(components)} components')


if __name__ == '__main__':
    main()
