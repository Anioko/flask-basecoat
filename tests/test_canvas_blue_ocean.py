import copy
import json
import pathlib
import re
from threading import Thread

import pytest
from lxml import html as lxml_html
from werkzeug.serving import make_server

from flask import render_template
from flask_basecoat import canvases as registry
from flask_basecoat.testing import make_app

SLUG = "blue-ocean"
ENTRY = next(c for c in registry.canvases() if c["slug"] == SLUG)


def page(data=None):
    app = make_app()
    with app.test_request_context(f"/examples/canvas/{SLUG}"):
        return render_template(ENTRY["page"], data=data or registry.canvas_data(SLUG), entry=ENTRY)


def doc(data=None):
    return lxml_html.fromstring(page(data))


def list_rows(d):
    return [[c.text_content().strip() for c in tr.xpath("./th|./td")] for tr in d.xpath("//*[@data-canvas-rows]//tr")]


@pytest.fixture(scope="module")
def base():
    server = make_server("127.0.0.1", 0, make_app())
    Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture(scope="module")
def browser():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def open_page(browser, base, width=1440, height=900):
    pg = browser.new_page(viewport={"width": width, "height": height})
    pg.errors = []
    pg.on("pageerror", lambda e: pg.errors.append(str(e)))
    pg.goto(f"{base}/examples/canvas/{SLUG}")
    pg.wait_for_selector("[data-entelim-form]")
    pg.wait_for_timeout(250)
    return pg



def chart_spec(d):
    return json.loads(d.xpath('//*[@data-entelim-form]//script[@data-chart-spec]')[0].text)


def test_one_chart_with_a_value_curve_per_company_in_chart_tokens():
    data = registry.canvas_data(SLUG)
    d = doc(data)
    assert len(d.xpath('//*[@data-entelim-form]//*[@data-slot="chart"]')) == 1
    spec = chart_spec(d)
    assert spec['type'] == 'line' and len(spec['series']) == len(data['companies']) >= 3
    assert [p['factor'] for p in spec['data']] == [f['name'] for f in data['factors']]
    for c in data['companies']:
        entry = spec['config'][c['key']]
        assert entry['label'] == c['name']
        colours = [entry.get('color')] + list((entry.get('theme') or {}).values())
        assert all(re.fullmatch(r'var\(--chart-[1-3]\)', x) for x in colours if x)
    assert all(0 <= v <= 10 for p in spec['data'] for k, v in p.items() if k != 'factor')


def test_four_actions_grid_is_eliminate_raise_reduce_create():
    d = doc()
    titles = [t.text_content().strip() for t in d.xpath('//*[@data-entelim-form]//*[@data-blue-ocean-action]/ancestor::*[@data-slot="card"]//*[@data-slot="card-title"]')]
    assert titles == ['Eliminate', 'Raise', 'Reduce', 'Create']
    data = registry.canvas_data(SLUG)
    for key in ('eliminate', 'raise', 'reduce', 'create'):
        notes = [li.text_content().strip() for li in d.xpath(f'//*[@data-blue-ocean-action="{key}"]/li')]
        assert notes == data['actions'][key]


def test_list_route_has_every_score_and_every_action():
    data = registry.canvas_data(SLUG)
    d = doc(data)
    heads = [h.text_content().strip() for h in d.xpath('//*[@data-slot="table"]//th[@scope="col"]')]
    assert heads == ['Part', 'Factor or action'] + [c['name'] for c in data['companies']]
    rows = list_rows(d)
    nf = len(data['factors'])
    assert len(rows) == nf + sum(len(v) for v in data['actions'].values())
    for f, row in zip(data['factors'], rows[:nf]):
        assert row[1] == f['name'] and row[2:] == [f"{f['scores'][c['key']]} of 10" for c in data['companies']]
    assert [r[1] for r in rows[nf:]] == data['actions']['eliminate'] + data['actions']['raise'] + data['actions']['reduce'] + data['actions']['create']


def test_content_comes_from_the_data():
    data = copy.deepcopy(registry.canvas_data(SLUG))
    data['actions']['create'].append('Zephyr-7 marker action')
    data['factors'][0]['name'] = 'Zephyr-7 marker factor'
    out = page(data)
    assert out.count('Zephyr-7 marker action') == 2          # the grid and the list
    assert out.count('Zephyr-7 marker factor') == 2          # the chart data and the list row


def test_browser_chart_draws_and_phone_scrolls(browser, base):
    pg = open_page(browser, base)
    pg.wait_for_selector('[data-entelim-form] .recharts-wrapper svg')
    assert pg.locator('[data-entelim-form] .recharts-line').count() == len(registry.canvas_data(SLUG)['companies'])
    pg.locator('[data-canvas-view] [data-slot="toggle-group-item"]', has_text='List').focus()
    pg.keyboard.press('Enter')
    assert pg.get_by_role('table').first.is_visible()
    pg.close()
    ph = open_page(browser, base, width=390, height=844)
    m = ph.evaluate("""() => { const r = document.querySelector('[data-entelim-form]');
      return {page: document.documentElement.scrollWidth - innerWidth, region: r.scrollWidth - r.clientWidth,
      cols: getComputedStyle(r.querySelector('.grid-cols-2')).gridTemplateColumns.split(' ').length}; }""")
    assert m['page'] <= 1 and m['region'] > 200 and m['cols'] == 2
    assert ph.errors == []
    ph.close()
