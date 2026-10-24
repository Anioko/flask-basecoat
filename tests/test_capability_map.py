"""Capability-map family: grouping by capability_type, the five example pages, the dialogs, and the browser behaviour."""
import copy
import importlib.util
import pathlib
from threading import Thread

import pytest
from lxml import html as lxml_html
from werkzeug.serving import make_server

from flask import render_template
from flask_basecoat import canvases as registry, capability
from flask_basecoat.testing import make_app

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_page', ROOT / 'compliance' / 'scripts' / 'check_page.py')
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)
LIMITS = {'regions': 6, 'stat_cards': 4, 'charts': 2, 'tables': 1}
SLUGS = [s for s, _, _ in registry.CAPABILITY]
MAPS = ['capability-map', 'capability-tree', 'applications-by-capability']
ORDER = ['Strategic', 'Operational', 'Supporting', 'Type not set']


def render(slug, data=None):
    with make_app().test_request_context('/'):
        return render_template(f'examples/capability/{slug}.html', data=data or registry.capability_data())


def headings(slug, data=None):
    doc = lxml_html.fromstring(render(slug, data))
    return [h.text_content().strip().replace(' capabilities', '').split(' ·')[0] for h in doc.xpath('//*[@data-capmap]//h3[contains(@id, "-grp-")] | //*[@data-capmap]//th[contains(@id, "-grp-")]')]


# ---- grouping by capability_type

def test_groups_follow_the_type_field_in_order_and_never_drop():
    caps = [{'id': 'a', 'capability_type': 'supporting'}, {'id': 'b', 'capability_type': 'strategic'}, {'id': 'c'},
            {'id': 'd', 'capability_type': ''}, {'id': 'e', 'capability_type': 'operational'}, {'id': 'f', 'capability_type': 'Strategic'},
            {'id': 'g', 'capability_type': 'bogus'}, {'id': 'h', 'type': 'strategic', 'domain': 'strategic'}]
    groups = capability.capability_groups(caps)
    assert [g['label'] for g in groups] == ORDER
    assert [[i['id'] for i in g['items']] for g in groups] == [['b', 'f'], ['e'], ['a'], ['c', 'd', 'g', 'h']]
    assert sum(len(g['items']) for g in groups) == len(caps)


def test_only_the_capability_type_field_is_a_type():
    assert capability.type_of({'type': 'strategic'}) == '' and capability.type_of({'domain': 'strategic'}) == ''
    assert capability.type_of({'capability_type': ' Operational '}) == 'operational'


def test_empty_typed_groups_stay_and_the_unset_group_only_when_needed():
    groups = capability.capability_groups([{'id': 'a', 'capability_type': 'strategic'}])
    assert [g['key'] for g in groups] == ['strategic', 'operational', 'supporting']


def test_orphans_are_roots_not_dropped():
    caps = [{'id': 'a'}, {'id': 'b', 'parentId': 'a'}, {'id': 'c', 'parentId': 'gone'}]
    assert [c['id'] for c in capability.capability_roots(caps)] == ['a', 'c']


@pytest.mark.parametrize('slug', MAPS)
def test_each_view_shows_the_headings_in_order_with_all_three_types(slug):
    assert headings(slug) == ORDER


@pytest.mark.parametrize('slug', MAPS)
def test_a_capability_without_a_type_lands_in_the_last_group_and_is_not_dropped(slug):
    data = copy.deepcopy(registry.capability_data())
    for c in data['capabilities']:
        if c['id'] == 'customer':
            c['capability_type'] = None
    out = render(slug, data)
    assert 'Order Management' in out and headings(slug, data)[-1] == 'Type not set'
    doc = lxml_html.fromstring(out)
    last = doc.xpath('(//*[@data-capmap]//h3[contains(@id, "-grp-unset")] | //*[@data-capmap]//th[contains(@id, "-grp-unset")])')
    assert 'Customer Management' in (last[0].getparent().getparent().text_content() if slug == 'applications-by-capability' else last[0].getparent().getparent().text_content())


def test_the_old_type_key_is_not_read():
    data = copy.deepcopy(registry.capability_data())
    for c in data['capabilities']:
        c['type'] = c.pop('capability_type')
    assert headings('capability-map', data) == ['Strategic', 'Operational', 'Supporting', 'Type not set']
    doc = lxml_html.fromstring(render('capability-map', data))
    assert not doc.xpath('//*[@data-cap-tile][ancestor::section[contains(@aria-labelledby, "-grp-strategic")]]')


# ---- pages

@pytest.mark.parametrize('slug', SLUGS)
def test_capability_page_is_shadcn_composed_at_its_tier(slug):
    form = dict((s, f) for s, _, f in registry.CAPABILITY)[slug]
    doc = lxml_html.fromstring(render(slug))
    marked = doc.xpath('//*[@data-entelim-form]')
    assert len(marked) == (1 if form.startswith('C') else 0)
    original = lxml_html.fromstring(cp.golden_path('dashboard-01').read_text(encoding='utf8'))
    res, score, _ = cp.check(doc, original, 'dashboard-01', LIMITS)
    assert {k: v[:3] for k, v in res.items() if v} == {}
    assert score == 100.0


@pytest.mark.parametrize('slug', MAPS[:2])
def test_list_route_has_one_row_per_capability(slug):
    doc = lxml_html.fromstring(render(slug))
    n = len(registry.capability_data()['capabilities'])
    assert len(doc.xpath('//*[@data-capmap-pane="list"]//tbody/tr')) == n
    assert len(doc.xpath('//*[@data-capmap-pane="list"]//th[@scope="col"]')) == 8


