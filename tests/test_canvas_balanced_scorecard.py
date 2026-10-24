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

SLUG = "balanced-scorecard"
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


KEYS = ['financial', 'internal', 'customer', 'learning']
TITLES = {'financial': 'Financial', 'internal': 'Internal Business Processes', 'customer': 'Customer', 'learning': 'Learning and Growth'}


def test_four_perspectives_around_the_vision_in_the_published_places():
    d = doc()
    cards = d.xpath('//*[@data-entelim-form]//*[@data-slot="card"]')
    titles = [c.xpath('.//*[@data-slot="card-title"]')[0].text_content().strip() for c in cards]
    assert titles == ['Financial', 'Internal Business Processes', 'Vision and Strategy', 'Customer', 'Learning and Growth']
    for c in cards:
        cls = c.get('class').split()
        assert not any(x.startswith(('md:', 'lg:', 'xl:', 'sm:')) for x in cls)    # no responsive reflow inside the drawing
    for t in ('Objectives', 'Measures', 'Targets', 'Initiatives'):
        assert len(d.xpath(f'//*[@data-entelim-form]//th[normalize-space()="{t}"]')) == 4
    assert len(d.xpath('//*[@data-entelim-form]//*[@data-slot="card"]//svg')) >= 4      # the arrows


def test_every_objective_of_the_data_is_drawn_and_listed():
    data = json.loads(json.dumps(registry.canvas_data(SLUG)))
    objectives = [(k, r) for k in KEYS for r in data['perspectives'][k]]
    d = doc(data)
    drawn = d.xpath('//*[@data-entelim-form]//tbody/tr')
    assert len(drawn) == len(objectives) == 12
    rows = list_rows(d)
    assert len(rows) == len(objectives) + 2                     # plus the vision and the strategy
    for (k, r), row in zip(objectives, rows[2:]):
        assert row == [TITLES[k], r['objective'], r['measure'], r['target'], r['initiative']]
    assert rows[0][1].startswith('Vision:') and rows[1][1].startswith('Strategy:')


def test_content_comes_from_the_data():
    data = copy.deepcopy(registry.canvas_data(SLUG))
    data['perspectives']['customer'][0]['objective'] = 'Zephyr-7 marker objective'
    data['vision'] = 'Zephyr-7 marker vision'
    out = page(data)
    assert out.count('Zephyr-7 marker objective') == 2 and out.count('Zephyr-7 marker vision') == 2


def test_browser_keyboard_phone_and_list(browser, base):
    pg = open_page(browser, base)
    pg.locator('[data-entelim-form]').focus()
    assert pg.evaluate("() => document.activeElement.hasAttribute('data-entelim-form')")
    pg.locator('[data-canvas-view] [data-slot="toggle-group-item"]', has_text='List').focus()
    pg.keyboard.press('Enter')
    assert pg.get_by_role('table').first.is_visible()
    assert pg.locator('[data-canvas-rows] tr').count() == 14
    pg.close()
    ph = open_page(browser, base, width=390, height=844)
    m = ph.evaluate("""() => { const r = document.querySelector('[data-entelim-form]');
      const g = r.querySelector('.grid'); return {page: document.documentElement.scrollWidth - innerWidth, region: r.scrollWidth - r.clientWidth,
      cols: getComputedStyle(g).gridTemplateColumns.split(' ').length}; }""")
    assert m['page'] <= 1 and m['region'] > 200 and m['cols'] == 24
    assert ph.errors == []
    ph.close()
