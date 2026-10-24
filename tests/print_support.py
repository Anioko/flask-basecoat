"""Support for the print golden (R17): serve the bare Flask-Basecoat app, print a page to PDF with Chromium, read it.

Used by tests/test_print_golden.py and scripts/render_document_print.py. Needs Playwright with Chromium and PyMuPDF
(``pip install playwright pymupdf``; ``playwright install chromium``).
"""
import threading
from contextlib import contextmanager

from werkzeug.serving import make_server

from flask_basecoat.testing import make_app

MM = 72 / 25.4  # points in a millimetre
MARGIN_X = 20 * MM          # the left and right page margins of the document sheet (print.css)
MARGIN_TOP = 24 * MM
MARGIN_BOTTOM = 22 * MM
SHEETS = {'a4': (210 * MM, 297 * MM), 'letter': (612.0, 792.0)}
DOCUMENT_PATH = '/examples/document/solution-document'


@contextmanager
def served_app():
    """The bare app on a free port (R7: no fixed port, so parallel runs never collide). Yields the base URL."""
    server = make_server('127.0.0.1', 0, make_app())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        thread.join(timeout=5)


def charts_ready(page):
    """Wait until every chart on the page is drawn (the runtime fills the SVG after load)."""
    if not page.query_selector('[data-slot=chart]'):
        return
    page.wait_for_function(
        "() => [...document.querySelectorAll('[data-slot=chart]')].every(e => e.querySelector('svg.recharts-surface'))")
    page.wait_for_timeout(1200)  # the series draw-in animation


def print_pdf(browser, url, theme=None):
    """The page as Chromium prints it: the sheet from the page's own @page rules, backgrounds on."""
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    try:
        page.goto(url + (('&' if '?' in url else '?') + f'theme={theme}' if theme else ''))
        charts_ready(page)
        return page.pdf(prefer_css_page_size=True, print_background=True)
    finally:
        page.close()


def body_blocks(pdf_page):
    """Text blocks inside the text area of a page (between the margins), top to bottom: (y0, text)."""
    height = pdf_page.rect.height
    blocks = []
    for x0, y0, x1, y1, text, *_ in pdf_page.get_text('blocks'):
        if y0 >= MARGIN_TOP - 2 and y1 <= height - MARGIN_BOTTOM + 2:
            blocks.append((y0, text.strip()))
    return sorted(blocks)


def margin_text(pdf_page):
    """(header, footer): the text in the top and bottom margins of a page."""
    height = pdf_page.rect.height
    head, foot = [], []
    for x0, y0, x1, y1, text, *_ in pdf_page.get_text('blocks'):
        if y1 < MARGIN_TOP:
            head.append(text.strip())
        elif y0 > height - MARGIN_BOTTOM:
            foot.append(text.strip())
    return ' '.join(head), ' '.join(foot)


def overflow(pdf_page, tolerance=1.5):
    """Everything drawn on the page (text, rules, fills, images) that leaves the text column: [(kind, rect)]."""
    left, right = MARGIN_X - tolerance, pdf_page.rect.width - MARGIN_X + tolerance
    out = []
    for block in pdf_page.get_text('dict')['blocks']:
        x0, _, x1, _ = block['bbox']
        if x0 < left or x1 > right:
            out.append(('image' if block['type'] == 1 else 'text', tuple(round(v, 1) for v in block['bbox'])))
    for drawing in pdf_page.get_drawings():
        r = drawing['rect']
        if r.x0 < left or r.x1 > right:
            out.append(('drawing', tuple(round(v, 1) for v in r)))
    return out
