"""Chart gallery routes, the chart spec macros and the shipped chart specs."""
import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLDEN_CHARTS = ROOT / 'compliance' / 'golden' / 'out' / 'charts'
CHART_NAMES = sorted(p.stem for p in GOLDEN_CHARTS.glob('chart-*.html') if not p.name.endswith('.hover.html'))
FULL_WIDTH = {'chart-area-interactive', 'chart-bar-interactive', 'chart-line-interactive'}

SPEC = {
    'component': 'BarChart',
    'config': {'desktop': {'label': 'Desktop', 'color': 'var(--chart-1)'},
               'mobile': {'label': 'Mobile', 'theme': {'light': 'oklch(0.6 0.1 200)', 'dark': 'oklch(0.7 0.1 200)'}},
               'visitors': {'label': 'Visitors'}},
    'data': [{'month': 'January', 'desktop': 186, 'mobile': 80, 'note': '</script><b>'}],
    'props': {'accessibilityLayer': True},
    'series': [{'component': 'Bar', 'dataKey': 'desktop', 'fill': 'var(--color-desktop)', 'radius': 4}],
    'axes': [{'component': 'XAxis', 'dataKey': 'month', 'tickFormatter': {'$fn': 'slice', 'start': 0, 'end': 3}}],
    'grid': {'component': 'CartesianGrid', 'vertical': False},
    'tooltip': {'cursor': False},
    'legend': None,
}


@pytest.fixture(scope='module')
def app():
    from flask_basecoat.testing import make_app
    return make_app()


@pytest.fixture(scope='module')
def client(app):
    with app.test_client() as c:
        yield c


def render(app, source, **ctx):
    with app.test_request_context('/'):
        return app.jinja_env.from_string("{% import 'basecoat/index.html' as ui %}" + source).render(**ctx)


def test_there_are_seventy_upstream_charts():
    assert len(CHART_NAMES) == 70


@pytest.mark.parametrize('name', CHART_NAMES)
def test_chart_page_renders_in_its_frame(client, name):
    r = client.get(f'/basecoat/charts/{name}')
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    frame = 'full' if name in FULL_WIDTH else 'regular'
    width = '1232px' if name in FULL_WIDTH else '384px'
    assert f'<div data-chart-frame="{frame}" style="width: {width};">' in body
    assert 'data-slot="card"' in body and 'data-slot="chart"' in body
    spec = re.search(r'<script type="application/json" data-chart-spec>(.*?)</script>', body, re.S)
    assert spec, 'chart spec missing'
    data = json.loads(spec.group(1))
    assert data['component'].endswith('Chart')
    assert data['series']


def test_unknown_chart_is_404(client):
    assert client.get('/basecoat/charts/chart-does-not-exist').status_code == 404


def test_charts_index_groups_every_chart(client):
    r = client.get('/basecoat/charts/')
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    for group in ('area', 'bar', 'line', 'pie', 'radar', 'radial', 'tooltip'):
        assert f'id="{group}"' in body, group
    for name in CHART_NAMES:
        assert f'/basecoat/charts/{name}"' in body, name
    # full-width charts span the row of the 3-column grid
    for name in FULL_WIDTH:
        block = body[:body.index(f'/basecoat/charts/{name}"')]
        assert block.rfind('md:col-span-2 lg:col-span-3') > block.rfind('<section'), name
    assert body.count('data-slot="chart"') == 70


def test_gallery_index_has_a_charts_section(client):
    body = client.get('/basecoat/').get_data(as_text=True)
    assert '>Charts <' in body
    assert '/basecoat/charts/' in body
    for name in CHART_NAMES:
        assert f'>{name}<' in body, name


def test_compare_works_for_charts(client):
    r = client.get('/basecoat/compare/chart-area-default')
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert '/basecoat/golden/charts/chart-area-default.html' in body
    assert 'src="/basecoat/charts/chart-area-default"' in body
    assert client.get('/basecoat/golden/charts/chart-area-default.html').status_code == 200


