"""Build the runtime spec of the dashboard-01 block chart from the pinned upstream TSX."""
import copy
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
src = (ROOT / 'compliance/upstream/shadcn/radix/blocks/dashboard-01/components/chart-area-interactive.tsx').read_text(encoding='utf-8')
rows = [{'date': d, 'desktop': int(a), 'mobile': int(b)}
        for d, a, b in re.findall(r'\{ date: "([\d-]+)", desktop: (\d+), mobile: (\d+) \}', src)]
assert len(rows) == 91, len(rows)

base = json.loads((ROOT / 'flask_basecoat/data/charts/chart-area-interactive.json').read_text(encoding='utf-8'))
print('data same as chart-area-interactive:', base['data'] == rows)

spec = copy.deepcopy(base)
spec['config'] = {'visitors': {'label': 'Visitors'},
                  'desktop': {'label': 'Desktop', 'color': 'var(--primary)'},
                  'mobile': {'label': 'Mobile', 'color': 'var(--primary)'}}
spec['data'] = rows
# upstream: fillDesktop stops 1.0 / 0.1, fillMobile 0.8 / 0.1
stops = {d['props']['id']: d['children'] for d in spec['defs']}
stops['fillDesktop'][0]['props']['stopOpacity'] = 1.0
stops['fillDesktop'][1]['props']['stopOpacity'] = 0.1
stops['fillMobile'][0]['props']['stopOpacity'] = 0.8
stops['fillMobile'][1]['props']['stopOpacity'] = 0.1
for k in ('fillDesktop', 'fillMobile'):
    assert [s['props']['stopColor'] for s in stops[k]] == [f'var(--color-{k[4:].lower()})'] * 2
assert [s['dataKey'] for s in spec['series']] == ['mobile', 'desktop']
assert spec['state'] == {'timeRange': '90d'}
assert spec['derive']['reference'] == '2024-06-30' and spec['derive']['days'] == {'90d': 90, '30d': 30, '7d': 7}
for needle in ('"var(--primary)"', 'stopOpacity={1.0}', 'stopOpacity={0.8}', 'minTickGap={32}', 'tickMargin={8}',
               'cursor={false}', 'indicator="dot"', 'type="natural"', 'stackId="a"', 'new Date("2024-06-30")',
               'React.useState("90d")'):
    assert needle in src, needle
out = ROOT / 'flask_basecoat/data/charts/dashboard-01-chart-area-interactive.json'
out.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
print('wrote', out)
# The written spec was then given two upstream behaviours by hand: no legend, and the 7-day range below 768px
# (useIsMobile). Re-apply them if this script is run again.
