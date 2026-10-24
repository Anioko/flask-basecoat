"""Generate the chart specs and chart pages.

Inputs:  compliance/recipes/charts/<name>.json (extracted from the upstream charts) and the golden pages
         compliance/golden/out/charts/<name>.html, compliance/golden/out/chart.html
Outputs: flask_basecoat/data/charts/<name>.json            runtime spec of every upstream chart
         flask_basecoat/data/charts/chart-example-<n>.json the six charts of the `chart` component example
         flask_basecoat/templates/basecoat/pages/charts/<name>.html
         flask_basecoat/templates/basecoat/pages/components/chart.html

The card around each chart is ported from the golden DOM with the page generator (scripts/gen_pages.py), so it is
made of the card macros; the chart itself becomes ``ui.chart_from_spec(chart_spec(name), ...)``. Each chart page
defines a ``card()`` macro (used by the charts index) and renders it inside the canonical width frame.

Usage: python scripts/gen_chart_pages.py [name ...]
"""
import copy
import json
import pathlib
import re
import sys

from lxml import etree, html as lxml_html

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
import gen_pages as GP  # noqa: E402
from flask_basecoat import charts as C  # noqa: E402

RECIPES = ROOT / 'compliance' / 'recipes' / 'charts'
GOLDEN = ROOT / 'compliance' / 'golden' / 'out'
PAGES = ROOT / 'flask_basecoat' / 'templates' / 'basecoat' / 'pages'
DATA = C.DATA_DIR

MONTHS6 = [('January', 186, 80), ('February', 305, 200), ('March', 237, 120), ('April', 73, 190), ('May', 209, 130), ('June', 214, 140)]
SLICE3 = {'$fn': 'slice', 'start': 0, 'end': 3}
DM = {'desktop': {'label': 'Desktop', 'color': 'var(--chart-1)'}, 'mobile': {'label': 'Mobile', 'color': 'var(--chart-2)'}}
BROWSERS = {'visitors': {'label': 'Visitors'}, 'chrome': {'label': 'Chrome', 'color': 'var(--chart-1)'}, 'safari': {'label': 'Safari', 'color': 'var(--chart-2)'},
            'firefox': {'label': 'Firefox', 'color': 'var(--chart-3)'}, 'edge': {'label': 'Edge', 'color': 'var(--chart-4)'}, 'other': {'label': 'Other', 'color': 'var(--chart-5)'}}

