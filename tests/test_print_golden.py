"""Print golden for long-form documents (R17), made with Chromium's PDF output in A4 and in US Letter.

The solution document (/examples/document/solution-document) is printed with Playwright's page.pdf and the PDF is read
back. The golden file (tests/golden/print/solution-document.json) holds the page count and the page of every section;
regenerate it with ``PRINT_GOLDEN_UPDATE=1 python -m pytest tests/test_print_golden.py`` after a deliberate change.

Asserts: the page count; that each h2 is the first thing in the text area of a new page; the running header and the
"Page n of m" footer on every page after the cover and neither on the cover; that nothing drawn is wider than the text
column (in the PDF, and in the DOM under print media); the light tokens on a dark screen; that navigation and buttons
do not print and links print their text only; and that chart series differ without colour.
"""
import json
import os
import pathlib

import pytest

pymupdf = pytest.importorskip('pymupdf')
sync_api = pytest.importorskip('playwright.sync_api')

from . import print_support as ps  # noqa: E402

GOLDEN = pathlib.Path(__file__).parent / 'golden' / 'print' / 'solution-document.json'
TITLE = 'Claims Platform Modernisation: Solution Document'
SECTIONS = ['Executive summary', 'Context and objectives', 'Options considered', 'Cost and evaluation',
            'Delivery plan', 'Recommendation', 'Risks', 'Next steps']
UPDATE = bool(os.environ.get('PRINT_GOLDEN_UPDATE'))


@pytest.fixture(scope='module')
def site():
    with ps.served_app() as url:
        yield url


@pytest.fixture(scope='module')
def browser():
    try:
        with sync_api.sync_playwright() as p:
            b = p.chromium.launch()
            yield b
            b.close()
    except Exception as e:  # no Chromium installed
        pytest.skip(f'Chromium is not available: {e}')


@pytest.fixture(scope='module')
def pdfs(browser, site):
    out = {}
    for size in ps.SHEETS:
        data = ps.print_pdf(browser, f'{site}{ps.DOCUMENT_PATH}?size={size}')
        out[size] = pymupdf.open(stream=data, filetype='pdf')
    return out


@pytest.fixture(scope='module')
def golden(pdfs):
    if UPDATE:
        data = {}
        for size, doc in pdfs.items():
            pages = {}
            for n, page in enumerate(doc, 1):
                first = ps.body_blocks(page)[:1]
                for name in SECTIONS:
                    if first and first[0][1].split('\n')[0] == name:
                        pages[name] = n
            data[size] = {'pages': len(doc), 'sections': pages}
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(data, indent=2) + '\n')
    return json.loads(GOLDEN.read_text())


@pytest.mark.parametrize('size', ['a4', 'letter'])
class TestSheet:
    def test_sheet_size(self, pdfs, size):
        width, height = ps.SHEETS[size]
        for page in pdfs[size]:
            assert page.rect.width == pytest.approx(width, abs=1)
            assert page.rect.height == pytest.approx(height, abs=1)

    def test_page_count(self, pdfs, golden, size):
        assert len(pdfs[size]) == golden[size]['pages']
        assert 8 <= len(pdfs[size]) <= 10, 'a solution document runs eight to ten pages'

    def test_each_h2_starts_a_page(self, pdfs, golden, size):
        doc = pdfs[size]
        for name in SECTIONS:
            pages = [n for n, page in enumerate(doc, 1)
                     if any(text.split('\n')[0] == name for _, text in ps.body_blocks(page))]
            assert len(pages) == 1, f'{name!r} is on pages {pages}'
            first = ps.body_blocks(doc[pages[0] - 1])[0][1]
            assert first.split('\n')[0] == name, f'{name!r} is not the first text on page {pages[0]}: {first[:60]!r}'
            assert pages[0] == golden[size]['sections'][name], f'{name!r} moved to page {pages[0]}'
        starts = [golden[size]['sections'][name] for name in SECTIONS]
        assert starts == sorted(set(starts)), 'sections must start on distinct, increasing pages'

    def test_cover_is_page_one_without_header_or_footer(self, pdfs, size):
        page = pdfs[size][0]
        text = ' '.join(page.get_text().split())
        for part in (TITLE, '24 October 2026', 'Version 1.2', 'Amara Okafor'):
            assert part in text
        assert 'harbourline insurance group' in text.lower()
        assert ps.margin_text(page) == ('', '')
        assert not any(name in text for name in SECTIONS[1:]), 'the cover carries no section'

    def test_running_header_and_footer(self, pdfs, size):
        doc = pdfs[size]
        total = len(doc)
        head, foot = ps.margin_text(doc[1])
        assert head == TITLE
        assert foot == f'Page 2 of {total}'
        for n in range(2, total + 1):
            head, foot = ps.margin_text(doc[n - 1])
            assert (head, foot) == (TITLE, f'Page {n} of {total}')

    def test_nothing_is_wider_than_the_text_column(self, pdfs, size):
        for n, page in enumerate(pdfs[size], 1):
            assert ps.overflow(page) == [], f'page {n}'

    def test_navigation_and_buttons_do_not_print_and_links_print_their_text_only(self, pdfs, size):
        text = '\n'.join(page.get_text() for page in pdfs[size])
        assert 'Examples' not in text            # the breadcrumb
        assert 'http' not in text and '/examples' not in text
        assert all(not page.get_links() or all(link.get('uri') is None for link in page.get_links()) for page in pdfs[size])

    def test_values_are_text_and_figures_stay_whole(self, pdfs, golden, size):
        doc = pdfs[size]
        cost_page = doc[golden[size]['sections']['Cost and evaluation'] - 1].get_text()
        delivery_page = doc[golden[size]['sections']['Delivery plan'] - 1].get_text()
        for value in ('1.2', '9.6', '3.4', '7.8', '5.1', '5.9', '11.8', '4.6'):
            assert value in cost_page.split(), value
        for value in ('5', '20', '40', '60', '80', '95', '100', '15', '30', '45', '75', '90'):
            assert value in delivery_page.split(), value
        # a figure or table caption sits on the page of its figure, so no figure is split across pages
        for caption, section in (('Figure 1', 'Cost and evaluation'), ('Figure 2', 'Delivery plan'),
                                 ('Table 1', 'Options considered'), ('Table 2', 'Risks'), ('Table 3', 'Next steps')):
            n = golden[size]['sections'][section]
            assert caption in doc[n - 1].get_text(), caption


