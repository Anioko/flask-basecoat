"""Contrast of body text on tinted surfaces (R16, 4.5:1), measured on real browser pixels.

For every visible text element of each canvas and capability page, in light and dark, it composes the element's
background layer by layer (the way the browser paints it) and computes the WCAG contrast of the text colour against it.
"Tinted" means some layer between the element and the page background is partly transparent (a chart token at 10 percent,
a ramp step of primary) or is a ramp chip. Run against a live server:

    python scripts/contrast_check.py http://127.0.0.1:5731 [--neutral]   # brand tokens by default (?brand=entelim)

Prints the minimum per page and theme and every text under 4.5:1. Exit 1 when any is under 4.5.
"""
import json
import sys

from playwright.sync_api import sync_playwright

JS = r"""
() => {
  const cv = document.createElement('canvas'); cv.width = cv.height = 1; const cx = cv.getContext('2d', {willReadFrequently: true});
  const rgba = (s) => { cx.clearRect(0,0,1,1); cx.fillStyle = '#000'; cx.fillStyle = s; cx.fillRect(0,0,1,1); const d = cx.getImageData(0,0,1,1).data; return [d[0],d[1],d[2],d[3]/255]; };
  const over = (top, bot) => { const a = top[3]; return [0,1,2].map(i => top[i]*a + bot[i]*(1-a)).concat([1]); };
  const lin = (v) => { v/=255; return v<=0.04045 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
  const L = (c) => 0.2126*lin(c[0]) + 0.7152*lin(c[1]) + 0.0722*lin(c[2]);
  const ratio = (a, b) => { const x = L(a), y = L(b); return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05); };
  const out = [];
  const main = document.querySelector('[data-entelim-form], main') || document.body;
  const walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  while (walker.nextNode()) {
    const t = walker.currentNode; if (!t.textContent.trim()) continue;
    const el = t.parentElement; if (seen.has(el)) continue; seen.add(el);
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden') continue;
    const chain = []; for (let e = el; e; e = e.parentElement) chain.unshift(e);
    let bg = [255,255,255,1], tinted = false;
    const base = rgba(getComputedStyle(document.body).backgroundColor); bg = base[3] ? over(base, [255,255,255,1]) : bg;
    for (const e of chain) {
      const c = rgba(getComputedStyle(e).backgroundColor);
      if (c[3] > 0) { if (c[3] < 1 && e !== document.body && e !== document.documentElement) tinted = true; bg = over(c, bg); }
      if (e.hasAttribute && e.hasAttribute('data-ramp-chip')) tinted = true;
      if (e.getAttribute && e.getAttribute('data-slot') === 'badge' && /bg-primary/.test(e.className)) tinted = true;
    }
    const fg = rgba(cs.color); const f = over(fg, bg);
    const recipe = !!el.closest('[data-slot="badge"][data-variant="destructive"], [data-slot="button"][data-variant="destructive"]');
    out.push({recipe, text: t.textContent.trim().slice(0, 40), tinted, ratio: ratio(f, bg), size: parseFloat(cs.fontSize), weight: cs.fontWeight});
  }
  return out;
}
"""

PAGES = None


def pages():
    sys.path.insert(0, '.')
    from flask_basecoat import canvases as r
    return ['canvas/' + c[0] for c in r.CANVASES] + ['capability/' + c[0] for c in r.CAPABILITY]


def main():
    base = sys.argv[1]
    neutral = '--neutral' in sys.argv
    report, bad = {}, 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        for page in pages():
            for theme in ('light', 'dark'):
                pg = b.new_page(viewport={'width': 1440, 'height': 900})
                pg.goto(f"{base}/examples/{page}?theme={theme}" + ('' if neutral else '&brand=entelim'))
                pg.wait_for_timeout(500)
                rows = pg.evaluate(JS)
                pg.close()
                tinted = [x for x in rows if x['tinted'] and not x['recipe']]   # the shadcn destructive Badge and Button recipes are not ours to change
                low = [x for x in tinted if x['ratio'] < 4.5]
                worst = min(tinted, key=lambda x: x['ratio']) if tinted else None
                report[f'{page} {theme}'] = {'texts': len(tinted), 'min': round(worst['ratio'], 2) if worst else None, 'worst': worst['text'] if worst else '', 'under_4_5': [(x['text'], round(x['ratio'], 2)) for x in low][:8]}
                bad += len(low)
        b.close()
    print(json.dumps(report, indent=1))
    print('texts under 4.5:1 on a tinted surface:', bad)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