# The six charts of compliance/upstream/shadcn/radix/examples/chart-example.tsx, written as specs.
EXAMPLE_SPECS = [
    {'component': 'AreaChart', 'config': {'desktop': DM['desktop']},
     'data': [{'month': m, 'desktop': d} for m, d, _ in MONTHS6],
     'props': {'accessibilityLayer': True, 'margin': {'left': 12, 'right': 12}},
     'series': [{'component': 'Area', 'dataKey': 'desktop', 'type': 'natural', 'fill': 'var(--color-desktop)', 'fillOpacity': 0.4, 'stroke': 'var(--color-desktop)'}],
     'axes': [{'component': 'XAxis', 'dataKey': 'month', 'tickLine': False, 'axisLine': False, 'tickMargin': 8, 'tickFormatter': SLICE3}],
     'grid': {'component': 'CartesianGrid', 'vertical': False}, 'tooltip': {'cursor': False, 'indicator': 'line'}, 'legend': None, 'labels': []},
    {'component': 'BarChart', 'config': DM,
     'data': [{'month': m, 'desktop': d, 'mobile': mo} for m, d, mo in MONTHS6],
     'props': {'accessibilityLayer': True},
     'series': [{'component': 'Bar', 'dataKey': 'desktop', 'fill': 'var(--color-desktop)', 'radius': 4},
                {'component': 'Bar', 'dataKey': 'mobile', 'fill': 'var(--color-mobile)', 'radius': 4}],
     'axes': [{'component': 'XAxis', 'dataKey': 'month', 'tickLine': False, 'tickMargin': 10, 'axisLine': False, 'tickFormatter': SLICE3}],
     'grid': {'component': 'CartesianGrid', 'vertical': False}, 'tooltip': {'cursor': False, 'indicator': 'dashed'}, 'legend': None, 'labels': []},
    {'component': 'LineChart', 'config': DM,
     'data': [{'month': m, 'desktop': d, 'mobile': mo} for m, d, mo in MONTHS6],
     'props': {'accessibilityLayer': True, 'margin': {'left': 12, 'right': 12}},
     'series': [{'component': 'Line', 'dataKey': 'desktop', 'type': 'monotone', 'stroke': 'var(--color-desktop)', 'strokeWidth': 2, 'dot': False},
                {'component': 'Line', 'dataKey': 'mobile', 'type': 'monotone', 'stroke': 'var(--color-mobile)', 'strokeWidth': 2, 'dot': False}],
     'axes': [{'component': 'XAxis', 'dataKey': 'month', 'tickLine': False, 'axisLine': False, 'tickMargin': 8, 'tickFormatter': SLICE3}],
     'grid': {'component': 'CartesianGrid', 'vertical': False}, 'tooltip': {'cursor': False}, 'legend': None, 'labels': []},
    {'component': 'PieChart', 'config': BROWSERS,
     'data': [{'browser': b, 'visitors': v, 'fill': f'var(--color-{b})'} for b, v in (('chrome', 275), ('safari', 200), ('firefox', 287), ('edge', 173), ('other', 190))],
     'props': {},
     'series': [{'component': 'Pie', 'dataKey': 'visitors', 'nameKey': 'browser', 'innerRadius': 60, 'strokeWidth': 5,
                 'labels': [{'content': {'$fn': 'centerText', 'dominantBaseline': 'middle', 'lines': [
                     {'value': {'sum': 'visitors'}, 'className': 'fill-foreground text-3xl font-bold', 'dy': 0},
                     {'value': {'text': 'Visitors'}, 'className': 'fill-muted-foreground', 'dy': 24}]}}]}],
     'axes': [], 'grid': None, 'tooltip': {'cursor': False, 'hideLabel': True}, 'legend': None, 'labels': []},
    {'component': 'RadialBarChart', 'config': {'visitors': {'label': 'Visitors'}, 'safari': {'label': 'Safari', 'color': 'var(--chart-2)'}},
     'data': [{'browser': 'safari', 'visitors': 1260, 'fill': 'var(--color-safari)'}],
     'props': {'endAngle': 100, 'innerRadius': 64, 'outerRadius': 94},
     'series': [{'component': 'RadialBar', 'dataKey': 'visitors', 'background': True}],
     'axes': [{'component': 'PolarRadiusAxis', 'tick': False, 'tickLine': False, 'axisLine': False,
               'labels': [{'content': {'$fn': 'centerText', 'dominantBaseline': 'middle', 'lines': [
                   {'value': {'pick': 'visitors', 'index': 0}, 'className': 'fill-foreground text-4xl font-bold', 'dy': 0},
                   {'value': {'text': 'Visitors'}, 'className': 'fill-muted-foreground', 'dy': 24}]}}]}],
     'grid': {'component': 'PolarGrid', 'gridType': 'circle', 'radialLines': False, 'stroke': 'none', 'className': 'first:fill-muted last:fill-background', 'polarRadius': [86, 74]},
     'tooltip': None, 'legend': None, 'labels': []},
    {'component': 'RadarChart', 'config': DM,
     'data': [{'month': m, 'desktop': d, 'mobile': mo} for m, d, mo in MONTHS6],
     'props': {},
     'series': [{'component': 'Radar', 'dataKey': 'desktop', 'fill': 'var(--color-desktop)', 'fillOpacity': 0.6},
                {'component': 'Radar', 'dataKey': 'mobile', 'fill': 'var(--color-mobile)'}],
     'axes': [{'component': 'PolarAngleAxis', 'dataKey': 'month'}],
     'grid': {'component': 'PolarGrid'}, 'tooltip': {'cursor': False, 'indicator': 'line'}, 'legend': None, 'labels': []},
]
EXAMPLE_CONTAINERS = [None, None, None, 'mx-auto aspect-square max-h-[250px]', 'mx-auto aspect-square max-h-[210px]', 'mx-auto aspect-square max-h-[250px]']


