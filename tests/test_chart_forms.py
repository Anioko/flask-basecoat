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
