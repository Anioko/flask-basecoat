"""Chart specs: the declarative description of a chart that the `chart` macro renders and the runtime draws.

A spec is a JSON object (a Python dict in a template or view)::

    {
      "component": "AreaChart" | "BarChart" | "LineChart" | "PieChart" | "RadarChart" | "RadialBarChart",
      "config": {"desktop": {"label": "Desktop", "color": "var(--chart-1)"}},  # ChartConfig, also feeds <style>
      "data": [{"month": "January", "desktop": 186}, ...],
      "props": {"margin": {"left": 12, "right": 12}, "layout": "vertical", "stackOffset": "expand", ...},
      "series": [{"component": "Area", "dataKey": "desktop", "type": "natural", "fill": "var(--color-desktop)",
                  "labelList": [...], "labels": [...], "cells": [...], ...}],
      "axes": [{"component": "XAxis", "dataKey": "month", "tickFormatter": {"$fn": "slice", "start": 0, "end": 3}}],
      "grid": {"component": "CartesianGrid", "vertical": false} | null,
      "tooltip": {"cursor": false, "indicator": "line", "hideLabel": true, ...} | null,
      "legend": {"nameKey": "browser", "className": "..."} | null,
      "defs": [{"tag": "linearGradient", "props": {...}, "children": [{"tag": "stop", "props": {...}}]}],
      "state": {"timeRange": "90d"},                      # interactive charts
      "derive": {"$fn": "sinceDays", ...},                # data filtered by the state
      "computed": {"activeIndex": {"$fn": "indexOf", "key": "month", "state": "activeMonth"}}
    }

Props are the props the upstream Recharts element is given; Recharts defaults are applied by the runtime. A value
``{"state": name}`` reads the chart state and ``{"$template": "var(--color-{activeChart})"}`` formats it.

Function-valued props are written as ``{"$fn": name, ...arguments}`` and resolved in the browser by the registry
in ``static/js/src/components/chart-format.js``. ``FORMATTERS`` below lists them. ``runtime_spec`` turns an
extracted upstream recipe (``compliance/recipes/charts/<name>.json``) into a spec, mapping each function source
of the upstream charts to its registry entry (``FUNCTION_SOURCES``).
"""
import copy
import json
import pathlib
import re

from flask_basecoat.twmerge import merge as _merge


def tw_merge(*classes):
    return _merge(classes)

DATA_DIR = pathlib.Path(__file__).resolve().parent / 'data' / 'charts'

FORMATTERS = {
    'slice': 'String(value).slice(start, end): XAxis/YAxis tickFormatter',
    'localeDate': 'new Date(value).toLocaleDateString(locale, options): tickFormatter, labelFormatter',
    'configLabel': 'chartConfig[value]?.label: tickFormatter, LabelList formatter',
    'configLabelOfFirstDataKey': 'chartConfig[payload[0].dataKey].label: tooltip labelFormatter',
    'payloadField': 'payload?.[0]?.payload[key]: tooltip labelFormatter showing a field of the hovered row (the name of a scatter point)',
    'unitValue': 'tooltip formatter: label, value and unit (wrap=true puts them in a min-w-[130px] row)',
    'unitValueWithTotal': 'tooltip formatter: swatch, label, value and unit, plus a Total row after index `after`',
    'centerText': 'Label content: <text> centred on the polar view box, one <tspan> per line',
    'activeRectangle': 'Bar shape: extra Rectangle props for the bar at `index`',
    'activeSector': 'Pie shape: outerRadius + grow for the sector at `index`',
    'activeSectorRing': 'Pie shape: activeSector plus a ring from outerRadius+ring[0] to outerRadius+ring[1]',
    'payloadDot': 'Line dot coloured with the row fill',
    'iconDot': 'Line dot drawn as a lucide icon',
    'payloadText': 'Pie label showing payload[key]',
    'stackedTick': 'PolarAngleAxis tick showing two values and the category',
    'sinceDays': 'derive: rows whose `key` date is at most N days before `reference` (N from the state)',
    'indexOf': 'computed: index of the row whose `key` equals the state value',
}

_TOTAL = {'centerText': True}


def _center(lines, baseline='middle'):
    out = {'$fn': 'centerText', 'lines': lines}
    if baseline:
        out['dominantBaseline'] = baseline
    return out