def test_applications_table_has_a_row_per_capability_and_names_gaps():
    doc = lxml_html.fromstring(render('applications-by-capability'))
    data = registry.capability_data()
    assert len(doc.xpath('//tbody/tr[@data-covered]')) == len(data['capabilities'])
    assert 'No application supports this capability' in doc.text_content()


def test_dialog_macros_offer_the_three_types_and_not_set():
    out = render('capability-dialogs')
    for label in ('Strategic', 'Operational', 'Supporting', 'Not set'):
        assert label in out
    doc = lxml_html.fromstring(out)
    assert len(doc.xpath('//*[@data-slot="dialog-content"]')) == 3 and len(doc.xpath('//*[@data-slot="alert-dialog-content"]')) == 1


# ---- browser

playwright = pytest.importorskip('playwright.sync_api')


@pytest.fixture(scope='module')
def base():
    server = make_server('127.0.0.1', 0, make_app())
    Thread(target=server.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()


@pytest.fixture(scope='module')
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def page(browser, base, slug, width=1440, height=900, theme='light'):
    pg = browser.new_page(viewport={'width': width, 'height': height})
    pg.errors = []
    pg.on('console', lambda m: pg.errors.append(m.text) if m.type == 'error' else None)
    pg.on('pageerror', lambda e: pg.errors.append(str(e)))
    pg.goto(f'{base}/examples/capability/{slug}?theme={theme}')
    pg.wait_for_timeout(300)
    return pg


@pytest.mark.parametrize('slug', SLUGS)
def test_browser_renders_clean_in_light_and_dark(browser, base, slug):
    for theme in ('light', 'dark'):
        pg = page(browser, base, slug, theme=theme)
        assert pg.errors == [] and pg.evaluate("document.documentElement.classList.contains('dark')") == (theme == 'dark')
        pg.close()


@pytest.mark.parametrize('slug', MAPS)
def test_browser_phone_keeps_the_shape_and_the_page_does_not_overflow(browser, base, slug):
    pg = page(browser, base, slug, width=390, height=844)
    m = pg.evaluate("() => { const r = document.querySelector('[data-entelim-form]'); return {page: document.documentElement.scrollWidth - innerWidth, region: r.scrollWidth - r.clientWidth}; }")
    assert m['page'] <= 1 and m['region'] > 40
    pg.close()


def test_browser_metric_switch_changes_the_ramp_and_the_words(browser, base):
    pg = page(browser, base, 'capability-map')
    first = pg.locator('[data-cap-tile] [data-ramp]').first
    before = first.evaluate('e => [...e.classList].sort().join(" ")')
    pg.locator('[data-capmap-metric] [data-slot="toggle-group-item"]', has_text='Investment').click()
    assert pg.locator('[data-legend="investment"]').is_visible() and not pg.locator('[data-legend="maturity"]').is_visible()
    assert 'investment' in pg.locator('[data-cap-tile]').first.inner_text().lower()
    pg.locator('[data-capmap-metric] [data-slot="toggle-group-item"]', has_text='Maturity').click()
    assert first.evaluate('e => [...e.classList].sort().join(" ")') == before
    pg.close()


def test_browser_keyboard_opens_detail_and_toggles_a_tile(browser, base):
    pg = page(browser, base, 'capability-map')
    pg.locator('[data-cap-open="strategy"]').focus()
    pg.keyboard.press('Enter')
    dialog = pg.get_by_role('dialog')
    dialog.wait_for(state='visible')
    assert 'Strategy & Planning' in dialog.inner_text() and 'Strategic' in dialog.inner_text()
    pg.keyboard.press('Escape')
    btn = pg.get_by_role('button', name='Show sub-capabilities of Portfolio & Investment Planning')
    btn.focus(); pg.keyboard.press('Enter')
    assert btn.get_attribute('aria-expanded') == 'true'
    pg.close()


def test_browser_list_view_and_coverage_filter(browser, base):
    pg = page(browser, base, 'capability-tree')
    pg.locator('[data-capmap-view] [data-slot="toggle-group-item"]', has_text='Table').focus(); pg.keyboard.press('Enter')
    assert pg.get_by_role('table').first.is_visible() and not pg.locator('[data-entelim-form]').is_visible()
    pg.close()
    pg = page(browser, base, 'applications-by-capability')
    total = pg.locator('tr[data-covered]:visible').count()
    pg.locator('[data-capmap-filter] [data-slot="toggle-group-item"]', has_text='Without an application').focus(); pg.keyboard.press('Enter')
    gaps = pg.locator('tr[data-covered]:visible').count()
    assert 0 < gaps < total
    pg.close()


def test_browser_dialogs_open_validate_and_announce(browser, base):
    pg = page(browser, base, 'capability-dialogs')
    pg.get_by_role('button', name='Add capability').first.click()
    d = pg.get_by_role('dialog')
    d.wait_for(state='visible')
    d.get_by_role('button', name='Create capability').click()
    assert d.get_by_text('Capability name is required.').is_visible()
    d.get_by_label('Capability name').fill('Dock scheduling')
    d.get_by_role('button', name='Create capability').click()
    pg.wait_for_selector('[role="dialog"]', state='hidden')
    assert 'Dock scheduling' in pg.locator('[data-capmap-live]').inner_text() and 'Strategic' in pg.locator('[data-capmap-live]').inner_text()
    pg.get_by_role('button', name='Delete Order Management').click()
    ad = pg.get_by_role('alertdialog'); ad.wait_for(state='visible')
    assert 'sub-capabilities' in ad.inner_text()
    pg.close()
