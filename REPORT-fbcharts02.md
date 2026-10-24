# REPORT fbcharts02: the two-by-two matrix (R18) and the cost bridge (R19) on the one chart renderer

Branch `feat/charts-matrix-bridge`, cut from `origin/feat/shadcn-100-compliance`. Nothing pushed.

## What exists now

| Page | Spec | Oracle (Recharts 3.8) | Gallery |
|---|---|---|---|
| `/basecoat/charts/chart-scatter-default` | `data/charts/chart-scatter-default.json` | `out/charts-extra/chart-scatter-default.html` | group "Scatter Charts" |
| `/basecoat/charts/chart-matrix-two-by-two` | `data/charts/chart-matrix-two-by-two.json` | `out/charts-extra/chart-matrix-two-by-two.html` | group "Matrices", spans the row |
| `/basecoat/charts/chart-bar-waterfall` | `data/charts/chart-bar-waterfall.json` | `out/charts-extra/chart-bar-waterfall.html` | group "Bar Charts", spans the row |

The specs come from `scripts/gen_chart_forms.py`. The bridge's offsets, signed labels and total are computed from its steps
(current cost 4,800; savings -900, -700, -500; migration +650; three-year total 3,350).
Screenshots: `shots/fbcharts02/<chart>-<1440|390>-<light|dark>.png`, 12 files.

## Results

- `check_page.py <url> --nearest <name> --browser` prints `SHADCN COMPOSED` at 100% content fidelity on all three pages
  (also asserted in `tests/test_chart_forms.py`).
- `chart_diff.py`, with and without `--hover`: all three pages match their Recharts oracle in DOM, classes, geometry (0.5px)
  and tooltip.
- The 70 upstream chart goldens are unchanged: 67 still pass `chart_diff`, with and without hover. The other three
  (`chart-area-interactive`, `chart-bar-interactive`, `chart-line-interactive`) differ only in date ticks ("Apr 3" against
  "Apr 4"). I ran `chart_diff` on `chart-bar-interactive` in a clean checkout of the base commit `b327186` and it fails the
  same way, so this is not caused by this work (the goldens were probably taken in another time zone).
- `check_ratchet.py`: 385/385 files clean.
- Tests: `tests/test_chart_forms.py` (34) and `tests/test_charts.py` (152) pass in a clean worktree of HEAD
  (`--noconftest`, see "Things to know").

## Renderer commits (each with its test)

1. `ReferenceLine` and `ReferenceArea` (`chart-reference.js`): a `references` list in the spec; x, y or a segment, `ifOverflow`,
   `position`, labels; zIndex 400 and 100.
2. Axis `label` (CartesianAxis) and user `ticks` on an axis.
3. `ScatterChart`, `Scatter`, `ZAxis` (`chart-scatter.js`, the seven d3-shape symbols in `chart-d3.js`, item tooltip).
4. `payloadField` formatter (tooltip label read from the hovered row, so a point is named).
5. A "View" toggle (`data-chart-view`) that swaps the chart panel for the table panel.

The bridge needed no renderer support beyond what already exists plus the references: per-series `fill: "transparent"`,
`tooltipType: "none"`, `legendType: "none"`, `labelList` with a `dataKey` and `null` values were already expressible.
I added no formatter for the signed value: the spec carries it as a `label` field next to the data, and a test asserts
that it agrees with the step.

## Rulings relied on

- **R18**: scatter, ZAxis, ReferenceLine, ReferenceArea ported; square plot (464 x 464 plot in a 560 x 544 container);
  both axes titled in words; one reference line per axis (cost 200, value 50); four quadrant labels; a labelled point per
  option; bubble size from effort; a Table view listing every point.
- **R19**: stacked BarChart spec, transparent base excluded from tooltip, legend and table; falls chart-5, rises chart-2,
  totals primary; signed labels; connectors as ReferenceLine segments.