def test_dark_screen_prints_with_the_light_tokens(browser, site):
    data = ps.print_pdf(browser, f'{site}{ps.DOCUMENT_PATH}?size=a4', theme='dark')
    doc = pymupdf.open(stream=data, filetype='pdf')
    for n in (1, 2, 4):
        pix = doc[n].get_pixmap(dpi=30, colorspace=pymupdf.csGRAY)
        mean = sum(pix.samples) / len(pix.samples)
        assert mean > 235, f'page {n + 1} is dark (mean grey {mean:.0f})'
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    try:
        page.goto(f'{site}{ps.DOCUMENT_PATH}?theme=dark')
        assert page.evaluate("document.documentElement.classList.contains('dark')")
        screen = page.evaluate("getComputedStyle(document.body).backgroundColor")
        page.emulate_media(media='print')
        printed = page.evaluate("getComputedStyle(document.body).backgroundColor")
        assert screen != printed
        assert page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--background').trim()") in ('oklch(1 0 0)', 'oklch(100% 0 0)')
    finally:
        page.close()


@pytest.mark.parametrize('size', ['a4', 'letter'])
def test_dom_stays_inside_the_column_and_chrome_is_hidden_under_print_media(browser, site, size):
    width, _ = ps.SHEETS[size]
    column = (width - 2 * ps.MARGIN_X) / 0.75   # CSS pixels
    page = browser.new_page(viewport={'width': round(column), 'height': 1000})
    try:
        page.goto(f'{site}{ps.DOCUMENT_PATH}?size={size}')
        ps.charts_ready(page)
        page.emulate_media(media='print')
        page.wait_for_timeout(300)
        wide = page.evaluate("""(col) => [...document.querySelectorAll('[data-document] *')].filter(e => {
            const s = getComputedStyle(e); if (s.display === 'none' || s.visibility === 'hidden' || e.closest('.recharts-tooltip-wrapper')) return false;
            const r = e.getBoundingClientRect(); if (!r.width && !r.height) return false;
            const o = document.querySelector('[data-document]').getBoundingClientRect();
            return r.right > o.left + col + 1 || r.left < o.left - 1;
        }).map(e => e.tagName + '.' + String(e.getAttribute('class')).slice(0, 60))""", column)
        assert wide == []
        visible = page.evaluate("""() => [...document.querySelectorAll('nav, button, [data-slot=button], [data-slot=breadcrumb], [data-slot=sidebar], [data-slot=toast]')]
            .filter(e => getComputedStyle(e).display !== 'none').map(e => e.tagName)""")
        assert visible == []
        for a in page.query_selector_all('a[href]'):
            assert a.evaluate("e => getComputedStyle(e, '::after').content") in ('none', 'normal')
    finally:
        page.close()


def test_chart_series_differ_without_colour_in_print(browser, site):
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    try:
        page.goto(f'{site}{ps.DOCUMENT_PATH}')
        ps.charts_ready(page)
        page.emulate_media(media='print')
        line = page.evaluate("""() => [...document.querySelectorAll('[data-chart=chart-document-delivery] .recharts-line-curve')]
            .map(e => getComputedStyle(e).strokeDasharray)""")
        assert len(line) == 2 and len(set(line)) == 2 and line[1] == '7px, 4px'
        markers = page.evaluate("""() => [...document.querySelectorAll('[data-chart=chart-document-delivery] .recharts-line-dots')]
            .map(g => getComputedStyle(g.querySelector('.recharts-line-dot')).fill)""")
        assert len(set(markers)) == 2, 'one series has filled markers, the other hollow ones'
        bars = page.evaluate("""() => [...document.querySelectorAll('[data-chart=chart-document-costs] .recharts-bar')]
            .map(g => getComputedStyle(g.querySelector('.recharts-rectangle')).stroke)""")
        assert len(set(bars)) == 2
        page.emulate_media(media='screen')
        on_screen = page.evaluate("""() => [...document.querySelectorAll('[data-chart] .recharts-line-curve')]
            .map(e => getComputedStyle(e).strokeDasharray)""")
        assert '7px, 4px' not in on_screen, 'the print rules do not change the screen'
    finally:
        page.close()


def test_blog_detail_prints_as_a_document(browser, site):
    """R17 names the blog detail screen: the same stylesheet prints it, with its comment form and buttons left out."""
    doc = pymupdf.open(stream=ps.print_pdf(browser, f'{site}/examples/blog-detail-page'), filetype='pdf')
    text = '\n'.join(p.get_text() for p in doc)
    assert 'The Best Way to Write a Recurring Email Newsletter' in text
    assert 'Post Comment' not in text and 'Reply' not in text and 'SHARE THIS' in text.upper()
    assert len(doc) >= 2
    head, foot = ps.margin_text(doc[1])
    assert head == 'The Best Way to Write a Recurring Email Newsletter' and foot == f'Page 2 of {len(doc)}'
    assert all(ps.overflow(p) == [] for p in doc)
