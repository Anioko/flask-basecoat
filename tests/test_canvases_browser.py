"""Strategy canvases in a real browser (Playwright): render with no console errors, keyboard to every control, the list
route, the phone keeps the shape and scrolls, light and dark, and editing a box."""
from threading import Thread

import pytest
from werkzeug.serving import make_server

from flask_basecoat import canvases as registry
from flask_basecoat.testing import make_app

playwright = pytest.importorskip('playwright.sync_api')
BUILT = [c['slug'] for c in registry.available()]


@pytest.fixture(scope='module')
def base():
    server = make_server('127.0.0.1', 0, make_app())   # a free port, so parallel runs do not clash
    t = Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()


@pytest.fixture(scope='module')
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def open_page(browser, base, slug, width=1440, height=900, theme='light'):
    pg = browser.new_page(viewport={'width': width, 'height': height})
    pg.errors = []
    pg.on('console', lambda m: pg.errors.append(m.text) if m.type == 'error' else None)
    pg.on('pageerror', lambda e: pg.errors.append(str(e)))
    pg.goto(f'{base}/examples/canvas/{slug}?theme={theme}')
    pg.wait_for_selector('[data-entelim-form]')
    pg.wait_for_timeout(250)
    return pg


@pytest.mark.parametrize('slug', BUILT)
def test_renders_without_console_errors(browser, base, slug):
    pg = open_page(browser, base, slug)
    assert pg.locator('[data-entelim-form]').is_visible()
    assert pg.locator('main h1, h1').first.inner_text().strip()
    assert pg.errors == []
    pg.close()


@pytest.mark.parametrize('slug', BUILT)
def test_keyboard_reaches_every_control(browser, base, slug):
    pg = open_page(browser, base, slug)
    expected = pg.evaluate("""() => {
      const root = document.querySelector('[data-canvas]');
      const sel = 'button:not([disabled]), a[href], [tabindex="0"], input, textarea, select';
      return Array.from(root.querySelectorAll(sel)).filter(e => e.offsetParent !== null && e.tabIndex >= 0 && !e.closest('[hidden]')
        && !e.closest('[data-slot="sheet-content"]') && !e.closest('[data-slot="chart"]')).map((e, i) => (e.setAttribute('data-kb', i), i)).length;
    }""")
    assert expected >= 2           # at least the view switch and the scroll region
    pg.locator('[data-canvas-view] [data-slot="toggle-group-item"]').first.focus()
    seen = set()
    for _ in range(expected + 8):
        idx = pg.evaluate("() => document.activeElement && document.activeElement.getAttribute('data-kb')")
        if idx is not None:
            seen.add(idx)
        pg.keyboard.press('Tab')
    assert len(seen) == expected, f'{len(seen)} of {expected} controls reached by Tab'
    pg.close()


@pytest.mark.parametrize('slug', BUILT)
def test_list_view_by_keyboard_and_back(browser, base, slug):
    pg = open_page(browser, base, slug)
    notes = pg.locator('[data-canvas-notes] > li').count()
    pg.locator('[data-canvas-view] [data-slot="toggle-group-item"]', has_text='List').focus()
    pg.keyboard.press('Enter')
    table = pg.get_by_role('table')
    assert table.first.is_visible()
    assert not pg.locator('[data-entelim-form]').is_visible()
    if notes:
        rows = pg.locator('[data-canvas-rows] tr').count()
        assert rows >= notes
    pg.locator('[data-canvas-view] [data-slot="toggle-group-item"]', has_text='Canvas').focus()
    pg.keyboard.press('Enter')
    assert pg.locator('[data-entelim-form]').is_visible()
    pg.close()


@pytest.mark.parametrize('slug', BUILT)
def test_phone_scrolls_the_region_and_keeps_the_shape(browser, base, slug):
    wide = open_page(browser, base, slug)
    cols_wide = wide.evaluate("""() => { const g = document.querySelector('[data-entelim-form] .grid'); return g ? getComputedStyle(g).gridTemplateColumns.split(' ').length : 0; }""")
    wide.close()
    pg = open_page(browser, base, slug, width=390, height=844)
    m = pg.evaluate("""() => { const r = document.querySelector('[data-entelim-form]');
      return {page: document.documentElement.scrollWidth - window.innerWidth, region: r.scrollWidth - r.clientWidth,
              cols: (() => { const g = r.querySelector('.grid'); return g ? getComputedStyle(g).gridTemplateColumns.split(' ').length : 0; })()}; }""")
    assert m['page'] <= 1, 'the page itself must not overflow at 390'
    assert m['region'] > 40, 'the marked region must scroll sideways, not reflow'
    assert m['cols'] == cols_wide, 'column count at 390 must equal column count at 1440'
    pg.locator('[data-entelim-form]').focus()
    pg.keyboard.press('ArrowRight')
    pg.wait_for_timeout(400)
    assert pg.evaluate("() => document.querySelector('[data-entelim-form]').scrollLeft") > 0
    pg.close()


@pytest.mark.parametrize('slug', BUILT)
def test_light_and_dark(browser, base, slug):
    seen = {}
    for theme in ('light', 'dark'):
        pg = open_page(browser, base, slug, theme=theme)
        seen[theme] = pg.evaluate("() => [document.documentElement.classList.contains('dark'), getComputedStyle(document.body).backgroundColor, getComputedStyle(document.querySelector('[data-entelim-form]')).borderTopColor]")
        assert pg.errors == []
        pg.close()
    assert seen['light'][0] is False and seen['dark'][0] is True
    assert seen['light'][1] != seen['dark'][1]


@pytest.mark.parametrize('slug', BUILT)
def test_editing_a_box_updates_the_drawing_and_the_list(browser, base, slug):
    pg = open_page(browser, base, slug)
    edit = pg.locator('[data-canvas-edit]').first
    if edit.count() == 0:
        pytest.skip('this canvas has no note boxes')
    edit.focus()
    pg.keyboard.press('Enter')
    sheet = pg.get_by_role('dialog')
    sheet.wait_for(state='visible')
    box = edit.get_attribute('data-canvas-edit')
    area = sheet.locator('textarea')
    area.fill(area.input_value() + '\nA note added from the sheet')
    sheet.get_by_role('button', name='Save notes').click()
    pg.wait_for_selector('[role="dialog"]', state='hidden')
    assert pg.locator(f'[data-canvas-notes="{box}"] > li', has_text='A note added from the sheet').count() == 1
    assert 'A note added from the sheet' in pg.locator('[data-canvas-rows]').inner_text()
    assert 'Saved' in pg.locator('[data-canvas-live]').inner_text()
    pg.close()