def test_chart_example_page_draws_six_charts(client):
    body = client.get('/basecoat/components/chart').get_data(as_text=True)
    assert body.count('data-chart-spec') == 6


def test_chart_from_spec_renders_the_container(app):
    html = render(app, "{{ ui.chart_from_spec(spec, id='visitors', class='aspect-auto h-[250px] w-full') }}", spec=SPEC)
    assert html.startswith('<div data-slot="chart"')
    assert 'data-chart="chart-visitors"' in html
    cls = re.search(r'class="([^"]*)"', html).group(1).split()
    assert {'cn-chart', 'flex', 'justify-center', 'text-xs', 'aspect-auto', 'h-[250px]', 'w-full'} <= set(cls)
    assert 'aspect-video' not in cls  # merged away by aspect-auto, as cn() does upstream
    assert '<div class="recharts-responsive-container" style="width: 100%; height: 100%; min-width: 0px;">' in html
    assert '<div class="recharts-wrapper"></div>' in html


def test_chart_from_spec_embeds_the_spec_safely(app):
    html = render(app, "{{ ui.chart_from_spec(spec, id='visitors') }}", spec=SPEC)
    script = re.search(r'<script type="application/json" data-chart-spec>(.*?)</script>', html, re.S).group(1)
    assert '</script>' not in script
    assert json.loads(script) == SPEC


def test_chart_style_matches_chart_container(app):
    html = render(app, "{{ ui.chart_style('chart-visitors', spec.config) }}", spec=SPEC)
    expected = ('<style>\n [data-chart=chart-visitors] {\n  --color-desktop: var(--chart-1);\n  --color-mobile: oklch(0.6 0.1 200);\n}\n\n'
                '\n.dark [data-chart=chart-visitors] {\n  --color-desktop: var(--chart-1);\n  --color-mobile: oklch(0.7 0.1 200);\n}\n</style>')
    assert html == expected
    assert render(app, "{{ ui.chart_style('chart-x', {'a': {'label': 'A'}}) }}") == ''


def test_generated_chart_ids_are_unique(app):
    html = render(app, "{{ ui.chart_from_spec(spec) }}{{ ui.chart_from_spec(spec) }}", spec=SPEC)
    ids = re.findall(r'data-chart="([^"]+)"', html)
    assert len(ids) == 2 and ids[0] != ids[1]


@pytest.mark.parametrize('name', CHART_NAMES)
def test_shipped_spec_has_no_function_source(name):
    from flask_basecoat.charts import FORMATTERS, load_spec
    spec = load_spec(name)

    def walk(o):
        if isinstance(o, dict):
            if '$fn' in o:
                assert o['$fn'] in FORMATTERS, o['$fn']
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
        elif isinstance(o, str):
            yield o

    for s in walk(spec):
        assert '=>' not in s, s[:80]
        assert 'unresolved' not in s


def test_runtime_registry_covers_every_formatter():
    from flask_basecoat.charts import FORMATTERS
    src = (ROOT / 'flask_basecoat/static/js/src/components/chart-format.js').read_text(encoding='utf8')
    chart = (ROOT / 'flask_basecoat/static/js/src/components/chart.js').read_text(encoding='utf8')
    for name in FORMATTERS:
        assert re.search(rf'\b{name}\b\s*[:(]', src + chart), name


def test_runtime_spec_maps_upstream_function_sources():
    from flask_basecoat.charts import runtime_spec
    recipe = json.loads((ROOT / 'compliance/recipes/charts/chart-area-default.json').read_text(encoding='utf8'))
    spec = runtime_spec(recipe)
    assert spec['axes'][0]['tickFormatter'] == {'$fn': 'slice', 'start': 0, 'end': 3}
    assert spec['tooltip']['$class'] == 'cn-chart-tooltip grid min-w-32 items-start'
    with pytest.raises(KeyError):
        from flask_basecoat.charts import function_ref
        function_ref('(value) => value.toUpperCase()')