def q(s):
    return GP.q(s)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf8', newline='\n')


def placeholder(i):
    return f'<span data-chart-placeholder="{i}"></span>'


def chart_call(spec_name, chart_id, cls):
    kw = f", class={q(cls)}" if cls else ''
    return f"{{{{ ui.chart_from_spec(chart_spec({q(spec_name)}), id={q(chart_id)}{kw}) }}}}"


def chart_class(el):
    """Classes of the golden chart element beyond the ChartContainer recipe (the chart's own className)."""
    from flask_basecoat import slots as S
    want, _ = S.classes_for('chart', {})
    return ' '.join(c for c in (el.get('class') or '').split() if c not in set(want))


def select_content_block(control, chart_id, state):
    items = []
    initial = state
    for it in control['items']:
        checked = ', checked=true' if it['value'] == initial else ''
        cls = it.get('className') or ''
        if it.get('swatch'):
            inner = (f'<div class="flex items-center gap-2 text-xs"><span class="flex h-3 w-3 shrink-0 rounded-xs" '
                     f'style="background-color: {it["swatch"]};"></span>{it["label"]}</div>')
            items.append(f"{{% call ui.select_item(value={q(it['value'])}, class={q(cls)}{checked}) %}}{inner}{{% endcall %}}")
        else:
            items.append(f"{{{{ ui.select_item(text={q(it['label'])}, value={q(it['value'])}, class={q(cls)}{checked}) }}}}")
    content = control.get('content') or {}
    kw = [f"class={q(content.get('className') or '')}"]
    if content.get('align'):
        kw.append(f"align={q(content['align'])}")
    return f"{{% call ui.select_content({', '.join(kw)}) %}}{''.join(items)}{{% endcall %}}"


def port(root_el, replacements):
    """Render an lxml subtree to Jinja with the page generator, then put the chart calls in."""
    ctx = {}
    out = GP.render_node(root_el, 1, ctx)
    for marker, text in replacements.items():
        if marker not in out:
            raise RuntimeError(f'marker {marker} lost in the port')
        out = out.replace(marker, text)
    return out


