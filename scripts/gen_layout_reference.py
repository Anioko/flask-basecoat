"""Generate docs/LAYOUT.md and its screenshots: the layout recipes the shadcn originals use.

shadcn/ui has no grid system or grid component. Its originals repeat a small set of layout recipes made of Tailwind
utilities and container queries. Each recipe below names the original it comes from; before anything is written the
script checks that the recipe's classes appear together on one element of that original's pinned render (or source),
so the reference cannot describe a pattern shadcn does not use. Screenshots of each recipe, taken from the library's
own port of the original, are saved at 390, 768 and 1440 pixels wide.

    python scripts/gen_layout_reference.py            # verify, write docs/LAYOUT.md and docs/layout/*.png
    python scripts/gen_layout_reference.py --no-shots # verify and write the document only
"""
import pathlib
import re
import sys
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
GOLDEN = ROOT / 'compliance' / 'golden' / 'out'
SHOTS = ROOT / 'docs' / 'layout'
WIDTHS = (390, 768, 1440)

RECIPES = [
    {
        'id': 'page-column',
        'name': 'Page column',
        'source': ('block', 'dashboard-01'),
        'classes': ['flex', 'flex-col', 'gap-4', 'py-4', 'md:gap-6', 'md:py-6'],
        'page': '/basecoat/blocks/dashboard-01',
        'selector': '[class~="@container/main"]',
        'use': 'The content column of a signed-in page, inside the sidebar inset. The column is a container '
               '(`@container/main`), so the rows inside respond to its width, not the window. Every row carries its '
               'own side padding `px-4 lg:px-6`.',
        'snippet': '''<div class="flex flex-1 flex-col">
  <div class="@container/main flex flex-1 flex-col gap-2">
    <div class="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
      <div class="px-4 lg:px-6"> …a row… </div>
    </div>
  </div>
</div>''',
    },
    {
        'id': 'stat-row',
        'name': 'Stat card row',
        'source': ('block', 'dashboard-01'),
        'classes': ['grid', 'grid-cols-1', 'gap-4', 'px-4', 'lg:px-6', '@xl/main:grid-cols-2', '@5xl/main:grid-cols-4'],
        'page': '/basecoat/blocks/dashboard-01',
        'selector': '[class~="@5xl/main:grid-cols-4"]',
        'use': 'Up to four KPI cards of one structure. One column, two when the page column is wide, four when it is '
               'very wide. The cards use `@container/card` so their value grows with the card.',
        'snippet': '''<div class="grid grid-cols-1 gap-4 px-4 lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
  {% call ui.card(class='@container/card') %} … {% endcall %}   {# ×4 #}
</div>''',
    },
    {
        'id': 'card-container',
        'name': 'Card that adapts to its width',
        'source': ('block', 'dashboard-01'),
        'classes': ['@container/card'],
        'page': '/basecoat/blocks/dashboard-01',
        'selector': '[data-slot="card"][class~="@container/card"]:has([data-slot="chart"])',
        'use': 'A card is a container; its parts switch at the card width, not the window width: '
               '`@[250px]/card:text-3xl` for a KPI value, `@[540px]/card:block` for a longer description, '
               '`@[767px]/card:flex` to show a toggle group instead of a select.',
        'snippet': '''{% call ui.card(class='@container/card') %}
  {% call ui.card_header() %}
    {{ ui.card_title(text='Total Visitors') }}
    {% call ui.card_description() %}<span class="hidden @[540px]/card:block">Total for the last 3 months</span><span class="@[540px]/card:hidden">Last 3 months</span>{% endcall %}
    {% call ui.card_action() %} …toggle group `hidden @[767px]/card:flex`, select `@[767px]/card:hidden`… {% endcall %}
  {% endcall %}
{% endcall %}''',
    },
    {
        'id': 'content-tiles',
        'name': 'Content tiles',
        'source': ('block', 'sidebar-07'),
        'classes': ['grid', 'auto-rows-min', 'gap-4', 'md:grid-cols-3'],
        'page': '/basecoat/blocks/sidebar-07',
        'selector': '[class~="md:grid-cols-3"][class~="auto-rows-min"]',
        'use': 'Three equal tiles above a main area (every sidebar block). sidebar-12 uses five columns '
               '(`md:grid-cols-5`). The main area below is `min-h-[100vh] flex-1 rounded-xl md:min-h-min`.',
        'snippet': '''<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
  <div class="grid auto-rows-min gap-4 md:grid-cols-3"> …three tiles… </div>
  <div class="min-h-[100vh] flex-1 rounded-xl md:min-h-min"> …main area… </div>
</div>''',
    },
    {
        'id': 'centered-form',
        'name': 'Centred form',
        'source': ('block', 'login-01'),
        'classes': ['flex', 'min-h-svh', 'w-full', 'items-center', 'justify-center', 'p-6', 'md:p-10'],
        'page': '/basecoat/blocks/login-01',
        'selector': '[class~="min-h-svh"][class~="md:p-10"]',
        'use': 'A single card form centred on the page, at most `max-w-sm` wide (sign in, sign up, short forms). '
               'Fields inside are a `FieldGroup`, which is a container (`@container/field-group`).',
        'snippet': '''<div class="flex min-h-svh w-full items-center justify-center p-6 md:p-10">
  <div class="w-full max-w-sm">{% call ui.card() %} …FieldGroup… {% endcall %}</div>
</div>''',
    },
    {
        'id': 'split-screen',
        'name': 'Split screen',
        'source': ('block', 'login-02'),
        'classes': ['grid', 'min-h-svh', 'lg:grid-cols-2'],
        'page': '/basecoat/blocks/login-02',
        'selector': '[class~="lg:grid-cols-2"][class~="min-h-svh"]',
        'use': 'Form on one half, cover image on the other, from 1024px wide; the form column is `max-w-xs`.',
        'snippet': '''<div class="grid min-h-svh lg:grid-cols-2">
  <div class="flex flex-col gap-4 p-6 md:p-10"> …logo, form `w-full max-w-xs`… </div>
  <div class="relative hidden bg-muted lg:block"> …cover image… </div>
</div>''',
    },
    {
        'id': 'card-split',
        'name': 'Card split in two',
        'source': ('block', 'login-04'),
        'classes': ['grid', 'p-0', 'md:grid-cols-2'],
        'page': '/basecoat/blocks/login-04',
        'selector': '[data-slot="card-content"][class~="md:grid-cols-2"]',
        'use': 'A form and an image side by side inside one card, from 768px wide; the card column is '
               '`w-full max-w-sm md:max-w-4xl`.',
        'snippet': '''<div class="w-full max-w-sm md:max-w-4xl">
  {% call ui.card(class='overflow-hidden p-0') %}{% call ui.card_content(class='grid p-0 md:grid-cols-2') %}
    <form class="p-6 md:p-8"> … </form>
    <div class="relative hidden bg-muted md:block"> …image… </div>
  {% endcall %}{% endcall %}
</div>''',
    },
    {
        'id': 'paired-fields',
        'name': 'Paired fields',
        'source': ('block', 'signup-03'),
        'classes': ['grid', 'grid-cols-2', 'gap-4'],
        'page': '/basecoat/blocks/signup-03',
        'selector': '[data-slot="field"][class~="grid-cols-2"]',
        'use': 'Two short fields on one row inside a form (password and confirmation). From 640px only: '
               '`grid gap-4 sm:grid-cols-2` (login-05, signup-05). Three provider buttons: `grid grid-cols-3 gap-4` (login-04).',
        'snippet': '''{% call ui.field(class='grid grid-cols-2 gap-4') %}
  {% call ui.field() %} …password… {% endcall %}
  {% call ui.field() %} …confirm… {% endcall %}
{% endcall %}''',
    },
    {
        'id': 'chart-gallery',
        'name': 'Chart grid',
        'source': ('tsx', 'compliance/upstream/shadcn/charts-app/page.tsx'),
        'classes': ['grid', 'flex-1', 'gap-10', 'md:grid-cols-2', 'md:gap-6', 'lg:grid-cols-3', 'xl:gap-10'],
        'page': '/basecoat/charts/',
        'selector': '[class~="lg:grid-cols-3"][class~="xl:gap-10"]',
        'use': 'Chart cards two to a row from 768px and three from 1024px; a chart that needs the full width spans '
               'the row (`md:col-span-2 lg:col-span-3`).',
        'snippet': '''<div class="grid flex-1 scroll-mt-20 items-stretch gap-10 md:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:gap-10">
  {% call ui.card() %} …chart… {% endcall %}
  {% call ui.card(class='md:col-span-2 lg:col-span-3') %} …full-width chart… {% endcall %}
</div>''',
    },
]


