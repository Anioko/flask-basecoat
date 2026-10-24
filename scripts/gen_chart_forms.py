"""Generate the chart specs of the forms shadcn has no original for (rulings R18 and R19).

Outputs: flask_basecoat/data/charts/chart-scatter-default.json   a plain scatter chart (R18)
         flask_basecoat/data/charts/chart-matrix-two-by-two.json value against cost, split in four (R18)
         flask_basecoat/data/charts/chart-bar-waterfall.json     a cost bridge (R19)

The Recharts oracles these specs are checked against are compliance/golden/charts/extra/*.tsx (same data, same
element props); their browser renders are compliance/golden/out/charts-extra/. Keep the data here and in the
oracles identical. The waterfall's offsets, labels and total are computed from its steps, so the total always
equals the sum of the steps.

Run from the repo root:  python scripts/gen_chart_forms.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flask_basecoat.charts import DATA_DIR, finish_spec  # noqa: E402

# ---------------------------------------------------------------- scatter, default

SCATTER_DATA = [
    {'cost': 60, 'value': 82}, {'cost': 90, 'value': 68}, {'cost': 150, 'value': 74}, {'cost': 280, 'value': 88},
    {'cost': 300, 'value': 76}, {'cost': 250, 'value': 62}, {'cost': 30, 'value': 22}, {'cost': 70, 'value': 35},
    {'cost': 280, 'value': 30}, {'cost': 220, 'value': 18},
]


def scatter_default():
    return {
        'type': 'scatter', 'component': 'ScatterChart',
        'config': {'value': {'label': 'Value', 'color': 'var(--chart-1)'}},
        'data': SCATTER_DATA,
        'props': {'accessibilityLayer': True, 'margin': {'left': 12, 'right': 12}},
        'series': [{'component': 'Scatter', 'fill': 'var(--color-value)'}],
        'axes': [
            {'component': 'XAxis', 'type': 'number', 'dataKey': 'cost', 'name': 'Cost', 'tickLine': False, 'axisLine': False, 'tickMargin': 8},
            {'component': 'YAxis', 'type': 'number', 'dataKey': 'value', 'name': 'Value', 'tickLine': False, 'axisLine': False, 'tickMargin': 8},
        ],
        'grid': {'component': 'CartesianGrid'},
        'tooltip': {'cursor': False},
        'legend': None, 'labels': [],
    }


# ---------------------------------------------------------------- two-by-two matrix

# Ten options. cost: delivery cost in $ thousands (x), value: benefit score out of 100 (y), effort: person-weeks (size).
MATRIX_DATA = [
    {'option': 'SSO rollout', 'cost': 60, 'value': 82, 'effort': 6},
    {'option': 'Retire legacy CRM', 'cost': 90, 'value': 68, 'effort': 10},
    {'option': 'API gateway', 'cost': 120, 'value': 74, 'effort': 14},
    {'option': 'Data lake', 'cost': 280, 'value': 88, 'effort': 40},
    {'option': 'ERP upgrade', 'cost': 300, 'value': 76, 'effort': 52},
    {'option': 'Mainframe exit', 'cost': 250, 'value': 62, 'effort': 36},
    {'option': 'Wiki cleanup', 'cost': 30, 'value': 22, 'effort': 3},
    {'option': 'Portal rename', 'cost': 70, 'value': 35, 'effort': 4},
    {'option': 'Custom BI suite', 'cost': 280, 'value': 30, 'effort': 30},
    {'option': 'On-prem refresh', 'cost': 220, 'value': 18, 'effort': 20},
]
X_MAX, Y_MAX = 400, 100
X_SPLIT, Y_SPLIT = 200, 50
BAND = 6  # height of a quadrant's label band, in value points (6% of the plot is 28px at 464px)

QUADRANTS = [  # (label, x range, y range of the band, chart token)
    ('Quick wins', (0, X_SPLIT), (Y_MAX - BAND, Y_MAX), 'var(--chart-2)'),
    ('Major projects', (X_SPLIT, X_MAX), (Y_MAX - BAND, Y_MAX), 'var(--chart-1)'),
    ('Fill-ins', (0, X_SPLIT), (Y_SPLIT - BAND, Y_SPLIT), 'var(--chart-4)'),
    ('Reconsider', (X_SPLIT, X_MAX), (Y_SPLIT - BAND, Y_SPLIT), 'var(--chart-5)'),
]


def quadrant_of(point):
    """The quadrant label a point falls in (a point on a threshold line belongs to the higher side)."""
    high_cost, high_value = point['cost'] >= X_SPLIT, point['value'] >= Y_SPLIT
    return {(False, True): 'Quick wins', (True, True): 'Major projects', (False, False): 'Fill-ins', (True, False): 'Reconsider'}[(high_cost, high_value)]


def matrix_two_by_two():
    refs = []
    for label, (x1, x2), (y1, y2), colour in QUADRANTS:
        refs.append({'component': 'ReferenceArea', 'x1': x1, 'x2': x2, 'y1': y1, 'y2': y2, 'fill': colour, 'fillOpacity': 0.1, 'stroke': 'none',
                     'label': {'value': label, 'position': 'insideTopLeft', 'offset': 8, 'fill': 'var(--foreground)', 'fontSize': 12}})
    refs.append({'component': 'ReferenceLine', 'x': X_SPLIT, 'stroke': 'var(--muted-foreground)', 'strokeDasharray': '4 4'})
    refs.append({'component': 'ReferenceLine', 'y': Y_SPLIT, 'stroke': 'var(--muted-foreground)', 'strokeDasharray': '4 4'})
    axis_label = {'fill': 'var(--muted-foreground)'}
    return {
        'type': 'scatter', 'component': 'ScatterChart',
        'config': {'value': {'label': 'Value', 'color': 'var(--chart-1)'}},
        'data': MATRIX_DATA,
        'props': {'accessibilityLayer': True, 'margin': {'top': 16, 'right': 24, 'bottom': 8, 'left': 8}},
        'series': [{'component': 'Scatter', 'fill': 'var(--color-value)',
                    'labelList': [{'dataKey': 'option', 'position': 'right', 'offset': 8, 'className': 'fill-foreground', 'fontSize': 12}]}],
        'axes': [
            {'component': 'XAxis', 'type': 'number', 'dataKey': 'cost', 'name': 'Cost', 'domain': [0, X_MAX], 'ticks': [0, 100, 200, 300, 400],
             'height': 56, 'tickLine': False, 'axisLine': False, 'tickMargin': 8,
             'label': dict(axis_label, value='Cost to deliver ($ thousands)', position='insideBottom', offset=0)},
            {'component': 'YAxis', 'type': 'number', 'dataKey': 'value', 'name': 'Value', 'domain': [0, Y_MAX], 'ticks': [0, 25, 50, 75, 100],
             'width': 64, 'tickLine': False, 'axisLine': False, 'tickMargin': 8,
             'label': dict(axis_label, value='Value to the business (score)', angle=-90, position='insideLeft', offset=8, style={'textAnchor': 'middle'})},
            {'component': 'ZAxis', 'type': 'number', 'dataKey': 'effort', 'name': 'Effort (person-weeks)', 'range': [60, 400]},
        ],
        'references': refs,
        'grid': {'component': 'CartesianGrid'},
        'tooltip': {'cursor': False, 'labelFormatter': {'$fn': 'payloadField', 'key': 'option'}},
        'legend': None, 'labels': [],
    }


# ---------------------------------------------------------------- cost bridge

# (step, kind, amount in $ thousands): a total is drawn from zero, a change moves the running total.
BRIDGE_STEPS = [
    ('Current cost', 'total', 4800),
    ('Licences', 'change', -900),
    ('Hosting', 'change', -700),
    ('Support', 'change', -500),
    ('Migration', 'change', 650),
    ('Three-year total', 'total', None),  # the sum of the steps before it
]


def money(n, signed=False):
    sign = '-' if n < 0 else ('+' if signed else '')
    return f'{sign}${abs(n):,}k'


def bridge_rows():
    """One row per step: base (the transparent offset), fall, rise, total (the bars), label, and the running total."""
    rows, running = [], 0
    for step, kind, amount in BRIDGE_STEPS:
        row = {'step': step, 'base': 0, 'fall': None, 'rise': None, 'total': None}
        if kind == 'total':
            if amount is None:
                amount = running
            running = amount
            row.update(total=amount, label=money(amount))
        else:
            start, end = running, running + amount
            row['base'] = min(start, end)
            row['fall' if amount < 0 else 'rise'] = abs(amount)
            row['label'] = money(amount, signed=True)
            running = end
        row['running'] = running
        rows.append(row)
    return rows


def bridge_connectors(rows):
    """A dashed segment from each step to the next at the running total after the step."""
    return [{'component': 'ReferenceLine', 'segment': [{'x': a['step'], 'y': a['running']}, {'x': b['step'], 'y': a['running']}],
             'stroke': 'var(--muted-foreground)', 'strokeDasharray': '3 3'} for a, b in zip(rows, rows[1:])]


# chart-5 (the falls) is oklch(0.269) in both themes: 1.2:1 against the dark card, so a fall would vanish in dark mode.
# Every coloured bar gets a 1px outline in muted-foreground, which is at least 3:1 against the card in both themes.
OUTLINE = {'stroke': 'var(--muted-foreground)', 'strokeWidth': 1}


def bar_waterfall():
    rows = bridge_rows()
    label = {'dataKey': 'label', 'position': 'top', 'offset': 8, 'className': 'fill-foreground', 'fontSize': 12}
    return {
        'type': 'bar', 'component': 'BarChart',
        'config': {'base': {'label': 'Base'}, 'fall': {'label': 'Decrease', 'color': 'var(--chart-5)'},
                   'rise': {'label': 'Increase', 'color': 'var(--chart-2)'}, 'total': {'label': 'Total', 'color': 'var(--primary)'}},
        'data': [{k: v for k, v in r.items() if k != 'running'} for r in rows],
        'props': {'accessibilityLayer': True},
        'series': [
            {'component': 'Bar', 'dataKey': 'base', 'stackId': 'a', 'fill': 'transparent', 'legendType': 'none', 'tooltipType': 'none'},
            {'component': 'Bar', 'dataKey': 'fall', 'stackId': 'a', 'fill': 'var(--color-fall)', **OUTLINE, 'labelList': [dict(label)]},
            {'component': 'Bar', 'dataKey': 'rise', 'stackId': 'a', 'fill': 'var(--color-rise)', **OUTLINE, 'labelList': [dict(label)]},
            {'component': 'Bar', 'dataKey': 'total', 'stackId': 'a', 'fill': 'var(--color-total)', **OUTLINE, 'labelList': [dict(label)]},
        ],
        'axes': [
            {'component': 'XAxis', 'dataKey': 'step', 'tickLine': False, 'tickMargin': 10, 'axisLine': False, 'interval': 0},
            {'component': 'YAxis', 'tickLine': False, 'axisLine': False, 'tickMargin': 8},
        ],
        'references': bridge_connectors(rows),
        'grid': {'component': 'CartesianGrid', 'vertical': False},
        'tooltip': {},
        'legend': {},
        'labels': [],
    }


SPECS = {'chart-scatter-default': scatter_default, 'chart-matrix-two-by-two': matrix_two_by_two, 'chart-bar-waterfall': bar_waterfall}


def main():
    for name, build in SPECS.items():
        spec = finish_spec(build())
        path = DATA_DIR / f'{name}.json'
        path.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + '\n', encoding='utf8')
        print(f'{path.relative_to(ROOT)}: {len(spec["data"])} rows')


if __name__ == '__main__':
    main()
