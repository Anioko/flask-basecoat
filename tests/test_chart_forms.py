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