def class_sets(recipe):
    kind, ref = recipe['source']
    if kind == 'block':
        text = (GOLDEN / 'blocks' / f'{ref}.html').read_text(encoding='utf8')
        return [set(c.replace('&amp;', '&').split()) for c in re.findall(r'class="([^"]*)"', text)]
    text = (ROOT / ref).read_text(encoding='utf8')
    return [set(c.split()) for c in re.findall(r'className="([^"]*)"', text)]


def verify():
    problems = []
    for r in RECIPES:
        want = set(r['classes'])
        if not any(want <= s for s in class_sets(r)):
            problems.append(f"{r['id']}: {sorted(want)} do not appear together in {r['source'][1]}")
    return problems


def scale():
    """The spacing values the originals use, from the page check's vocabulary."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('check_page', ROOT / 'compliance' / 'scripts' / 'check_page.py')
    cp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cp)
    v = cp.LAYOUT_VOCAB

    def values(prefix_re):
        out = sorted({re.sub(r'^.*?:', '', t) for t in v if re.match(prefix_re, cp.strip_variant(t))},
                     key=lambda t: (len(t), t))
        return out
    return {
        'gap': values(r'^gap-'),
        'padding': values(r'^p[xytrbl]?-'),
        'columns': sorted({t for t in v if 'grid-cols-' in t and '[' not in t}),
        'width': sorted({re.sub(r'^.*?:', '', t) for t in v if cp.strip_variant(t).startswith('max-w-') and '[' not in t}),
    }


def shots():
    from playwright.sync_api import sync_playwright
    from flask_basecoat.testing import make_app
    app = make_app()
    port = 5410
    threading.Thread(target=lambda: app.run(port=port, use_reloader=False), daemon=True).start()
    time.sleep(1.5)
    SHOTS.mkdir(parents=True, exist_ok=True)
    taken = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for r in RECIPES:
            for w in WIDTHS:
                pg = b.new_page(viewport={'width': w, 'height': 900})
                pg.goto(f"http://127.0.0.1:{port}{r['page']}")
                pg.add_style_tag(content='*,*::before,*::after{transition:none!important;animation:none!important}')
                pg.wait_for_timeout(600)
                el = pg.query_selector(r['selector'])
                if el and el.is_visible():
                    out = SHOTS / f"{r['id']}-{w}.png"
                    box = el.bounding_box()
                    pad = 8
                    clip = {'x': max(0, box['x'] - pad), 'y': max(0, box['y'] - pad),
                            'width': min(box['width'] + 2 * pad, w), 'height': min(box['height'] + 2 * pad, 900)}
                    pg.screenshot(path=str(out), clip=clip, full_page=True)
                    taken.setdefault(r['id'], []).append(w)
                pg.close()
        b.close()
    return taken


def main(argv):
    problems = verify()
    if problems:
        print('recipes not found in their originals:')
        for p in problems:
            print('  ', p)
        return 1
    taken = {} if '--no-shots' in argv else shots()
    sc = scale()
    out = ['# Layout recipes', '',
           'shadcn/ui has no grid system and no grid component. Its originals repeat a few layout recipes made of '
           'Tailwind utilities and container queries, and a page looks like shadcn when it uses the same ones. Each '
           'recipe below comes from a named original; `scripts/gen_layout_reference.py` checks that its classes appear '
           'together in that original before writing this page, and the page check '
           '(`compliance/scripts/check_page.py`) reports any grid, gap, padding, margin or width value that no '
           'original uses.', '',
           '## Rules the originals follow', '',
           '- **Containers decide layout.** The page column is `@container/main` and cards are `@container/card`; rows '
           'and card parts switch on those widths (`@xl/main:`, `@5xl/main:`, `@[540px]/card:`). Window breakpoints '
           '(`md:`, `lg:`) are used for the page frame, split screens and the chart grid.',
           '- **Spacing comes from one short scale.** Regions are `gap-4`, `md:gap-6` apart; page rows are inset '
           '`px-4 lg:px-6`; card parts use the card recipe and are not padded again.',
           '- **Rows follow the original\'s count.** Four stat cards; three content tiles (five in sidebar-12); two or '
           'three chart cards; two paired fields. Wider pages split into tabs or linked pages instead of adding columns.',
           '', '## Values in use', '',
           '| Kind | Values the originals use |', '|---|---|',
           f"| Gap | {', '.join('`' + v + '`' for v in sc['gap'])} |",
           f"| Padding | {', '.join('`' + v + '`' for v in sc['padding'][:40])} |",
           f"| Columns | {', '.join('`' + v + '`' for v in sc['columns'])} |",
           f"| Maximum width | {', '.join('`' + v + '`' for v in sc['width'])} |", '']
    for r in RECIPES:
        kind, ref = r['source']
        src = f'`{ref}`' if kind == 'block' else f'the upstream charts page (`{ref}`)'
        out += [f"## {r['name']}", '', f"From {src}. {r['use']}", '', '```html', r['snippet'], '```', '']
        if r['id'] in taken:
            out.append(' '.join(f"![{r['name']} at {w}px](layout/{r['id']}-{w}.png)" for w in taken[r['id']]))
            out.append('')
            out.append('Widths: ' + ', '.join(f'{w}px' for w in taken[r['id']]) + '.')
            out.append('')
    (ROOT / 'docs' / 'LAYOUT.md').write_text('\n'.join(out), encoding='utf8')
    print(f"docs/LAYOUT.md: {len(RECIPES)} recipes verified; screenshots: {sum(len(v) for v in taken.values())}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