def chart_page(name):
    recipe = json.loads((RECIPES / f'{name}.json').read_text(encoding='utf8'))
    spec = C.runtime_spec(recipe)
    write(DATA / f'{name}.json', json.dumps(spec, indent=1, ensure_ascii=False) + '\n')
    doc = lxml_html.fromstring((GOLDEN / 'charts' / f'{name}.html').read_text(encoding='utf8'))
    frame = doc.find('body')[0]
    preview = frame[0]
    card = preview[0]
    chart_el = next(e for e in card.iter() if isinstance(e.tag, str) and e.get('data-slot') == 'chart')
    chart_id = recipe['chart']['container'].get('id') or name[len('chart-'):]
    reps = {placeholder(0): chart_call(name, chart_id, chart_class(chart_el))}
    marker = etree.fromstring(placeholder(0))
    marker.tail = chart_el.tail
    chart_el.getparent().replace(chart_el, marker)
    inter = recipe.get('interactive') or {}
    state = (inter.get('runtime') or {}).get('state') or {}
    for ci, control in enumerate(inter.get('controls') or []):
        if control['component'] == 'Select':
            trig = next(e for e in card.iter() if isinstance(e.tag, str) and e.get('data-slot') == 'select-trigger')
            sname = control['value']['state']
            trig.set('data-chart-control', f'chart-{chart_id}')
            trig.set('data-chart-state', sname)
            m = f'<span data-select-placeholder="{ci}"></span>'
            node = etree.fromstring(m)
            node.tail = trig.tail
            trig.tail = None
            trig.addnext(node)
            reps[m] = select_content_block(control, chart_id, state.get(sname))
        elif control['component'] == 'button':
            buttons = [e for e in card.iter() if isinstance(e.tag, str) and e.tag == 'button' and e.get('data-active') is not None]
            for b, item in zip(buttons, control['repeat']):
                b.set('type', 'button')
                b.set('data-chart-control', f'chart-{chart_id}')
                b.set('data-chart-state', 'activeChart')
                b.set('data-chart-value', item['value'])
    body = port(card, reps)
    width = frame.get('style')
    kind = frame.get('data-chart-frame')
    page = (
        "{% extends 'basecoat/pages/_layout.html' %}\n"
        "{% import 'basecoat/index.html' as ui %}\n"
        f"{{# Port of the upstream shadcn/ui chart `{name}` (pinned source in compliance/upstream/shadcn/charts). #}}\n"
        f"{{% block title %}}{name} · Flask-Basecoat{{% endblock %}}\n"
        "{% macro card() -%}\n" + body + "\n{%- endmacro %}\n"
        "{% block body %}\n"
        f'<div data-chart-frame="{kind}" style="{width}"><div class="bg-background *:data-[slot=card]:has-[[data-slot=chart]]:shadow-none">{{{{ card() }}}}</div></div>\n'
        "{% endblock %}\n"
    )
    write(PAGES / 'charts' / f'{name}.html', GP.compact(page))


def example_page():
    for i, spec in enumerate(EXAMPLE_SPECS):
        write(DATA / f'chart-example-{i + 1}.json', json.dumps(C.finish_spec(copy.deepcopy(spec)), indent=1, ensure_ascii=False) + '\n')
    doc = lxml_html.fromstring((GOLDEN / 'chart.html').read_text(encoding='utf8'))
    body = doc.find('body')
    charts = [e for e in body.iter() if isinstance(e.tag, str) and e.get('data-slot') == 'chart']
    reps = {}
    for i, el in enumerate(charts):
        reps[placeholder(i)] = chart_call(f'chart-example-{i + 1}', f'example-{i + 1}', chart_class(el))
        marker = etree.fromstring(placeholder(i))
        marker.tail = el.tail
        el.getparent().replace(el, marker)
    parts = []
    for ch in body:
        if isinstance(ch.tag, str) and ch.tag == 'div' and set(GP.classes_of(ch)) == {'w-full', 'bg-muted', 'dark:bg-background'} and len(ch) == 1 and ch[0].get('data-slot') == 'example-wrapper':
            parts.append(GP.render_node(ch[0], 1, {}))
        elif isinstance(ch.tag, str):
            parts.append(GP.render_node(ch, 1, {}))
    inner = ''.join(parts)
    for k, v in reps.items():
        inner = inner.replace(k, v)
    page = (
        "{% extends 'basecoat/pages/_layout.html' %}\n"
        "{% import 'basecoat/index.html' as ui %}\n"
        "{# Port of the upstream shadcn/ui example `chart` (pinned source in compliance/upstream). #}\n"
        "{% block title %}chart · Flask-Basecoat{% endblock %}\n"
        "{% block body %}\n" + inner + "{% endblock %}\n"
    )
    write(PAGES / 'components' / 'chart.html', GP.compact(page))


def main(argv):
    names = [a for a in argv if not a.startswith('--')]
    allnames = sorted(p.stem for p in RECIPES.glob('chart-*.json'))
    targets = [n for n in allnames if not names or n in names]
    for n in targets:
        chart_page(n)
    if not names or 'chart' in names:
        example_page()
    print(json.dumps({'charts': len(targets), 'unresolved': sorted(set(GP.report['unresolved']))[:20]}))


if __name__ == '__main__':
    main(sys.argv[1:])
