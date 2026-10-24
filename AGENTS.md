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

### The gates beyond the page check

Each is a flag of the same command (`--gates` runs all of them). A line starting `FAIL` names the node and the rule; fix
the page, never the check. The markup contract of the Tier C forms is in `docs/PAGE-GATES.md`.

| Gate | Command | Passes when |
|---|---|---|
| A2 structure | `check_page.py /page --nearest login-01 --structure --tier A` | the element tree equals the original's golden render after repeated rows, cards and list items collapse to one each. Prints the percent match and the first differing node. Tier A needs 100%; Tier B and C need the frame (sidebar, inset, header) at 100% |
| A5 pixels | `... --pixels --tier A` | with text runs, chart plots, avatars and images painted out, at most 0.5% of pixels differ from the golden render at 1440 and 390, light and dark. Tier B and C compare the frame only, at 2% (B8) |
| B9 charts | `... --charts` (`--rendered` also draws it) | each chart spec names a pinned chart id (`load_spec` sets it), is that chart's family, has no more series than it (and at most 5), and uses `chart-1` to `chart-5`, `muted-foreground` and the colours the pinned chart itself carries |
| R9 accessibility | `... --a11y [--departures departures.json]` | axe (WCAG 2.2 AA) at 1440 and 390, light and dark, finds no serious or critical issue, even one the original has, unless the page records a departure `{"check": "R9", "rule": "color-contrast", "wcag": "1.4.3", "reason": "..."}` (a file, or `<meta name="shadcn-departure" content="R9 color-contrast wcag=1.4.3 reason=...">`). Moderate and minor issues fail only beyond the original's count |
| Tier C forms | `... --forms [--form c4]` | each region marked `data-entelim-form="c1"` to `"c5"` passes its form's gate: C1 diagram, C2 heat map, C3 timeline, C4 canvas, C5 document. C1 also holds on every page: one diagram engine (R15) |
| Help text | `... --help-text` | no "Nothing here yet", "No data" or "N/A" as visible text; every icon-only button has an accessible name and a Tooltip; no native `title` tooltip on a control; an ordered measure drawn in colour shows its value as text and has a legend (R16) |

`python compliance/scripts/check_page.py --survey report.md` runs every gate on the 27 blocks and all example pages.
Tests: `tests/test_check_page_gates.py` (each gate has a passing fixture and a broken one).

## What the library itself proves

`python scripts/shadcn_compliance.py --browser` compares every component example, block and chart with the pinned
upstream render: DOM structure, class recipes, computed styles in light and dark, accessibility and behaviour. See
`compliance/CONVENTIONS.md`.
