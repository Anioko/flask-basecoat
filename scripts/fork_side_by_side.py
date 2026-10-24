"""Screenshot each canvas and capability page beside its fork version (Anioko/shadcn-examples, rendered from the fork's own
React components with react-dom/server and the fork's own Tailwind stylesheet; see REPORT-fbcanvas01b.md), at 1440 and 390
wide, light and dark. Left: fork. Right: this library with the Entelim brand tokens (?brand=entelim).

    python scripts/fork_side_by_side.py http://127.0.0.1:5731 /tmp/forkrender shots/fbcanvas01b
"""
import sys
from io import BytesIO

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

base, forkdir, out = sys.argv[1:4]
sys.path.insert(0, '.')
from flask_basecoat import canvases as r

PAGES = [(f'canvas/{c[0]}', f'page-{c[0]}.html', c[0]) for c in r.CANVASES] + [('capability/capability-map', 'page-cap.html', 'capability-map')]
MAXH = 5200


def shot(pg, url, dark, w):
    pg.set_viewport_size({'width': w, 'height': 900})
    pg.goto(url)
    if url.startswith('file:'):
        pg.evaluate("t => document.documentElement.classList.toggle('dark', t)", dark)
    pg.wait_for_timeout(500)
    return Image.open(BytesIO(pg.screenshot(full_page=True))).convert('RGB')


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    for route, forkfile, name in PAGES:
        for w in (1440, 390):
            for theme in ('light', 'dark'):
                dark = theme == 'dark'
                left = shot(pg, f'file://{forkdir}/{forkfile}', dark, w)
                right = shot(pg, f'{base}/examples/{route}?theme={theme}&brand=entelim', dark, w)
                h = min(max(left.height, right.height), MAXH)
                bar = 28
                canvas = Image.new('RGB', (left.width + right.width + 12, h + bar), (128, 128, 128))
                canvas.paste(left.crop((0, 0, left.width, min(left.height, h))), (0, bar))
                canvas.paste(right.crop((0, 0, right.width, min(right.height, h))), (left.width + 12, bar))
                d = ImageDraw.Draw(canvas)
                d.text((6, 8), f'FORK  {name}  {w}px {theme}', fill=(255, 255, 255))
                d.text((left.width + 18, 8), f'TOKEN VERSION (this library, Entelim brand tokens)', fill=(255, 255, 255))
                canvas.save(f'{out}/{name}-{w}-{theme}.png', optimize=True)
    b.close()