FUNCTION_SOURCES = {
    '(value) => value.slice(0, 3)': {'$fn': 'slice', 'start': 0, 'end': 3},
    '(value) => { const date = new Date(value) return date.toLocaleDateString("en-US", { month: "short", day: "numeric", }) }':
        {'$fn': 'localeDate', 'locale': 'en-US', 'options': {'month': 'short', 'day': 'numeric'}},
    '(value) => { return new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric", }) }':
        {'$fn': 'localeDate', 'locale': 'en-US', 'options': {'month': 'short', 'day': 'numeric'}},
    '(value) => { return new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", }) }':
        {'$fn': 'localeDate', 'locale': 'en-US', 'options': {'month': 'short', 'day': 'numeric', 'year': 'numeric'}},
    '(value) => { return new Date(value).toLocaleDateString("en-US", { weekday: "short", }) }':
        {'$fn': 'localeDate', 'locale': 'en-US', 'options': {'weekday': 'short'}},
    '(value) => { return new Date(value).toLocaleDateString("en-US", { day: "numeric", month: "long", year: "numeric", }) }':
        {'$fn': 'localeDate', 'locale': 'en-US', 'options': {'day': 'numeric', 'month': 'long', 'year': 'numeric'}},
    '(value) => chartConfig[value as keyof typeof chartConfig]?.label': {'$fn': 'configLabel'},
    '(_, payload) => { return chartConfig[ payload?.[0].dataKey as keyof typeof chartConfig ].label }': {'$fn': 'configLabelOfFirstDataKey'},
    '({ index, ...props }: BarShapeProps) => index === ACTIVE_INDEX ? ( <Rectangle {...props} fillOpacity={0.8} stroke={props.payload.fill} strokeDasharray={4} strokeDashoffset={4} /> ) : ( <Rectangle {...props} /> )':
        {'$fn': 'activeRectangle', 'index': 2, 'props': {'fillOpacity': 0.8, 'strokeDasharray': 4, 'strokeDashoffset': 4}, 'strokeFromPayload': 'fill'},
    '({ payload, ...props }) => { return ( <Dot key={payload.browser} r={5} cx={props.cx} cy={props.cy} fill={payload.fill} stroke={payload.fill} /> ) }':
        {'$fn': 'payloadDot', 'r': 5},
    '({ cx, cy, payload }) => { if (cx == null || cy == null) { return null } const r = 24 return ( <GitCommitVertical key={payload.month} x={cx - r / 2} y={cy - r / 2} width={r} height={r} fill="hsl(var(--background))" stroke="var(--color-desktop)" /> ) }':
        {'$fn': 'iconDot', 'icon': 'git-commit-vertical', 'size': 24, 'fill': 'hsl(var(--background))', 'stroke': 'var(--color-desktop)'},
    '({ index, outerRadius = 0, ...props }: PieSectorShapeProps) => index === ACTIVE_INDEX ? ( <Sector {...props} outerRadius={outerRadius + 10} /> ) : ( <Sector {...props} outerRadius={outerRadius} /> )':
        {'$fn': 'activeSector', 'index': 0, 'grow': 10},
    '({ index, outerRadius = 0, ...props }: PieSectorShapeProps) => { if (index === activeIndex) { return ( <g> <Sector {...props} outerRadius={outerRadius + 10} /> <Sector {...props} outerRadius={outerRadius + 25} innerRadius={outerRadius + 12} /> </g> ) } return <Sector {...props} outerRadius={outerRadius} /> }':
        {'$fn': 'activeSectorRing', 'index': {'state': 'activeIndex'}, 'grow': 10, 'ring': [12, 25]},
    '({ viewBox }) => { if (viewBox && "cx" in viewBox && "cy" in viewBox) { return ( <text x={viewBox.cx} y={viewBox.cy} textAnchor="middle" dominantBaseline="middle" > <tspan x={viewBox.cx} y={viewBox.cy} className="fill-foreground text-3xl font-bold" > {totalVisitors.toLocaleString()} </tspan> <tspan x={viewBox.cx} y={(viewBox.cy || 0) + 24} className="fill-muted-foreground" > Visitors </tspan> </text> ) } }':
        _center([{'value': {'sum': 'visitors'}, 'className': 'fill-foreground text-3xl font-bold', 'dy': 0},
                 {'value': {'text': 'Visitors'}, 'className': 'fill-muted-foreground', 'dy': 24}]),
    '({ viewBox }) => { if (viewBox && "cx" in viewBox && "cy" in viewBox) { return ( <text x={viewBox.cx} y={viewBox.cy} textAnchor="middle" dominantBaseline="middle" > <tspan x={viewBox.cx} y={viewBox.cy} className="fill-foreground text-3xl font-bold" > {desktopData[activeIndex].desktop.toLocaleString()} </tspan> <tspan x={viewBox.cx} y={(viewBox.cy || 0) + 24} className="fill-muted-foreground" > Visitors </tspan> </text> ) } }':
        _center([{'value': {'pick': 'desktop', 'index': {'state': 'activeIndex'}}, 'className': 'fill-foreground text-3xl font-bold', 'dy': 0},
                 {'value': {'text': 'Visitors'}, 'className': 'fill-muted-foreground', 'dy': 24}]),
    '({ viewBox }) => { if (viewBox && "cx" in viewBox && "cy" in viewBox) { return ( <text x={viewBox.cx} y={viewBox.cy} textAnchor="middle" dominantBaseline="middle" > <tspan x={viewBox.cx} y={viewBox.cy} className="fill-foreground text-4xl font-bold" > {chartData[0].visitors.toLocaleString()} </tspan> <tspan x={viewBox.cx} y={(viewBox.cy || 0) + 24} className="fill-muted-foreground" > Visitors </tspan> </text> ) } }':
        _center([{'value': {'pick': 'visitors', 'index': 0}, 'className': 'fill-foreground text-4xl font-bold', 'dy': 0},
                 {'value': {'text': 'Visitors'}, 'className': 'fill-muted-foreground', 'dy': 24}]),
    '({ viewBox }) => { if (viewBox && "cx" in viewBox && "cy" in viewBox) { return ( <text x={viewBox.cx} y={viewBox.cy} textAnchor="middle"> <tspan x={viewBox.cx} y={(viewBox.cy || 0) - 16} className="fill-foreground text-2xl font-bold" > {totalVisitors.toLocaleString()} </tspan> <tspan x={viewBox.cx} y={(viewBox.cy || 0) + 4} className="fill-muted-foreground" > Visitors </tspan> </text> ) } }':
        _center([{'value': {'pickSum': ['desktop', 'mobile'], 'index': 0}, 'className': 'fill-foreground text-2xl font-bold', 'dy': -16},
                 {'value': {'text': 'Visitors'}, 'className': 'fill-muted-foreground', 'dy': 4}], baseline=None),
    '({ payload, ...props }) => { return ( <text cx={props.cx} cy={props.cy} x={props.x} y={props.y} textAnchor={props.textAnchor} dominantBaseline={props.dominantBaseline} fill="var(--foreground)" > {payload.visitors} </text> ) }':
        {'$fn': 'payloadText', 'key': 'visitors', 'fill': 'var(--foreground)'},
    '({ x, y, textAnchor, index, ...props }) => { const data = chartData[index] const yValue = typeof y === "number" ? y : 0 return ( <text x={x} y={yValue + (index === 0 ? -10 : 0)} textAnchor={textAnchor} fontSize={13} fontWeight={500} {...props} > <tspan>{data.desktop}</tspan> <tspan className="fill-muted-foreground">/</tspan> <tspan>{data.mobile}</tspan> <tspan x={x} dy={"1rem"} fontSize={12} className="fill-muted-foreground" > {data.month} </tspan> </text> ) }':
        {'$fn': 'stackedTick', 'keys': ['desktop', 'mobile'], 'labelKey': 'month', 'firstDy': -10},
    '(value, name, item, index) => ( <> <div className="h-2.5 w-2.5 shrink-0 rounded-[2px] bg-(--color-bg)" style={ { "--color-bg": `var(--color-${name})`, } as React.CSSProperties } /> {chartConfig[name as keyof typeof chartConfig]?.label || name} <div className="ml-auto flex items-baseline gap-0.5 font-mono font-medium text-foreground tabular-nums"> {value} <span className="font-normal text-muted-foreground"> kcal </span> </div> {/* Add this after the last item */} {index === 1 && ( <div className="mt-1.5 flex basis-full items-center border-t pt-1.5 text-xs font-medium text-foreground"> Total <div className="ml-auto flex items-baseline gap-0.5 font-mono font-medium text-foreground tabular-nums"> {item.payload.running + item.payload.swimming} <span className="font-normal text-muted-foreground"> kcal </span> </div> </div> )} </> )':
        {'$fn': 'unitValueWithTotal', 'unit': 'kcal', 'keys': ['running', 'swimming'], 'after': 1},
    '(value, name) => ( <div className="flex min-w-[130px] items-center text-xs text-muted-foreground"> {chartConfig[name as keyof typeof chartConfig]?.label || name} <div className="ml-auto flex items-baseline gap-0.5 font-mono font-medium text-foreground tabular-nums"> {value} <span className="font-normal text-muted-foreground"> kcal </span> </div> </div> )':
        {'$fn': 'unitValue', 'unit': 'kcal', 'wrap': True},
}

