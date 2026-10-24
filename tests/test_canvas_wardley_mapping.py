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

SLUG = "wardley-mapping"
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



STAGES = ['Genesis', 'Custom-built', 'Product', 'Commodity']


def stage(e):
    return STAGES[0 if e < 0.25 else 1 if e < 0.5 else 2 if e < 0.75 else 3]


def level(v):
    return 'high' if v < 0.34 else 'medium' if v < 0.67 else 'low'


def counts(data):
    comps = data['components']
    return len(comps), sum(len(c['depends_on']) for c in comps), sum(1 for c in comps if c.get('movement'))


def test_drawing_names_its_counts_and_the_list_route_repeats_them():
    data = registry.canvas_data(SLUG)
    n, deps, moves = counts(data)
    d = doc(data)
    svg = d.xpath('//*[@data-entelim-form]//svg[@role="img"]')[0]
    assert svg.get('aria-label') == f'Wardley map: {n} components, {deps} dependencies, {moves} movements'
    assert len(svg.xpath('.//line[@data-wm="dependency"]')) == deps
    assert len(svg.xpath('.//line[@data-wm="movement"]')) == moves
    rows = list_rows(d)
    assert len(rows) == n
    heads = [h.text_content().strip() for h in d.xpath('//*[@data-slot="table"]//th[@scope="col"]')]
    assert heads[:5] == ['Component', 'Evolution stage', 'Visibility', 'Depends on', 'Movement']
    assert sum(0 if r[3] == 'None' else len(r[3].split(', ')) for r in rows) == deps
    assert sum(1 for r in rows if r[4] != 'None') == moves


def test_each_component_is_a_named_button_positioned_by_evolution_and_visibility():
    data = registry.canvas_data(SLUG)
    d = doc(data)
    buttons = d.xpath('//*[@data-entelim-form]//button[@data-wm-component]')
    assert len(buttons) == len(data['components'])
    for b, c in zip(buttons, data['components']):
        assert b.get('data-wm-component') == c['id']
        want = f"{c['name']}, user, visibility {level(c['visibility'])}" if c['kind'] == 'user' else f"{c['name']}, evolution {stage(c['evolution'])}, visibility {level(c['visibility'])}"
        assert b.get('aria-label') == want
        x = float(re.search(r'--x:([\d.]+)%', b.get('style')).group(1))
        assert abs(x - c['evolution'] * 100) < 0.06
    ys = [float(re.search(r'--y:([\d.]+)%', b.get('style')).group(1)) for b in buttons]
    assert ys == sorted(ys)                                  # top of the value chain first: Tab order is reading order
    assert len(d.xpath('//*[@data-entelim-form]//svg[@role="img"]')) == 1


def test_axes_and_stages_are_labelled_and_the_user_need_is_at_the_top():
    text = doc().xpath('//*[@data-entelim-form]')[0].text_content()
    for s in ('Genesis', 'Custom-Built', 'Product (+rental)', 'Commodity (+utility)', 'User need', 'Infrastructure', 'Evolution'):
        assert s in text


def test_components_carry_no_geometry_outside_the_custom_properties():
    d = doc()
    for el in d.xpath('//*[@data-entelim-form]//*[@style]'):
        props = {p.split(':')[0].strip() for p in el.get('style').split(';') if ':' in p}
        assert props <= {'--x', '--y', '--w'}


def test_a_changed_component_moves_and_lists_everywhere():
    data = copy.deepcopy(registry.canvas_data(SLUG))
    data['components'][5]['name'] = 'Zephyr-7 marker component'
    data['components'][5]['evolution'] = 0.9
    d = doc(data)
    assert list_rows(d)[5][0] == 'Zephyr-7 marker component' and list_rows(d)[5][1] == 'Commodity'
    b = d.xpath('//button[@data-wm-component]')[5]
    assert 'evolution Commodity' in b.get('aria-label') and '--x:90.0%' in b.get('style')


def test_browser_enter_opens_the_sheet_of_a_component(browser, base):
    pg = open_page(browser, base)
    first = pg.locator('[data-wm-component]').nth(2)
    first.focus()
    pg.keyboard.press('Enter')
    dialog = pg.get_by_role('dialog')
    dialog.wait_for(state='visible')
    comp = registry.canvas_data(SLUG)['components'][2]
    assert comp['name'] in dialog.inner_text() and stage(comp['evolution']) in dialog.inner_text()
    pg.keyboard.press('Escape')
    pg.wait_for_selector('[role="dialog"]', state='hidden')
    assert pg.evaluate("() => document.activeElement.getAttribute('data-wm-component')") == comp['id']
    assert pg.errors == []
    pg.close()


def test_browser_tab_reaches_every_component_in_order(browser, base):
    pg = open_page(browser, base)
    ids = [c['id'] for c in registry.canvas_data(SLUG)['components']]
    pg.locator('[data-entelim-form]').focus()
    seen = []
    for _ in range(len(ids)):
        pg.keyboard.press('Tab')
        seen.append(pg.evaluate("() => document.activeElement.getAttribute('data-wm-component')"))
    assert seen == ids
    pg.close()


def test_browser_phone_keeps_the_axes_and_scrolls(browser, base):
    ph = open_page(browser, base, width=390, height=844)
    m = ph.evaluate("""() => { const r = document.querySelector('[data-entelim-form]');
      return {page: document.documentElement.scrollWidth - innerWidth, region: r.scrollWidth - r.clientWidth,
              stages: r.querySelector('.grid') ? getComputedStyle(r.querySelector('.grid')).gridTemplateColumns.split(' ').length : 0}; }""")
    assert m['page'] <= 1 and m['region'] > 200 and m['stages'] == 4
    assert ph.errors == []
    ph.close()
