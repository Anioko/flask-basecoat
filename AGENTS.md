# Building pages with Flask-Basecoat (guide for coding agents)

Flask-Basecoat renders shadcn/ui as Jinja macros. A page looks exactly like shadcn when it is assembled from those
macros inside a shadcn original's frame, and a script can prove it. Follow the steps in order; do not design from
memory of what shadcn "looks like".

## 1. Pick the nearest original

Every page starts from one shadcn original that the library renders and checks against upstream:

| Page | Start from | Where to read it |
|---|---|---|
| Signed-in dashboard, list or detail page | `dashboard-01` (sidebar, inset, site header, section cards, interactive area chart, data table) | `flask_basecoat/templates/examples/reference/portfolio.html` (a passing reference page) and `/basecoat/blocks/dashboard-01` |
| Sign in / sign up | `login-01` … `login-05`, `signup-01` … `signup-05` | `/basecoat/blocks/<name>` |
| A different sidebar or navigation | `sidebar-01` … `sidebar-16` | `/basecoat/blocks/<name>` |
| A single component pattern (form field, dialog, table, empty state …) | the component's upstream example | `/basecoat/components/<name>` and `docs/MACROS.md` |
| A chart | one of the 70 upstream charts | `/basecoat/charts/` and `/basecoat/charts/<name>` |

Write the original in the page: `<meta name="shadcn-nearest" content="dashboard-01">` in the `head` block.

## 2. Reuse the frame, change only content

- Signed-in pages: `{% from 'examples/reference/_shell.html' import shell %}` and `{% call shell('Page title') %} … {% endcall %}`.
  The shell is dashboard-01's sidebar, inset and site header with only the labels changed. Change labels and links;
  keep its parts.
- Keep the original's regions. dashboard-01 has four section cards, one chart card and one data table. A page may have
  at most 6 card regions, at most 4 stat cards of one structure, at most 2 chart cards and 1 primary table. When a page
  needs more, split it (a Tabs panel or a linked page); never shrink, tint or decorate to fit.

## 3. Lay out with the originals' recipes

shadcn has no grid system; its originals repeat a few layout recipes. `docs/LAYOUT.md` lists them with the original
each comes from, a snippet and screenshots at 390, 768 and 1440 pixels: the page column, the stat card row, cards that
adapt to their width, content tiles, the centred form, the split screen, the card split in two, paired fields and the
chart grid. Use the recipe whose original matches the page; do not invent column counts, gaps or breakpoints. Prefer
the container queries the originals use (`@xl/main:`, `@[540px]/card:`) over window breakpoints inside the page column.

## 4. Write every visible part with a macro

```jinja
{% import 'basecoat/index.html' as ui %}
{% call ui.card(class='@container/card') %}
  {% call ui.card_header() %}
    {{ ui.card_description(text='Applications') }}
    {% call ui.card_title(class='text-2xl font-semibold tabular-nums') %}1,284{% endcall %}
    {% call ui.card_action() %}{% call ui.badge(variant='outline') %}{{ lucide('trending-up') }}+4.2%{% endcall %}{% endcall %}
  {% endcall %}
{% endcall %}
```

- `docs/MACROS.md` lists every macro, its variants and state arguments, with a usage line from the upstream example.
- Icons: `{{ lucide('name', 'classes') }}` (the Lucide set in `flask_basecoat/icons.py`; add names in `scripts/gen_icons.py`).
- Charts: `{{ ui.chart_from_spec(spec, id='name', class='aspect-auto h-[250px] w-full') }}` with a spec copied from
  `flask_basecoat/data/charts/<chart>.json` (`flask_basecoat.charts.load_spec`), data and config replaced.
  Range controls carry `data-chart-control="chart-<id>"`, `data-chart-state` and, on buttons, `data-chart-value`.
- Never write a raw `<button>`, `<input>`, `<select>`, `<textarea>` or `<table>`; never style a component with classes
  outside its recipe (no extra shadow, radius, colour or border); never put a card in a card.
- Wrapper elements (`div`, `section`, `p`, `span`, `h1`–`h4`) carry layout and type classes only: flex, grid, gap,
  padding, margin, width, column spans, container queries, `text-sm`, `font-medium`, `text-muted-foreground`, `tabular-nums`.
- Colours are theme tokens only (`bg-primary`, `text-muted-foreground`, `border`, `bg-chart-1` …); no palette colours
  (`bg-blue-500`), no hex, rgb or oklch values, no inline style other than CSS custom properties.

## 5. Prove it

```bash
python compliance/scripts/check_page.py /your/page --nearest dashboard-01            # structure, recipes, layout, tokens, density, frame
python compliance/scripts/check_page.py http://127.0.0.1:5000/your/page --browser    # also computed colours and 390px overflow
python compliance/scripts/check_ratchet.py                                           # no raw colours or controls in templates
```

A page is shadcn when the page check prints `SHADCN COMPOSED` at 100% content fidelity. Every failure names the node
and the rule; fix the page, never the check. The check passes every shadcn original the library ships (dashboard-01,
the 10 login and sign-up blocks, the 16 sidebar blocks) and fails each kind of departure (`tests/test_check_page.py`).

## What the library itself proves

`python scripts/shadcn_compliance.py --browser` compares every component example, block and chart with the pinned
upstream render: DOM structure, class recipes, computed styles in light and dark, accessibility and behaviour. See
`compliance/CONVENTIONS.md`.