# lucide-react aliases emit the canonical icon's class plus the alias class
ICON_CLASSES = {'waves': 'lucide lucide-waves-horizontal lucide-waves'}

TOOLTIP_BASE = 'cn-chart-tooltip grid min-w-32 items-start'
LEGEND_BASE = 'flex items-center justify-center gap-4'


def norm_source(src):
    return re.sub(r'\s+', ' ', src).strip()


def _get(obj, path):
    for part in re.findall(r'[^.\[\]]+', path):
        obj = obj[int(part)] if part.isdigit() else obj[part]
    return obj


def _set(obj, path, value):
    parts = re.findall(r'[^.\[\]]+', path)
    for part in parts[:-1]:
        obj = obj[int(part)] if part.isdigit() else obj[part]
    last = parts[-1]
    if last.isdigit():
        obj[int(last)] = value
    else:
        obj[last] = value


def function_ref(src):
    ref = FUNCTION_SOURCES.get(norm_source(src))
    if ref is None:
        raise KeyError(f'no chart formatter for function source: {norm_source(src)[:120]}')
    return copy.deepcopy(ref)


def icon_markup(name):
    from flask_basecoat.icons import svg
    markup = str(svg(name, aria_hidden='true'))
    if name in ICON_CLASSES:
        markup = markup.replace(f'class="lucide lucide-{name}"', f'class="{ICON_CLASSES[name]}"')
    return markup


