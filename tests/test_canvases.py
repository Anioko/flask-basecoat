"""Strategy canvases: every canvas in flask_basecoat.canvases renders from its data, keeps the Tier C form, offers the
list route, and passes the page check at 100 percent. The registry decides which canvases exist; a canvas is tested as
soon as its macro, data and example page exist."""
import copy
import importlib.util
import pathlib

import pytest
from lxml import html as lxml_html

from flask import render_template
from flask_basecoat import canvases as registry
from flask_basecoat.testing import make_app

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_page', ROOT / 'compliance' / 'scripts' / 'check_page.py')
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)
LIMITS = {'regions': 6, 'stat_cards': 4, 'charts': 2, 'tables': 1}
BUILT = [c['slug'] for c in registry.available()]


def page(slug, data=None):
    app = make_app()
    entry = next(c for c in registry.available() if c['slug'] == slug)
    with app.test_request_context(f'/examples/canvas/{slug}'):
        return render_template(entry['page'], data=data or registry.canvas_data(slug), entry=entry)


def test_registry_lists_fourteen_canvases_with_the_five_forms_only():
    assert len(registry.CANVASES) == 14
    assert {c['form'] for c in registry.canvases()} <= {'C1', 'C2', 'C3', 'C4', 'C5'}
    assert len({c['slug'] for c in registry.canvases()}) == 14


@pytest.mark.parametrize('slug', BUILT)
def test_canvas_page_renders_with_one_marked_scroll_region(slug):
    doc = lxml_html.fromstring(page(slug))
    marked = doc.xpath('//*[@data-entelim-form]')
    entry = next(c for c in registry.canvases() if c['slug'] == slug)
    assert len(marked) == 1 and marked[0].get('data-entelim-form') == entry['form']
    m = marked[0]
    assert m.get('role') == 'region' and m.get('aria-label') and m.get('tabindex') == '0'
    assert 'overflow-x-auto' in m.get('class').split()
    assert doc.xpath('//*[@data-slot="toggle-group"][contains(@aria-label, "view")]')
    assert doc.xpath('//meta[@name="shadcn-nearest"]')
    assert 'Northwind' in doc.text_content()


@pytest.mark.parametrize('slug', BUILT)
def test_canvas_content_comes_from_the_data(slug):
    data = registry.canvas_data(slug)
    marker = 'Zephyr-7 marker note'
    changed = copy.deepcopy(data)
    boxes = changed.get('boxes')
    if not boxes:
        pytest.skip('this canvas takes structured data, covered by its own test')
    first = next(iter(boxes))
    boxes[first] = list(boxes[first]) + [marker]
    assert marker not in page(slug)
    out = page(slug, changed)
    assert out.count(marker) == 3          # the note card, its hover card, and the list route


@pytest.mark.parametrize('slug', BUILT)
def test_list_route_has_the_same_notes_as_the_drawing(slug):
    doc = lxml_html.fromstring(page(slug))
    drawn = [li.text_content().strip() for li in doc.xpath('//*[@data-canvas-notes]/li//*[@data-note-text]')]
    if not drawn:
        pytest.skip('this canvas has its own list route, covered by its own test')
    rows = doc.xpath('//*[@data-canvas-rows]//tr')
    listed = [r.xpath('./td')[-1].text_content().strip() for r in rows]
    assert sorted(x for x in listed if not x.startswith('Empty.')) == sorted(drawn)
    assert doc.xpath('//*[@data-slot="table"]//th[@scope="col"]')
    assert doc.xpath('//*[@data-canvas-rows]//th[@scope="row"]')


@pytest.mark.parametrize('slug', BUILT)
def test_canvas_page_is_shadcn_composed_at_its_tier(slug, tmp_path):
    f = tmp_path / f'{slug}.html'
    f.write_text(page(slug), encoding='utf8')
    original = lxml_html.fromstring(cp.golden_path('dashboard-01').read_text(encoding='utf8'))
    res, score, counts = cp.check(lxml_html.fromstring(f.read_text(encoding='utf8')), original, 'dashboard-01', LIMITS)
    assert {k: v[:3] for k, v in res.items() if v} == {}
    assert score == 100.0
    assert counts['regions'] <= 6


@pytest.mark.parametrize('slug', BUILT)
def test_example_route_serves_the_page_and_the_index_links_it(slug):
    app = make_app()
    with app.test_client() as c:
        assert c.get(f'/examples/canvas/{slug}').status_code == 200
        assert f'/examples/canvas/{slug}' in c.get('/examples/canvas/').get_data(as_text=True)


# ---- the page check itself: the Tier C conditions catch each departure

def _check(text):
    original = lxml_html.fromstring(cp.golden_path('dashboard-01').read_text(encoding='utf8'))
    return cp.check(lxml_html.fromstring(text), original, 'dashboard-01', LIMITS)


@pytest.mark.parametrize('old,new', [
    ('tabindex="0" aria-label', 'aria-label'),                       # a scroll region a keyboard cannot reach
    ('overflow-x-auto rounded-lg', 'rounded-lg'),                    # a region that would not scroll on a phone
    ('role="region" tabindex', 'tabindex'),                          # no region role
    ('aria-label="Business model canvas view"', 'aria-label="Switch"'),   # no view switch
    ('<div class="min-w-240">', '<div class="min-w-240" style="width:960px">'),   # geometry outside the custom properties
])
def test_form_check_catches_departures(old, new):
    text = page('business-model-canvas')
    assert old in text, old
    res, _, _ = _check(text.replace(old, new, 1))
    assert res['form'], f'form check did not catch {new!r}'


def test_form_check_refuses_two_marked_regions():
    text = page('business-model-canvas')
    res, _, _ = _check(text.replace('<p class="text-xs text-muted-foreground">Scroll', '<div data-entelim-form="C4"></div><p class="text-xs text-muted-foreground">Scroll', 1))
    assert any('marked' in x for x in res['form'])


def test_cards_in_the_marked_region_count_as_one_region():
    res, _, counts = _check(page('business-model-canvas'))
    assert counts['regions'] == 1 and not res['density']
