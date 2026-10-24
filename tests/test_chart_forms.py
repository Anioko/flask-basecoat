"""The chart renderer's ports for the forms shadcn has no original for (rulings R18 and R19): ReferenceLine,
ReferenceArea, axis labels, ScatterChart with ZAxis, and the specs built on them (the two-by-two matrix and the cost
bridge). The browser tests draw a spec in headless Chromium through a throwaway app route and read the SVG back."""
import pathlib
import threading

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
playwright_sync = pytest.importorskip('playwright.sync_api')

@pytest.fixture(scope='module')
def server():
    from flask import render_template_string, request
    from werkzeug.serving import make_server
    from flask_basecoat.testing import make_app
    app = make_app()
    specs = {}

    @app.route('/t/<key>')
    def show(key):
        w = int(request.args.get('w', 600))
        h = int(request.args.get('h', 300))
        return render_template_string("""{% extends 'basecoat/pages/_layout.html' %}{% import 'basecoat/index.html' as ui %}
{% block body %}<div class="p-4"><div style="width: {{ w }}px">{{ ui.chart_from_spec(spec, id='t', class='aspect-auto w-full', attrs={'style': 'height: ' ~ h ~ 'px'}) }}</div></div>{% endblock %}""", spec=specs[key], w=w, h=h)

    @app.route('/v/<key>')
    def views(key):
        return render_template_string("""{% extends 'basecoat/pages/_layout.html' %}{% import 'basecoat/index.html' as ui %}
{% block body %}<div class="p-4">
{% call ui.toggle_group(type='single', variant='outline', attrs={'aria-label': 'View', 'data-chart-view': 'chart-t'}) %}
  {{ ui.toggle_group_item(text='Chart', value='chart', variant='outline', pressed=true) }}{{ ui.toggle_group_item(text='Table', value='table', variant='outline') }}
{% endcall %}
<div data-chart-view-panel="chart-t" data-chart-view-value="chart" id="chart-panel"><div style="width: 500px">{{ ui.chart_from_spec(spec, id='t', class='aspect-auto w-full', attrs={'style': 'height: 250px'}) }}</div></div>
<div data-chart-view-panel="chart-t" data-chart-view-value="table" id="table-panel" hidden>The table</div>
</div>{% endblock %}""", spec=specs[key])

    srv = make_server('127.0.0.1', 0, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{srv.server_port}', specs
    srv.shutdown()


@pytest.fixture(scope='module')
def browser():
    with playwright_sync.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def draw(server, browser):
    """draw(spec, w=600, h=300) -> page with the chart drawn; pages are closed after the test."""
    base, specs = server
    pages = []

    def go(spec, w=600, h=300, theme='light'):
        key = f'k{len(specs)}'
        specs[key] = spec
        page = browser.new_page(viewport={'width': max(w + 40, 400), 'height': h + 200})
        pages.append(page)
        page.goto(f'{base}/t/{key}?w={w}&h={h}&theme={theme}')
        page.wait_for_function("() => { const s = document.querySelector('svg.recharts-surface'); return s && s.getBoundingClientRect().width > 0 }")
        page.wait_for_timeout(100)
        return page

    yield go
    for pg in pages:
        pg.close()


def bar_spec(**over):
    spec = {'type': 'bar', 'component': 'BarChart', 'config': {'v': {'label': 'V', 'color': 'var(--chart-1)'}},
            'data': [{'k': 'A', 'v': 40}, {'k': 'B', 'v': 80}, {'k': 'C', 'v': 60}], 'props': {'accessibilityLayer': True},
            'series': [{'component': 'Bar', 'dataKey': 'v', 'fill': 'var(--color-v)'}],
            'axes': [{'component': 'XAxis', 'dataKey': 'k', 'tickLine': False, 'axisLine': False},
                     {'component': 'YAxis', 'domain': [0, 100], 'ticks': [0, 50, 100], 'tickLine': False, 'axisLine': False}],
            'grid': {'component': 'CartesianGrid', 'vertical': False}, 'tooltip': None, 'legend': None, 'labels': []}
    spec.update(over)
    return spec


PLOT_JS = """() => { const r = document.querySelector('svg.recharts-surface defs clipPath rect');
  return { x: +r.getAttribute('x'), y: +r.getAttribute('y'), width: +r.getAttribute('width'), height: +r.getAttribute('height') } }"""
ATTRS_JS = """(sel) => [...document.querySelectorAll(sel)].map((e) => Object.fromEntries([...e.attributes].map((a) => [a.name, a.value])))"""


# ---------------------------------------------------------------- ReferenceLine and ReferenceArea

def test_reference_line_sits_at_its_data_value(draw):
    spec = bar_spec(references=[{'component': 'ReferenceLine', 'y': 50, 'stroke': 'var(--muted-foreground)', 'strokeDasharray': '4 4'}])
    page = draw(spec)
    plot = page.evaluate(PLOT_JS)
    (line,) = page.evaluate(ATTRS_JS, '.recharts-reference-line-line')
    assert float(line['y1']) == pytest.approx(plot['y'] + plot['height'] / 2, abs=0.5) == pytest.approx(float(line['y2']), abs=0.01)
    assert sorted([float(line['x1']), float(line['x2'])]) == pytest.approx([plot['x'], plot['x'] + plot['width']], abs=0.5)
    assert line['stroke'] == 'var(--muted-foreground)' and line['stroke-dasharray'] == '4 4'
    assert line['fill'] == 'none' and line['stroke-width'] == '1'


def test_reference_line_segment_joins_two_category_centres(draw):
    spec = bar_spec(references=[{'component': 'ReferenceLine', 'segment': [{'x': 'A', 'y': 40}, {'x': 'B', 'y': 40}]}])
    page = draw(spec)
    plot = page.evaluate(PLOT_JS)
    (line,) = page.evaluate(ATTRS_JS, '.recharts-reference-line-line')
    band = plot['width'] / 3
    assert float(line['x1']) == pytest.approx(plot['x'] + band / 2, abs=0.6)
    assert float(line['x2']) == pytest.approx(plot['x'] + band * 1.5, abs=0.6)
    assert float(line['y1']) == pytest.approx(plot['y'] + plot['height'] * 0.6, abs=0.5)


def test_reference_line_outside_the_domain_is_discarded_unless_it_overflows_visibly(draw):
    spec = bar_spec(references=[{'component': 'ReferenceLine', 'y': 250}, {'component': 'ReferenceLine', 'x': 'Z'}])
    page = draw(spec)
    assert page.locator('.recharts-reference-line').count() == 0


def test_reference_area_covers_its_data_rectangle_and_labels_itself(draw):
    spec = bar_spec(references=[{'component': 'ReferenceArea', 'x1': 'B', 'x2': 'C', 'y1': 0, 'y2': 50, 'fill': 'var(--chart-2)', 'fillOpacity': 0.1, 'stroke': 'none',
                                 'label': {'value': 'Zone', 'position': 'insideTopLeft', 'offset': 8, 'fill': 'var(--foreground)'}}])
    page = draw(spec)
    plot = page.evaluate(PLOT_JS)
    (area,) = page.evaluate(ATTRS_JS, 'path.recharts-reference-area-rect')
    band = plot['width'] / 3
    assert float(area['x']) == pytest.approx(plot['x'] + band, abs=0.6)
    assert float(area['width']) == pytest.approx(band * 2, abs=0.6)
    assert float(area['y']) == pytest.approx(plot['y'] + plot['height'] / 2, abs=0.5)
    assert float(area['height']) == pytest.approx(plot['height'] / 2, abs=0.5)
    assert area['fill'] == 'var(--chart-2)' and area['fill-opacity'] == '0.1'
    label = page.locator('text.recharts-label', has_text='Zone')
    assert label.count() == 1
    assert float(label.get_attribute('x')) == pytest.approx(float(area['x']) + 8, abs=0.5)
    # reference elements live in the zIndex layers Recharts gives them: areas at 100, lines at 400, labels at 2000
    assert page.locator('g.recharts-zIndex-layer_100 > g.recharts-reference-area').count() == 1
    assert page.locator('g.recharts-zIndex-layer_2000 > text.recharts-label').count() == 1


# ---------------------------------------------------------------- axis labels and user ticks

def test_axis_labels_are_drawn_inside_the_axis_box_after_the_tick_labels(draw):
    spec = bar_spec()
    spec['axes'][0].update(height=56, label={'value': 'Step of the plan', 'position': 'insideBottom', 'offset': 0, 'fill': 'var(--muted-foreground)'})
    spec['axes'][1].update(width=64, label={'value': 'Cost in dollars', 'angle': -90, 'position': 'insideLeft', 'offset': 8, 'fill': 'var(--muted-foreground)', 'style': {'textAnchor': 'middle'}})
    page = draw(spec)
    plot = page.evaluate(PLOT_JS)
    (x_label,) = page.evaluate(ATTRS_JS, 'text.recharts-label:has(tspan)')[:1] and [a for a in page.evaluate(ATTRS_JS, 'text.recharts-label') if 'transform' not in a]
    assert float(x_label['x']) == pytest.approx(plot['x'] + plot['width'] / 2, abs=0.5)
    assert float(x_label['y']) == pytest.approx(plot['y'] + plot['height'] + 56, abs=0.5)  # the bottom of the axis box
    assert x_label['text-anchor'] == 'middle' and x_label['fill'] == 'var(--muted-foreground)'
    (y_label,) = [a for a in page.evaluate(ATTRS_JS, 'text.recharts-label') if 'transform' in a]
    assert y_label['transform'].startswith('rotate(-90')
    assert y_label['style'] == 'text-anchor: middle;'
    assert float(y_label['y']) == pytest.approx(plot['y'] + plot['height'] / 2, abs=0.5)
    # in layer 2000, each after the tick labels of its axis
    kinds = page.evaluate("() => [...document.querySelectorAll('g.recharts-zIndex-layer_2000 > *')].map((e) => e.getAttribute('class').split(' ').pop())")
    assert kinds == ['recharts-xAxis-tick-labels', 'recharts-label', 'recharts-yAxis-tick-labels', 'recharts-label']


def test_ticks_set_on_an_axis_are_the_ticks_drawn(draw):
    spec = bar_spec()
    spec['axes'][1].update(domain=[0, 100], ticks=[0, 25, 100])
    page = draw(spec)
    ticks = page.evaluate("() => [...document.querySelectorAll('.recharts-yAxis-tick-labels tspan')].map((t) => t.textContent)")
    assert ticks == ['0', '25', '100']


# ---------------------------------------------------------------- ScatterChart, Scatter and ZAxis

# d3-shape 3.2 symbol().type(...).size(100)(), taken with node from the package Recharts draws its symbols with
D3_SYMBOLS = {
    'circle': 'M5.642,0A5.642,5.642,0,1,1,-5.642,0A5.642,5.642,0,1,1,5.642,0',
    'cross': 'M-6.708,-2.236L-2.236,-2.236L-2.236,-6.708L2.236,-6.708L2.236,-2.236L6.708,-2.236L6.708,2.236L2.236,2.236L2.236,6.708L-2.236,6.708L-2.236,2.236L-6.708,2.236Z',
    'diamond': 'M0,-9.306L5.373,0L0,9.306L-5.373,0Z',
    'square': 'M-5,-5h10v10h-10Z',
    'star': 'M0,-9.438L2.119,-2.917L8.976,-2.917L3.429,1.114L5.548,7.636L0,3.605L-5.548,7.636L-3.429,1.114L-8.976,-2.917L-2.119,-2.917Z',
    'triangle': 'M0,-8.774L7.598,4.387L-7.598,4.387Z',
    'wye': 'M2.699,1.558L2.699,6.955L-2.699,6.955L-2.699,1.558L-7.373,-1.141L-4.674,-5.815L0,-3.116L4.674,-5.815L7.373,-1.141Z',
}

POINTS = [{'name': 'Alpha', 'x': 100, 'y': 20, 'z': 10}, {'name': 'Beta', 'x': 200, 'y': 60, 'z': 40}, {'name': 'Gamma', 'x': 300, 'y': 100, 'z': 20}]


def scatter_spec(z=True, **over):
    axes = [{'component': 'XAxis', 'type': 'number', 'dataKey': 'x', 'name': 'Cost', 'domain': [0, 400], 'ticks': [0, 100, 200, 300, 400], 'tickLine': False, 'axisLine': False},
            {'component': 'YAxis', 'type': 'number', 'dataKey': 'y', 'name': 'Value', 'domain': [0, 100], 'ticks': [0, 50, 100], 'tickLine': False, 'axisLine': False}]
    if z:
        axes.append({'component': 'ZAxis', 'type': 'number', 'dataKey': 'z', 'name': 'Effort', 'range': [60, 400]})
    spec = {'type': 'scatter', 'component': 'ScatterChart', 'config': {'y': {'label': 'Value', 'color': 'var(--chart-1)'}}, 'data': POINTS,
            'props': {'accessibilityLayer': True, 'margin': {'top': 10, 'right': 40, 'bottom': 10, 'left': 10}},
            'series': [{'component': 'Scatter', 'fill': 'var(--color-y)', 'labelList': [{'dataKey': 'name', 'position': 'right', 'offset': 8, 'fontSize': 12}]}],
            'axes': axes, 'grid': {'component': 'CartesianGrid'}, 'tooltip': {'cursor': False}, 'legend': None, 'labels': []}
    spec.update(over)
    return spec


SYMBOLS_JS = """() => [...document.querySelectorAll('.recharts-scatter-symbol')].map((g) => { const p = g.querySelector('path'); return {
  cx: +p.getAttribute('cx'), cy: +p.getAttribute('cy'), d: p.getAttribute('d'), w: +p.getAttribute('width'), label: g.getAttribute('aria-label'),
  role: g.getAttribute('role'), tabindex: g.getAttribute('tabindex') } })"""


def test_scatter_points_sit_at_their_data_values_and_bubble_size_comes_from_the_z_axis(draw):
    page = draw(scatter_spec())
    plot = page.evaluate(PLOT_JS)
    pts = page.evaluate(SYMBOLS_JS)
    assert len(pts) == 3
    for pt, row in zip(pts, POINTS):
        assert pt['cx'] == pytest.approx(plot['x'] + plot['width'] * row['x'] / 400, abs=0.5)
        assert pt['cy'] == pytest.approx(plot['y'] + plot['height'] * (1 - row['y'] / 100), abs=0.5)
    # ZAxis domain [0, max z] onto the area range [60, 400]: the symbol's area is size, its width 2 * sqrt(size / pi)
    import math
    for pt, row in zip(pts, POINTS):
        area = 60 + (400 - 60) * row['z'] / 40
        assert pt['w'] == pytest.approx(2 * math.sqrt(area / math.pi), abs=0.01)
    assert pts[1]['w'] > pts[2]['w'] > pts[0]['w']


def test_scatter_without_a_z_axis_draws_every_point_at_the_implicit_size_of_64(draw):
    page = draw(scatter_spec(z=False))
    pts = page.evaluate(SYMBOLS_JS)
    assert {pt['d'] for pt in pts} == {'M4.514,0A4.514,4.514,0,1,1,-4.514,0A4.514,4.514,0,1,1,4.514,0'}


def test_symbols_are_the_paths_d3_shape_draws(draw):
    page = draw(scatter_spec(z=False))
    got = page.evaluate("(names) => Object.fromEntries(names.map((n) => [n, window.FlaskBasecoatChart.d3.symbol(n, 100)]))", list(D3_SYMBOLS))
    assert got == D3_SYMBOLS
    assert page.evaluate("window.FlaskBasecoatChart.d3.symbol('no-such-shape', 100)") == D3_SYMBOLS['circle']  # unknown: a circle, as Recharts


def test_scatter_shape_prop_changes_the_symbol(draw):
    spec = scatter_spec(z=False)
    spec['series'][0]['shape'] = 'diamond'
    page = draw(spec)
    assert page.evaluate(SYMBOLS_JS)[0]['d'].startswith('M0,-')  # a diamond starts at its top vertex


def test_each_point_is_a_named_focusable_image_with_one_in_the_tab_order(draw):
    page = draw(scatter_spec())
    pts = page.evaluate(SYMBOLS_JS)
    assert [p['role'] for p in pts] == ['img'] * 3
    assert pts[0]['label'] == 'Alpha: Cost 100, Value 20, Effort 10'
    assert pts[2]['label'] == 'Gamma: Cost 300, Value 100, Effort 20'
    assert [p['tabindex'] for p in pts] == ['0', '-1', '-1']
    assert page.evaluate("document.querySelector('svg.recharts-surface').hasAttribute('tabindex')") is False


def test_hovering_a_point_shows_both_values_and_the_size(draw):
    page = draw(scatter_spec())
    page.locator('.recharts-scatter-symbol').nth(1).hover()
    tip = page.locator('.recharts-tooltip-wrapper .cn-chart-tooltip')
    tip.wait_for()
    assert tip.inner_text().split() == ['Cost', '200', 'Value', '60', 'Effort', '40']
    page.mouse.move(0, 0)
    page.wait_for_function("() => getComputedStyle(document.querySelector('.recharts-tooltip-wrapper')).visibility === 'hidden'")


def test_focus_shows_the_tooltip_and_the_arrow_keys_move_between_points(draw):
    page = draw(scatter_spec())
    page.locator('.recharts-scatter-symbol').first.focus()
    tip = page.locator('.recharts-tooltip-wrapper .cn-chart-tooltip')
    tip.wait_for()
    assert tip.inner_text().split()[:2] == ['Cost', '100']
    page.keyboard.press('ArrowRight')
    page.wait_for_function("() => document.activeElement.getAttribute('aria-label').startsWith('Beta')")
    assert tip.inner_text().split()[:2] == ['Cost', '200']
    assert [p['tabindex'] for p in page.evaluate(SYMBOLS_JS)] == ['-1', '0', '-1']
    page.keyboard.press('End')
    page.wait_for_function("() => document.activeElement.getAttribute('aria-label').startsWith('Gamma')")
    page.keyboard.press('ArrowRight')  # past the last point: stays
    assert page.evaluate("document.activeElement.getAttribute('aria-label')").startswith('Gamma')
    page.keyboard.press('Home')
    page.wait_for_function("() => document.activeElement.getAttribute('aria-label').startsWith('Alpha')")
    page.locator('body').click(position={'x': 5, 'y': 5})  # focus leaves the chart: the tooltip hides
    page.wait_for_function("() => getComputedStyle(document.querySelector('.recharts-tooltip-wrapper')).visibility === 'hidden'")


def test_points_have_no_keyboard_layer_when_accessibility_layer_is_off(draw):
    page = draw(scatter_spec(props={'accessibilityLayer': False, 'margin': {'top': 10, 'right': 40, 'bottom': 10, 'left': 10}}))
    # Recharts' own switch: without accessibilityLayer the chart has no roles, labels or tab stops
    assert page.evaluate("document.querySelectorAll('.recharts-scatter-symbol[tabindex], .recharts-scatter-symbol[role]').length") == 0
    assert page.evaluate("document.querySelectorAll('.recharts-scatter-symbol').length") == 3


def test_payload_field_formatter_names_the_hovered_point_in_the_tooltip(draw):
    spec = scatter_spec()
    spec['tooltip'] = {'cursor': False, 'labelFormatter': {'$fn': 'payloadField', 'key': 'name'}}
    page = draw(spec)
    page.locator('.recharts-scatter-symbol').nth(1).hover()
    tip = page.locator('.recharts-tooltip-wrapper .cn-chart-tooltip')
    tip.wait_for()
    assert tip.inner_text().split('\n')[0] == 'Beta'


# ---------------------------------------------------------------- the "View" toggle of a form: chart or table

def test_view_toggle_swaps_the_chart_panel_and_the_table_panel(server, browser):
    base, specs = server
    specs['views'] = bar_spec()
    page = browser.new_page(viewport={'width': 700, 'height': 600})
    try:
        page.goto(f'{base}/v/views')
        page.wait_for_function("() => document.querySelector('svg.recharts-surface')?.getBoundingClientRect().width > 0")
        assert page.locator('#chart-panel').is_visible() and not page.locator('#table-panel').is_visible()
        page.locator('[data-slot=toggle-group-item]', has_text='Table').click()
        assert page.locator('#table-panel').is_visible() and not page.locator('#chart-panel').is_visible()
        page.locator('[data-slot=toggle-group-item]', has_text='Table').click()  # pressing the chosen view again keeps it
        assert page.locator('#table-panel').is_visible()
        assert page.locator('[data-slot=toggle-group-item][data-state=on]').inner_text() == 'Table'
        page.locator('[data-slot=toggle-group-item]', has_text='Chart').click()
        assert page.locator('#chart-panel').is_visible() and not page.locator('#table-panel').is_visible()
        # the chart is drawn again at its width when it comes back into view
        page.wait_for_function("() => document.querySelector('svg.recharts-surface')?.getBoundingClientRect().width > 400")
    finally:
        page.close()


# ---------------------------------------------------------------- the three charts of R18 and R19, on their pages

import re
import subprocess
import sys

from flask_basecoat.charts import bridge_rows, load_spec, matrix_rows

PAGE_NAMES = ('chart-scatter-default', 'chart-matrix-two-by-two', 'chart-bar-waterfall')
COLOUR_JS = """(v) => { const cv = document.createElement('canvas'); cv.width = cv.height = 1; const cx = cv.getContext('2d', { willReadFrequently: true });
  cx.fillStyle = '#000'; cx.fillStyle = v; cx.fillRect(0, 0, 1, 1); return [...cx.getImageData(0, 0, 1, 1).data].slice(0, 3) }"""


def luminance(rgb):
    lin = [(c / 255 / 12.92) if c / 255 <= 0.03928 else ((c / 255 + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.fixture
def chart_page(server, browser):
    """chart_page(name, width=1440, theme='light') -> the gallery page of a chart, drawn."""
    base, _ = server
    pages = []

    def go(name, width=1440, theme='light'):
        page = browser.new_page(viewport={'width': width, 'height': 1000})
        pages.append(page)
        page.goto(f'{base}/basecoat/charts/{name}?theme={theme}')
        page.wait_for_function("() => { const s = document.querySelector('svg.recharts-surface'); return s && s.getBoundingClientRect().width > 0 }")
        page.wait_for_timeout(150)
        return page

    yield go
    for pg in pages:
        pg.close()


def plot_of(page):
    return page.evaluate(PLOT_JS)


# ---- the two-by-two matrix (R18)

def test_matrix_spec_is_ten_options_with_both_values_and_a_size():
    spec = load_spec('chart-matrix-two-by-two')
    assert spec['component'] == 'ScatterChart' and len(spec['data']) == 10
    assert len({d['option'] for d in spec['data']}) == 10
    assert all({'option', 'cost', 'value', 'effort'} <= set(d) for d in spec['data'])
    assert {a['component'] for a in spec['axes']} == {'XAxis', 'YAxis', 'ZAxis'}


def test_matrix_table_lists_every_point_with_both_values(chart_page):
    spec = load_spec('chart-matrix-two-by-two')
    page = chart_page('chart-matrix-two-by-two')
    assert not page.locator('table[data-slot=table]').is_visible()  # the chart is the default view
    page.locator('[data-slot=toggle-group-item]', has_text='Table').click()
    assert page.locator('table[data-slot=table]').is_visible() and not page.locator('svg.recharts-surface').is_visible()
    header = page.locator('table[data-slot=table] thead th').all_inner_texts()
    assert header == ['Option', 'Cost to deliver ($ thousands)', 'Value to the business (score)', 'Effort (person-weeks)', 'Quadrant']
    rows = [[c.strip() for c in r] for r in page.locator('table[data-slot=table] tbody tr').evaluate_all("(trs) => trs.map((tr) => [...tr.children].map((c) => c.textContent))")]
    assert len(rows) == len(spec['data']) == 10
    for d, row in zip(spec['data'], rows):
        assert row[:4] == [d['option'], str(d['cost']), str(d['value']), str(d['effort'])]
    # the table and the chart name the same points with the same values
    page.locator('[data-slot=toggle-group-item]', has_text='Chart').click()
    page.wait_for_function("() => document.querySelector('svg.recharts-surface')?.getBoundingClientRect().width > 100")
    labels = page.locator('.recharts-scatter-symbol').evaluate_all("(gs) => gs.map((g) => g.getAttribute('aria-label'))")
    for d, label in zip(spec['data'], labels):
        assert label == f"{d['option']}: Cost {d['cost']}, Value {d['value']}, Effort (person-weeks) {d['effort']}"


def test_matrix_quadrants_follow_the_thresholds():
    spec = load_spec('chart-matrix-two-by-two')
    rows = {r['name']: r['quadrant'] for r in matrix_rows(spec)['rows']}
    assert rows['SSO rollout'] == 'Quick wins' and rows['Data lake'] == 'Major projects'
    assert rows['Wiki cleanup'] == 'Fill-ins' and rows['Custom BI suite'] == 'Reconsider'
    assert set(rows.values()) == {'Quick wins', 'Major projects', 'Fill-ins', 'Reconsider'}


@pytest.mark.parametrize('theme', ['light', 'dark'])
def test_matrix_quadrant_labels_are_on_a_chart_tint_at_a_tenth_with_readable_text(chart_page, theme):
    page = chart_page('chart-matrix-two-by-two', theme=theme)
    areas = page.evaluate(ATTRS_JS, 'path.recharts-reference-area-rect')
    assert [a['fill'] for a in areas] == ['var(--chart-2)', 'var(--chart-1)', 'var(--chart-4)', 'var(--chart-5)']
    assert {a['fill-opacity'] for a in areas} == {'0.1'}
    texts = page.locator('g.recharts-zIndex-layer_2000 > text.recharts-label').evaluate_all("(ts) => ts.slice(0, 4).map((t) => t.textContent)")
    assert texts == ['Quick wins', 'Major projects', 'Fill-ins', 'Reconsider']
    plot = plot_of(page)
    bg = page.evaluate(COLOUR_JS, page.evaluate("getComputedStyle(document.querySelector('[data-slot=card]')).backgroundColor"))
    text_rgb = page.evaluate(COLOUR_JS, page.evaluate("getComputedStyle(document.querySelector('g.recharts-zIndex-layer_2000 > text.recharts-label')).fill"))
    for area in areas:
        token = page.evaluate(COLOUR_JS, page.evaluate("(v) => getComputedStyle(document.documentElement).getPropertyValue(v.slice(4, -1))", area['fill']))
        tinted = [round(0.1 * t + 0.9 * b) for t, b in zip(token, bg)]
        assert contrast(text_rgb, tinted) >= 4.5, (area['fill'], contrast(text_rgb, tinted))
        # the tint is a label band, not a wash over the quadrant: under a tenth of the plot's height
        assert float(area['height']) < plot['height'] * 0.1
    # the plot background itself is untinted: no background rectangle, and the only fills in the plot are the four bands
    assert page.locator('.recharts-cartesian-grid-bg').count() == 0
    assert page.evaluate("document.querySelectorAll('svg.recharts-surface rect[fill]').length") == 0


def test_matrix_has_a_square_plot_a_threshold_line_on_each_axis_and_axis_titles_in_words(chart_page):
    page = chart_page('chart-matrix-two-by-two')
    plot = plot_of(page)
    assert plot['width'] == pytest.approx(plot['height'], abs=1)
    lines = page.evaluate(ATTRS_JS, '.recharts-reference-line-line')
    assert len(lines) == 2
    vertical = next(line for line in lines if line['x1'] == line['x2'])
    horizontal = next(line for line in lines if line['y1'] == line['y2'])
    assert float(vertical['x1']) == pytest.approx(plot['x'] + plot['width'] * 200 / 400, abs=0.5)    # cost threshold 200
    assert float(horizontal['y1']) == pytest.approx(plot['y'] + plot['height'] * (1 - 50 / 100), abs=0.5)  # value threshold 50
    titles = page.locator('g.recharts-zIndex-layer_2000 > text.recharts-label').evaluate_all("(ts) => ts.slice(4).map((t) => t.textContent)")
    assert titles == ['Cost to deliver ($ thousands)', 'Value to the business (score)']


def test_matrix_labels_every_point_and_sizes_the_bubbles_from_effort(chart_page):
    spec = load_spec('chart-matrix-two-by-two')
    page = chart_page('chart-matrix-two-by-two')
    drawn = page.locator('g.recharts-label-list text').evaluate_all("(ts) => ts.map((t) => t.textContent)")
    assert drawn == [d['option'] for d in spec['data']]
    pts = page.evaluate(SYMBOLS_JS)
    widths = [p['w'] for p in pts]
    by_effort = sorted(range(10), key=lambda i: spec['data'][i]['effort'])
    assert [widths[i] for i in by_effort] == sorted(widths)
    assert max(widths) > 2 * min(widths)


def test_matrix_tooltip_shows_the_name_and_both_values(chart_page):
    spec = load_spec('chart-matrix-two-by-two')
    page = chart_page('chart-matrix-two-by-two')
    page.locator('.recharts-scatter-symbol').nth(2).hover()
    tip = page.locator('.recharts-tooltip-wrapper .cn-chart-tooltip')
    tip.wait_for()
    d = spec['data'][2]
    assert tip.inner_text().split('\n')[0] == d['option']
    assert re.findall(r'\d+', tip.inner_text()) == [str(d['cost']), str(d['value']), str(d['effort'])]


def test_matrix_at_390_keeps_its_square_and_scrolls_inside_a_named_region(chart_page):
    page = chart_page('chart-matrix-two-by-two', width=390)
    region = page.locator('[data-entelim-form]')
    assert region.get_attribute('role') == 'region' and region.get_attribute('aria-label') == 'Value against cost matrix'
    assert region.get_attribute('tabindex') == '0'
    assert page.evaluate("getComputedStyle(document.querySelector('[data-entelim-form]')).overflowX") == 'auto'
    assert page.evaluate("(() => { const r = document.querySelector('[data-entelim-form]'); return r.scrollWidth > r.clientWidth })()")
    plot = plot_of(page)
    assert plot['width'] == pytest.approx(plot['height'], abs=1) and plot['width'] > 400  # the plot keeps its size, it does not shrink or stack
    assert page.evaluate("document.documentElement.scrollWidth - window.innerWidth") <= 1  # the page itself does not scroll sideways
    assert page.locator('[data-entelim-form]').count() == 1


# ---- the cost bridge (R19)

def test_bridge_steps_and_the_total_equal_the_sum_of_their_steps():
    spec = load_spec('chart-bar-waterfall')
    b = bridge_rows(spec)
    assert [(r['step'], r['kind'], r['change'], r['total']) for r in b['rows']] == [
        ('Current cost', 'total', None, 4800), ('Licences', 'fall', -900, 3900), ('Hosting', 'fall', -700, 3200),
        ('Support', 'fall', -500, 2700), ('Migration', 'rise', 650, 3350), ('Three-year total', 'total', None, 3350)]
    assert [r['label'] for r in b['rows']] == ['$4,800k', '-$900k', '-$700k', '-$500k', '+$650k', '$3,350k']
    steps = [r['change'] for r in b['rows'] if r['change'] is not None]
    assert b['rows'][0]['total'] + sum(steps) == b['rows'][-1]['total'] == 3350
    assert b['consistent'] and b['summary'] == 'Starts at 4,800, falls by 2,100, rises by 650 and ends at 3,350'
    # the data the chart draws: the base is the lower edge of each floating bar, a bar's length is its step
    rows = {d['step']: d for d in spec['data']}
    assert [rows[s]['base'] for s in ('Licences', 'Hosting', 'Support', 'Migration')] == [3900, 3200, 2700, 2700]
    assert [rows[s]['fall'] for s in ('Licences', 'Hosting', 'Support')] == [900, 700, 500] and rows['Migration']['rise'] == 650
    assert rows['Current cost']['total'] == 4800 and rows['Three-year total']['total'] == 3350


def test_bridge_bars_are_drawn_at_the_values_of_their_steps(chart_page):
    spec = load_spec('chart-bar-waterfall')
    page = chart_page('chart-bar-waterfall')
    plot = plot_of(page)
    rects = page.evaluate("""() => [...document.querySelectorAll('g.recharts-bar')].map((g) => [...g.querySelectorAll('path.recharts-rectangle')].map((p) => ({
      fill: p.getAttribute('fill'), x: +p.getAttribute('x'), y: +p.getAttribute('y'), h: +p.getAttribute('height') })))""")
    base, fall, rise, total = rects
    assert [r['fill'] for r in base] == ['transparent'] * 5 or all(r['fill'] == 'transparent' for r in base)
    assert {r['fill'] for r in fall} == {'var(--color-fall)'} and {r['fill'] for r in rise} == {'var(--color-rise)'} and {r['fill'] for r in total} == {'var(--color-total)'}
    assert (len(fall), len(rise), len(total)) == (3, 1, 2)
    bottom = plot['y'] + plot['height']
    per_unit = total[0]['h'] / 4800                       # pixels per $ thousand, from the first total
    assert total[0]['y'] == pytest.approx(bottom - 4800 * per_unit, abs=0.6)
    assert total[1]['h'] == pytest.approx(3350 * per_unit, abs=0.6)
    for bar, (top, size) in zip(fall + rise, [(4800, 900), (3900, 700), (3200, 500), (3350, 650)]):
        assert bar['h'] == pytest.approx(size * per_unit, abs=0.6)
        assert bar['y'] == pytest.approx(bottom - top * per_unit, abs=0.6)
    drawn = page.locator('g.recharts-label-list text').evaluate_all("(ts) => ts.map((t) => t.textContent)")
    assert drawn == ['-$900k', '-$700k', '-$500k', '+$650k', '$4,800k', '$3,350k']
    # the connectors sit at the running total after each step
    lines = page.evaluate(ATTRS_JS, '.recharts-reference-line-line')
    assert len(lines) == 5
    assert [round((bottom - float(line['y1'])) / per_unit) for line in lines] == [4800, 3900, 3200, 2700, 3350]
    assert all(line['y1'] == line['y2'] and line['stroke'] == 'var(--muted-foreground)' for line in lines)
    assert spec['config']['fall']['color'] == 'var(--chart-5)' and spec['config']['rise']['color'] == 'var(--chart-2)' and spec['config']['total']['color'] == 'var(--primary)'


def test_bridge_colours_are_tokens_and_the_base_is_in_no_tooltip_legend_or_table(chart_page):
    page = chart_page('chart-bar-waterfall')
    css = page.evaluate("document.querySelector('[data-slot=chart] > style').textContent")
    assert '--color-fall: var(--chart-5)' in css and '--color-rise: var(--chart-2)' in css and '--color-total: var(--primary)' in css
    assert '--color-base' not in css
    legend = page.locator('.recharts-legend-wrapper').inner_text().split()
    assert legend == ['Decrease', 'Increase', 'Total']
    page.locator('g.recharts-bar').nth(1).locator('path.recharts-rectangle').nth(1).hover()  # the Hosting fall
    tip = page.locator('.recharts-tooltip-wrapper .cn-chart-tooltip')
    tip.wait_for()
    assert tip.inner_text().split() == ['Hosting', 'Decrease', '700']
    header = page.locator('table[data-slot=table] thead th').all_inner_texts()
    assert header == ['Step', 'Change', 'Running total']
    rows = page.locator('table[data-slot=table] tbody tr').evaluate_all("(trs) => trs.map((tr) => [...tr.children].map((c) => c.textContent.trim()))")
    assert rows == [['Current cost', '$4,800k', '4,800'], ['Licences', '-$900k', '3,900'], ['Hosting', '-$700k', '3,200'], ['Support', '-$500k', '2,700'],
                    ['Migration', '+$650k', '3,350'], ['Three-year total', '$3,350k', '3,350']]


def test_bridge_reads_at_390(chart_page):
    page = chart_page('chart-bar-waterfall', width=390)
    assert page.evaluate("document.documentElement.scrollWidth - window.innerWidth") <= 1
    labels = page.locator('.recharts-xAxis-tick-labels tspan').evaluate_all("(ts) => ts.map((t) => t.textContent)")
    assert labels == ['Current cost', 'Licences', 'Hosting', 'Support', 'Migration', 'Three-year total']  # interval 0: every step is named


# ---- the plain scatter chart, the gallery and the page check

def test_plain_scatter_draws_ten_points_at_the_implicit_size(chart_page):
    page = chart_page('chart-scatter-default')
    pts = page.evaluate(SYMBOLS_JS)
    assert len(pts) == 10 and {p['d'] for p in pts} == {'M4.514,0A4.514,4.514,0,1,1,-4.514,0A4.514,4.514,0,1,1,4.514,0'}
    assert page.locator('.recharts-reference-line, .recharts-reference-area').count() == 0


def test_gallery_lists_the_three_charts_and_compares_them_with_their_oracles(server):
    import urllib.request
    base, _ = server
    index = urllib.request.urlopen(f'{base}/basecoat/charts/').read().decode()
    for name in PAGE_NAMES:
        assert f'/basecoat/charts/{name}"' in index
        assert f'/basecoat/compare/{name}' in index
        oracle = urllib.request.urlopen(f'{base}/basecoat/golden/charts-extra/{name}.html')
        assert oracle.status == 200
        assert b'recharts-surface' in oracle.read()
        assert urllib.request.urlopen(f'{base}/basecoat/compare/{name}').status == 200
    assert 'id="scatter"' in index and 'id="matrix"' in index
    assert index.count('md:col-span-2 lg:col-span-3') >= 3 + 2  # the three upstream full-width charts and the matrix and the bridge


@pytest.mark.parametrize('name', PAGE_NAMES)
def test_check_page_prints_shadcn_composed_in_the_browser(server, name):
    base, _ = server
    out = subprocess.run([sys.executable, str(ROOT / 'compliance/scripts/check_page.py'), f'{base}/basecoat/charts/{name}', '--nearest', name, '--browser'],
                         capture_output=True, text=True, cwd=ROOT, timeout=240).stdout
    assert 'content fidelity: 100.0%' in out, out
    assert out.strip().splitlines()[-1] == 'SHADCN COMPOSED', out