def finish_spec(chart):
    """Fill in what the macro and the runtime need besides the upstream props: merged class strings and icons."""
    spec = chart
    t = spec.get('tooltip')
    if t:
        t.pop('content', None)
        t['$class'] = tw_merge(TOOLTIP_BASE, t.get('className') or '')
        if t.get('labelClassName'):
            t['$labelClass'] = tw_merge('font-medium', t['labelClassName'])
    lg = spec.get('legend')
    if lg:
        lg.pop('content', None)
        pad = 'pb-3' if lg.get('verticalAlign') == 'top' else 'pt-3'
        lg['$class'] = tw_merge(LEGEND_BASE, pad, lg.get('className') or '')
    icons = {}
    for key, conf in (spec.get('config') or {}).items():
        icon = conf.get('icon')
        if isinstance(icon, dict):
            conf['icon'] = icon['icon']
            icons[icon['icon']] = icon_markup(icon['icon'])
    for ref in _walk_refs(spec):
        if ref.get('$fn') == 'iconDot':
            icons[ref['icon']] = icon_markup(ref['icon'])
    if icons:
        spec['icons'] = icons
    return spec


def _walk_refs(obj):
    if isinstance(obj, dict):
        if '$fn' in obj:
            yield obj
        for v in obj.values():
            yield from _walk_refs(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_refs(v)


def runtime_spec(recipe):
    """Turn an extracted upstream chart recipe into a runtime spec (function sources become registry refs)."""
    rec = copy.deepcopy(recipe)
    for path in rec.get('functionProps', []):
        if not path.startswith('chart.'):
            continue
        _set(rec, path, function_ref(_get(rec, path)))
    if rec.get('unresolved'):
        raise ValueError(f"{rec['name']}: unresolved values {[u['path'] for u in rec['unresolved']]}")
    chart = rec['chart']
    spec = {k: chart[k] for k in ('type', 'component', 'config', 'data', 'props', 'series', 'axes', 'grid', 'tooltip', 'legend', 'labels') if k in chart}
    if chart.get('defs'):
        spec['defs'] = chart['defs']
    for s in spec['series']:
        if 'children' in s:
            s.pop('children')
    if spec.get('data') is None and spec['series'] and isinstance(spec['series'][0].get('data'), list):
        spec['data'] = spec['series'][0]['data']
    inter = rec.get('interactive') or {}
    if inter.get('runtime'):
        spec.update(copy.deepcopy(inter['runtime']))
    return finish_spec(spec)


def load_spec(name):
    """The shipped spec of an upstream chart (flask_basecoat/data/charts/<name>.json)."""
    path = DATA_DIR / f'{name}.json'
    return json.loads(path.read_text(encoding='utf8'))


def chart_style_css(chart_id, config):
    """The <style> body shadcn's ChartStyle emits: --color-<key> for the light and the dark theme."""
    entries = [(k, c) for k, c in (config or {}).items() if (c.get('theme') or c.get('color'))]
    if not entries:
        return ''
    blocks = []
    for theme, prefix in (('light', ''), ('dark', '.dark')):
        lines = []
        for key, c in entries:
            color = (c.get('theme') or {}).get(theme) or c.get('color')
            lines.append(f'  --color-{key}: {color};' if color else '')  # Array.join renders null as ''
        blocks.append(f'\n{prefix} [data-chart={chart_id}] {{\n' + '\n'.join(lines) + '\n}\n')
    return '\n'.join(blocks)


def chart_uid():
    """A data-chart id unique within the current request (falls back to a process counter outside one)."""
    global _UID
    try:
        from flask import g
        n = g.get('_basecoat_chart_uid', 0) + 1
        g._basecoat_chart_uid = n
        return f'u{n}'
    except RuntimeError:
        _UID += 1
        return f'u{_UID}'


_UID = 0


def spec_json(spec):
    """JSON for a <script type="application/json"> element: '<', '>' and '&' escaped so it cannot close the script."""
    text = json.dumps(spec, separators=(',', ':'), ensure_ascii=False)
    return text.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
