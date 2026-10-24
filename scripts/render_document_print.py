"""Print the solution document to PDF in A4 and Letter, and render pages 1 to 3 of each to PNG (R17).

    python scripts/render_document_print.py [out_dir]      default: shots/fbprint01

Needs Playwright with Chromium and PyMuPDF. The same code as tests/test_print_golden.py prints the page.
"""
import pathlib
import sys

import pymupdf
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests import print_support as ps  # noqa: E402


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    with ps.served_app() as url, sync_playwright() as p:
        browser = p.chromium.launch()
        for size in ps.SHEETS:
            data = ps.print_pdf(browser, f'{url}{ps.DOCUMENT_PATH}?size={size}')
            (out / f'solution-document-{size}.pdf').write_bytes(data)
            doc = pymupdf.open(stream=data, filetype='pdf')
            for n in range(min(3, len(doc))):
                doc[n].get_pixmap(dpi=110).save(out / f'solution-document-{size}-p{n + 1}.png')
            print(f'{size}: {len(doc)} pages')
        dark = ps.print_pdf(browser, f'{url}{ps.DOCUMENT_PATH}?size=a4', theme='dark')
        (out / 'solution-document-a4-from-dark-screen.pdf').write_bytes(dark)
        browser.close()


if __name__ == '__main__':
    main(pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'shots' / 'fbprint01')
