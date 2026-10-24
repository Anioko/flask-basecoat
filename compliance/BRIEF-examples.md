# Brief: port the shadcn-examples screens to Flask-Basecoat

Read `compliance/CONVENTIONS.md` first, then this file.

## Source

`compliance/upstream/shadcn-examples/` holds the pinned source of the shadcn-examples collection (MIT; see `PIN.json`).
Each screen is `examples/<slug>/page.tsx` plus its local `components/`, `data` files and hooks. Shared UI is in
`components/ui/` (new-york style shadcn copies). Never edit anything under `compliance/upstream/`.

## What a port is

A port reproduces the upstream screen: the same sections in the same order and layout, the same text, the same data
(every row, label, number and date from the upstream data files), the same components (a `Card` stays a card, a `Table`
a table, a `Sheet` a sheet, a `DropdownMenu` a dropdown menu with the same items), the same icons where our icon set has
them, and the same interactions the Flask-Basecoat runtime supports (tabs, dialogs, sheets, menus, popovers, toggles,
collapsibles, command palettes, carousels, sliders, tooltips, toasts, calendars). Text must be copied, not paraphrased.

Every shadcn part is written with the component macros (`{% import 'basecoat/index.html' as ui %}`), never as raw
`<button>`, `<input>`, `<select>` or `<textarea>`, and never with raw palette colours (`bg-blue-500`, `#hex`, `rgb()`):
use the theme tokens (`bg-primary`, `text-muted-foreground`, `bg-chart-1` ...). `python compliance/scripts/check_ratchet.py`
enforces this. Layout utilities (grid, flex, gap, padding, widths) are copied from the upstream classNames. Where upstream
uses a raw colour for a status or accent, map it to the nearest token (`text-destructive`, `bg-chart-2`, `bg-muted`...).

Icons: `{{ lucide('name', 'classes') }}` renders Lucide icons from `flask_basecoat/icons.py`. When an icon you need is
missing, add its PascalCase name to the dashboard icon list in `scripts/gen_icons.py` and run `python scripts/gen_icons.py`
(tabler/remix icons map to the nearest Lucide icon). Images: upstream `/public` images are not shipped; use the
`/placeholder.svg?height=H&width=W` route the extension serves, or an avatar fallback with initials. Do not hotlink
third-party image hosts.

Charts: a new spec-driven chart renderer is being written in parallel; until it lands use the existing chart container
API (`data-chart-type`, `data-chart-data`, `data-chart-series`, see `flask_basecoat/templates/examples/_dashboards.html`
`chart` macro for a working example) and keep the upstream chart's data and series. Do not edit
`flask_basecoat/static/js/src/components/chart.js`.

Interactivity that needs application state (drag and drop between kanban columns, a music player's progress, a POS
cart total, a todo list's add/complete) is implemented with a small inline `<script>` in the page that manipulates the
macro-rendered DOM, or with the existing runtime events; keep it in the page template and keep it short.

## Files you create (one set per screen, nothing shared)

- `flask_basecoat/templates/examples/ported/<slug>.html` — extends `examples/_layout.html`, imports the macros.
  Shared pieces for your own screens go in `flask_basecoat/templates/examples/ported/_<group>.html` (prefix `_`).
- `flask_basecoat/templates/examples/ported/<slug>.json` — `{"id": "<slug>", "title": "...", "description": "one
  sentence describing the screen", "tags": ["...", "..."]}`. The screen is then served at `/examples/<slug>` and listed
  on `/examples/` automatically.
- `tests/test_examples_<group>.py` — each screen returns 200, contains its key upstream headings, and has no raw controls.

Do not edit `flask_basecoat/examples.py`, `flask_basecoat/templates/examples/index.html`, the existing screens in
`flask_basecoat/templates/examples/*.html`, `flask_basecoat/templates/examples/_dashboards.html`, or anything under
`flask_basecoat/templates/basecoat/` or `flask_basecoat/static/js/`. If a macro is missing something a screen needs,
write it down in your report instead of changing the package.

## Verification you must do for every screen

1. Text coverage: every user-visible string in the upstream page and its components/data appears in the rendered page.
   Write a small script that extracts the upstream strings (JSX text, string literals rendered as text, data file values)
   and reports the missing ones; report the final percentage per screen and list anything deliberately left out with the
   reason.
2. Component inventory: count the upstream components used (Card, Table, Badge, Button, Tabs, Avatar ...) and confirm
   the port renders the same kinds with `data-slot` (e.g. upstream 6 `Card` -> at least 6 `data-slot="card"`).
3. Visual check: start a throwaway Flask app on a free port other than 5100 (e.g. `python -c "from flask_basecoat.testing
   import make_app; from flask_basecoat.examples import examples_bp; app=make_app(); app.register_blueprint(examples_bp,
   url_prefix='/examples'); app.run(port=5201)"`), take full-page screenshots with Playwright (Python) at 1440x900 in light
   and dark (`?theme=dark`), look at them, and fix overflow, clipping, broken layout, unreadable contrast and empty areas.
   Compare against the upstream layout as you understand it from the source.
4. `python compliance/scripts/check_ratchet.py` reports your files clean, and your tests pass.
5. No console errors in the browser (read them with Playwright).

## Rules

- Python code goes through the Write tool (Bash heredocs mangle backslashes on this machine). Use absolute paths; the
  working directory resets between calls. Prefix commands whose arguments start with `/` with `MSYS_NO_PATHCONV=1`.
- After adding classes, rebuild the stylesheets so the screenshots are right:
  `npx @tailwindcss/cli -i flask_basecoat/static/css/src/flask-basecoat.css -o flask_basecoat/static/css/flask-basecoat.min.css --minify`.
  Other people are rebuilding the same file; rebuild again right before your screenshots.
- Do not start or stop the server on port 5100. Do not run the full test suite or the full browser checks (memory is
  limited); run only your own tests and the ratchet.
- Commit nothing. Wording on the pages contains no status labels, hedges, notes about porting, or mentions of agents
  or tools.
- Report: per screen, the text coverage percentage, the component inventory comparison, what interactions work, what you
  could not reproduce and why, and any macro gaps. Do not soften failures.
