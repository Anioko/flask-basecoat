# Component authoring contract (working notes for builders)

Every shadcn/ui registry component (65) and block (27) is ported to Jinja. The upstream React
source is pinned under `compliance/upstream/shadcn/radix` and the rendered upstream DOM for every
component example and block lives in `compliance/golden/out/*.html`. The golden DOM is the target:
our page for a component must produce the same `data-slot` elements, in the same order, with the
same class set and the same state attributes. `python compliance/scripts/check_dom.py <name>` says
whether it does.

## Files

| What | Where |
| --- | --- |
| Macros for component `<name>` | `flask_basecoat/templates/basecoat/<name>.html` (registry name, hyphens kept) |
| Component page (port of upstream `<name>-example.tsx`) | `flask_basecoat/templates/basecoat/pages/components/<name>.html` |
| Block page (port of upstream `blocks/<name>/page.tsx`) | `flask_basecoat/templates/basecoat/pages/blocks/<name>.html` |
| Behaviour script for `<name>` | `flask_basecoat/static/js/src/components/<name>.js` |
| Upstream source | `compliance/upstream/shadcn/radix/ui/<name>.tsx`, examples in `../examples/<name>-example.tsx` |
| Recipe (generated) | `compliance/recipes/<name>.json` |
| Golden DOM | `compliance/golden/out/<name>.html`, blocks in `compliance/golden/out/blocks/<name>.html` |

## Macro rules

1. One macro per exported upstream component, snake_case of the React name:
   `Button` → `button`, `CardHeader` → `card_header`, `DropdownMenuCheckboxItem` → `dropdown_menu_checkbox_item`.
2. Each macro renders exactly the element the React component renders (`div`, `button`, `span`, `a`,
   `nav`, `table`...), with `data-slot` and the full class string from the recipe JSON (`base_classes`,
   plus the cva `variants` classes for the chosen `variant`/`size`), then `class` from the caller appended.
   Class order does not matter; the set must match.
3. State attributes follow Radix exactly as the golden DOM shows them: `data-state="open|closed"`,
   `"active|inactive"`, `"checked|unchecked"`, `"on|off"`, `"expanded|collapsed"`; `aria-expanded`,
   `aria-selected`, `aria-checked`, `aria-pressed`, `aria-haspopup`, `role`, `data-orientation`,
   `data-variant`, `data-size`, `data-side`, `data-align`, `data-inset`, `data-disabled`, `disabled`.
4. Every macro accepts `class=''`, `id=none`, and `attrs={}` (extra attributes rendered verbatim through
   `attrs()` from `basecoat/_base.html`). Content comes from `caller()` when the macro is called with
   `{% call %}`, otherwise from a `text` argument. Macros never emit raw colours, palette classes or
   hex values; everything visual comes from the `cn-*` classes and tokens.
5. Icons: `{{ lucide('chevron-down', 'size-4') }}` renders the same SVG lucide-react emits
   (`class="lucide lucide-chevron-down size-4"`). Use the icon the upstream TSX names in its
   `lucide="..."` prop (PascalCase → kebab-case, drop `Icon`).
6. Interactive parts are static HTML plus `data-state`; behaviour lives in
   `flask_basecoat/static/js/src/components/<name>.js`, registered with
   `FlaskBasecoat.register('<name>', { init(root) {...} })` and selected by `data-slot`.
   Floating content (menus, popovers, tooltips, select lists) is marked `data-floating` and positioned
   by the core (`FlaskBasecoat.float(trigger, content, {side, align, sideOffset})`).
7. Pages import the barrel: `{% import 'basecoat/index.html' as ui %}` and the example wrapper
   `{% from 'basecoat/_example.html' import example, example_wrapper %}`. A page reproduces the
   upstream example section by section, same titles, same elements, same order.

## Charts

The 70 charts and the `chart` example are golden pages taken in headless Chromium, not by ReactDOMServer
(Recharts draws nothing without a layout pass); see `compliance/CHARTS-GOLDEN.md`. Goldens live in
`compliance/golden/out/charts/<name>.html` (plus `<name>.hover.html` with the tooltip open) and the declarative
specs in `compliance/recipes/charts/<name>.json`.

Canonical widths, shared by the golden and our pages: at the 1280px viewport a regular chart renders inside
`<div data-chart-frame="regular" style="width: 384px;">` (one column of the upstream 3-column charts grid) and a
full-width chart (`chart-area-interactive`, `chart-bar-interactive`, `chart-line-interactive`) inside
`<div data-chart-frame="full" style="width: 1232px;">`. Inside the frame comes the upstream ComponentPreview wrapper
`<div class="bg-background *:data-[slot=card]:has-[[data-slot=chart]]:shadow-none">`, then the card. Heights follow
from `ChartContainer`'s `aspect-video` (or the chart's own class). Hover goldens are taken with the pointer at the
point recorded in `out/charts/manifest.json`.

### Our charts

| What | Where |
| --- | --- |
| Spec format, function-source mapping, `<style>` helper | `flask_basecoat/charts.py` |
| Macros `chart_from_spec(spec, id, class)` and `chart_style(chart_id, config)` | `flask_basecoat/templates/basecoat/_chart_spec.html` (exported by the barrel) |
| Runtime (d3 port, layout, polar charts, named formatters, controller) | `flask_basecoat/static/js/src/components/chart-d3.js`, `chart-render.js`, `chart-surface.js`, `chart-polar.js`, `chart-format.js`, `chart.js` |
| Shipped specs | `flask_basecoat/data/charts/<name>.json`, `chart-example-<n>.json` for the `chart` example, `dashboard-01-chart-area-interactive.json` for the dashboard-01 block (browser golden `out/blocks/dashboard-01.chart*.html`, 1096px card at 1440x900, see CHARTS-GOLDEN.md) |
| Chart pages (a `card()` macro plus the width frame) | `flask_basecoat/templates/basecoat/pages/charts/<name>.html`, index at `/basecoat/charts/` |

`python scripts/gen_chart_pages.py [name ...]` regenerates the specs from `compliance/recipes/charts/` and ports the
cards from the goldens. Function-valued props are named formatters (`{"$fn": ...}`), listed in
`compliance/recipes/charts/README.md`. `python compliance/scripts/chart_diff.py <name> [--hover]` prints the
differences of one chart against its golden.

## Self-check before reporting done

```
python compliance/scripts/check_dom.py <name>        # DOM parity with the golden markup
python compliance/scripts/check_recipes.py <name>    # every data-slot carries its recipe classes
python compliance/scripts/check_styles.py <name>     # computed styles against the golden page (Chromium, light + dark)
python compliance/scripts/check_a11y.py <name>       # axe: no findings beyond upstream's
python compliance/scripts/check_runtime.py <name>    # no script errors; popups, tabs, toggles behave like Radix; charts: hover replay
python -m pytest tests/test_shadcn_components.py -k <name> -q
```

A component is done when all of them pass. `python scripts/shadcn_compliance.py --browser` runs everything
and writes `compliance/REPORT.json`. Report the actual output, not a summary of it.
