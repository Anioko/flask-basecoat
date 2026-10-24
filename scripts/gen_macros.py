"""Generate the thin Jinja macro files for every shadcn/ui registry component.

Each macro is one upstream part (data-slot): it calls ``slot()`` (flask_basecoat.slots) for the tag,
class recipe and state attributes, and renders ``text`` or the ``{% call %}`` body as children.
Files are only written when missing unless --force is given, so hand-written refinements survive.
Also (re)writes the barrel ``basecoat/index.html`` and the shipped ``flask_basecoat/data/recipes.json``.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RECIPES_DIR = ROOT / 'compliance' / 'recipes'
TEMPLATES = ROOT / 'flask_basecoat' / 'templates' / 'basecoat'
DATA = ROOT / 'flask_basecoat' / 'data'
sys.path.insert(0, str(ROOT))

FORCE = '--force' in sys.argv


def snake(slot):
    return slot.replace('-', '_')


def load_recipes():
    merged, per = {}, {}
    for p in sorted(RECIPES_DIR.glob('*.json')):
        d = json.loads(p.read_text(encoding='utf8'))
        per[d['name']] = d
        for s, rec in d['slots'].items():
            if ':' in s:
                continue
            # the component file whose name prefixes the slot owns it (input-group owns input-group-button, not combobox)
            if s not in merged or (s.startswith(d['name'] + '-') or s == d['name']) and not merged[s]['component_name'] in (d['name'],) and not (s.startswith(merged[s]['component_name'] + '-') or s == merged[s]['component_name']):
                merged[s] = {**rec, 'component_name': d['name']}
    return merged, per


def macro_source(slot_name, rec, void, virtual):
    name = snake(slot_name)
    comp = rec.get('component', '')
    if virtual:
        return (
            f"{{#- {comp}: renders no element upstream; a display:contents wrapper groups the parts for the runtime. -#}}\n"
            f"{{% macro {name}(class='', id=none, attrs={{}}) -%}}\n"
            f"{{%- set s = slot('{slot_name}', kwargs, class, id, attrs) -%}}\n"
            f"<div{{{{ s.attributes }}}}>{{{{ caller() if caller }}}}</div>\n"
            f"{{%- endmacro %}}\n"
        )
    if void:
        return (
            f"{{#- {comp} -#}}\n"
            f"{{% macro {name}(class='', id=none, attrs={{}}) -%}}\n"
            f"{{%- set s = slot('{slot_name}', kwargs, class, id, attrs) -%}}\n"
            f"<{{{{ s.tag }}}}{{{{ s.attributes }}}}>\n"
            f"{{%- endmacro %}}\n"
        )
    return (
        f"{{#- {comp} -#}}\n"
        f"{{% macro {name}(text='', class='', id=none, attrs={{}}) -%}}\n"
        f"{{%- set s = slot('{slot_name}', kwargs, class, id, attrs) -%}}\n"
        f"<{{{{ s.tag }}}}{{{{ s.attributes }}}}>{{{{ s.inner }}}}{{{{ text }}}}{{{{ caller() if caller }}}}</{{{{ s.tag }}}}>\n"
        f"{{%- endmacro %}}\n"
    )


def main():
    from flask_basecoat import slots as S
    merged, per = load_recipes()
    DATA.mkdir(exist_ok=True)
    (DATA / 'recipes.json').write_text(json.dumps(merged, indent=1, sort_keys=True), encoding='utf8')
    S.RECIPES.clear(); S.RECIPES.update(merged)

    written, kept = [], []
    exports = []
    for comp_name, d in sorted(per.items()):
        path = TEMPLATES / f'{comp_name}.html'
        slots_here = [s for s in d['slots'] if ':' not in s]
        header = (f"{{# {comp_name}: port of shadcn/ui {d['source'].split('/')[-1]} (pinned in compliance/upstream). "
                  f"Macros: {', '.join(snake(s) for s in slots_here)} #}}\n")
        body = [header]
        for s in slots_here:
            rec = d['slots'][s]
            void = S.tag_for(s) in S.VOID
            body.append(macro_source(s, rec, void, s in S.VIRTUAL))
            exports.append((comp_name, snake(s)))
        src = '\n'.join(body)
        if path.exists() and not FORCE:
            kept.append(comp_name)
        else:
            path.write_text(src, encoding='utf8')
            written.append(comp_name)

    # barrel
    lines = ['{# Barrel: every shadcn/ui component macro. Usage: {% import "basecoat/index.html" as ui %} then {{ ui.button(text="Save") }} #}']
    for comp_name in sorted(per):
        names = [snake(s) for s in per[comp_name]['slots'] if ':' not in s]
        if not names:
            continue
        alias = '_' + snake(comp_name)
        lines.append(f"{{% import 'basecoat/{comp_name}.html' as {alias} %}}")
        for n in names:
            lines.append(f"{{% set {n} = {alias}.{n} %}}")
    lines.append("{% import 'basecoat/_example.html' as _ex %}{% set example = _ex.example %}{% set example_wrapper = _ex.example_wrapper %}")
    lines.append("{% import 'basecoat/wtforms.html' as _wt %}{% set render_field = _wt.render_field %}{% set render_form = _wt.render_form %}{% set field_errors = _wt.field_errors %}")
    (TEMPLATES / 'index.html').write_text('\n'.join(lines) + '\n', encoding='utf8')
    print(f'written {len(written)} macro files, kept {len(kept)}, {len(exports)} macros exported')


if __name__ == '__main__':
    main()