- **R16**: quadrant label bands are `var(--chart-n)` at fill-opacity 0.1 over the top 6% of each quadrant; text is
  `var(--foreground)`; the plot background has no tint. A test computes the contrast of label text on the composited band in
  light and dark: at least 4.5:1.
- **R15**: no second chart library; nothing added to the diagram engine.
- **R9** (accessibility outranks copying an original): see the two departures below.

## Departures from Recharts, deliberate

1. **Scatter points are focusable images.** Each point is `g.recharts-scatter-symbol` with `role="img"`, an `aria-label` with its
   name and values, a roving tab stop, arrow keys, Home and End, and the tooltip follows the focus. Recharts has no keyboard
   layer for a scatter chart. The svg itself then has no tab stop. `chart_compare.py` lists `role` on that element as the one
   attribute our markup adds (`ADDED_FOR_ACCESSIBILITY`).
2. **The bridge's bars have a 1px `var(--muted-foreground)` outline.** In the library's neutral theme `chart-5` is
   `oklch(0.269)` in both modes, 1.2:1 against the dark card, so a fall disappeared in dark mode. The outline is a spec prop, not
   a class. If your application's theme gives `chart-5` enough contrast against its card, remove `OUTLINE` in
   `gen_chart_forms.py` and the three `stroke` props in the oracle.

## Things you should know or decide

- **The chart tokens of the neutral theme are greys**, so in these screenshots the quadrant tints, the points and the rises are
  grey. The tints are `chart-1, 2, 4, 5` as `bg-chart-n/10` would be; they only look coloured in a theme with coloured chart
  tokens. The check is therefore blind to a colour-contrast problem a coloured theme could introduce between a label and its band.
- **The Tier C check does not exist in code.** `AGENTS.md` says `check_page.py` applies the Tier C conditions when a page has a
  `data-entelim-form` region, but `check_page.py` contains no such rule. The matrix page follows the AGENTS.md conditions by hand
  (one region, `role="region"`, a name, `tabindex="0"`, `overflow-x-auto`, a "View" ToggleGroup with a table alternative, the
  square keeping its shape at 390px) and the tests assert each one, but nothing in the page check enforces them.
- **Where the quadrant label sits.** R18 asks for "four quadrant labels, each on a chart token tint at /10". I read that as a
  label band at the top of each quadrant, as R16 says "header band". The alternative, tinting whole quadrants, would put colour
  behind the data and breaks "the plot background untinted". If you want the whole quadrant tinted, that is a ruling change.
- **The bridge scrolls on a phone** inside a named region (`min-w-[560px]`), like the matrix, because six step names and
  their signed values overlap at 310px. The page check passes either way.
- **Page frames.** The existing chart pages use `style="width: 384px"` frames, which the page check rejects (`styles`). The new
  pages use `max-w-sm` and `max-w-2xl` (672px) instead, which are widths an original uses. The oracles for the wide charts
  are 672px for the same reason, not the 640px I first drew.
- **Port 5100 was held by another session**, so the `conftest.py` live server could not start; I ran the chart tests with
  `--noconftest` (they do not need it). `tests/test_check_page.py` also passes (225 tests together on the dirty tree, before the
  last two commits).
- **Dependencies**: `compliance/golden/node_modules` and `node_modules` in this worktree are symlinks to another worktree's
  install (untracked, gitignored). Recharts is 3.8.0 there. The package source I read for the port is the npm tarball of the
  same version.
- **The package stylesheet** `flask-basecoat.min.css` was rebuilt with the tailwind of that install; compared with the base
  commit the only rules added are `h-[544px]`, `w-[560px]` and `min-w-[560px]`, and none was removed.

## Not done

- No mobile (390px) screenshot of the matrix scrolled to its right edge; the 390px screenshots show the first view.
- Star and wye symbols are tested against d3-shape's output but no page uses them.
- The matrix's Table view shows the Quadrant column from the spec's reference areas; there is no sorting or filtering.
