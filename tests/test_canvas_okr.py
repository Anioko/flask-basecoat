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

SLUG = "okr"
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



def score(kr):
    span = kr['target'] - kr['start']
    return max(0.0, min(1.0, (kr['current'] - kr['start']) / span)) if span else 1.0


def test_each_objective_has_three_to_five_key_results():
    data = registry.canvas_data(SLUG)
    assert len(data['objectives']) >= 2
    assert all(3 <= len(o['key_results']) <= 5 for o in data['objectives'])


def test_every_key_result_has_a_progress_bar_a_score_a_status_and_a_confidence():
    data = registry.canvas_data(SLUG)
    d = doc(data)
    krs = [kr for o in data['objectives'] for kr in o['key_results']]
    items = d.xpath('//*[@data-okr-kr]')
    assert len(items) == len(krs)
    bars = d.xpath('//*[@data-entelim-form]//*[@data-slot="progress"]')
    assert len(bars) == len(krs)
    for item, kr in zip(items, krs):
        text = item.text_content()
        assert f'{score(kr):.1f}' in text and kr['status'] in text         # a word as well as a colour
        bar = item.xpath('.//*[@data-slot="progress-indicator"]')[0]
        assert bar is not None
    assert len(d.xpath('//*[@data-entelim-form]//*[@data-slot="badge"][contains(., "Confidence")]')) == len(data['objectives'])


def test_list_route_is_a_table_of_the_same_key_results():
    data = registry.canvas_data(SLUG)
    d = doc(data)
    krs = [(o, kr) for o in data['objectives'] for kr in o['key_results']]
    rows = list_rows(d)
    assert len(rows) == len(krs)
    heads = [h.text_content().strip() for h in d.xpath('//*[@data-slot="table"]//th[@scope="col"]')]
    assert heads == ['Objective', 'Owner', 'Confidence', 'Key result', 'Result owner', 'Start', 'Now', 'Target', 'Score', 'Status', 'Initiatives']
    for (o, kr), row in zip(krs, rows):
        assert o['title'] in row[0] and kr['title'] in row[3] and row[8] == f'{score(kr):.1f}' and row[9] == kr['status']
        assert all(i['name'] in row[10] for i in kr['initiatives'])


def test_content_comes_from_the_data_and_the_score_is_computed():
    data = copy.deepcopy(registry.canvas_data(SLUG))
    kr = data['objectives'][0]['key_results'][0]
    kr['title'] = 'Zephyr-7 marker result'
    kr['start'], kr['current'], kr['target'] = 0, 50, 100
    d = doc(data)
    assert page(data).count('Zephyr-7 marker result') == 2
    assert list_rows(d)[0][8] == '0.5'


def test_browser_keyboard_phone_and_list(browser, base):
    pg = open_page(browser, base)
    assert pg.get_by_role('progressbar').count() == sum(len(o['key_results']) for o in registry.canvas_data(SLUG)['objectives']) or pg.locator('[data-slot="progress"]').count() > 0
    pg.locator('[data-canvas-view] [data-slot="toggle-group-item"]', has_text='List').focus()
    pg.keyboard.press('Enter')
    assert pg.get_by_role('table').first.is_visible() and not pg.locator('[data-entelim-form]').is_visible()
    pg.close()
    ph = open_page(browser, base, width=390, height=844)
    m = ph.evaluate("""() => { const r = document.querySelector('[data-entelim-form]');
      const g = r.querySelector('li.grid'); return {page: document.documentElement.scrollWidth - innerWidth, region: r.scrollWidth - r.clientWidth,
      cols: getComputedStyle(g).gridTemplateColumns.split(' ').length}; }""")
    assert m['page'] <= 1 and m['region'] > 200 and m['cols'] == 12
    assert ph.errors == []
    ph.close()
