# Charts golden

Recharts' `ResponsiveContainer` measures its parent with a ResizeObserver, so under `ReactDOMServer` a chart is an
empty `recharts-wrapper` of size 0. The goldens for the 70 shadcn charts and for the `chart` component example are
therefore taken from React + Recharts running in headless Chromium, and saved as static pages with the hydrated DOM
(`svg.recharts-surface` and everything in it). The pages use the same document skeleton as the SSR goldens, so
`check_dom`, `check_recipes`, `check_styles` and `check_a11y` load them unchanged.

## Rebuild

From `compliance/golden`:

```
npm run charts
```

which runs, in order:

```
npx tailwindcss -i golden.css -o out/golden.css --minify    # stylesheet the harness renders with
node charts/build.mjs                                        # charts/bundle.js (esbuild, IIFE, production React)
python charts/render_charts.py                               # out/charts/*.html, *.hover.html, manifest.json, out/chart.html
npx tailwindcss -i golden.css -o out/golden.css --minify    # rescan with the new goldens
```

`python charts/render_charts.py chart-area-default chart` re-renders only the named pages (the manifest keeps the
other entries). The chart specs are regenerated separately from the repo root with
`compliance/golden/node_modules/.bin/tsx compliance/scripts/extract-charts.ts` (see `recipes/charts/README.md`).
`npm run render` (the SSR oracle) no longer writes `out/chart.html`; only the browser path does.

## How a page is taken

| Step | What happens |
| --- | --- |
| Harness | `charts/harness.html?name=<chart>` loads `out/golden.css` and the bundle, `<html class="style-vega">`. Served over a local `http.server` thread at a 1280x900 viewport. |
| Render | `charts/entry.tsx` renders the upstream chart with `createRoot` inside the upstream `ComponentPreview` wrapper (`bg-background *:data-[slot=card]:has-[[data-slot=chart]]:shadow-none`), inside a width frame (below). No provider is added: the charts and the chart example import no Radix tooltip. |
| Ready | `window.__ready` is set two animation frames after every `[data-slot=chart]` has an `svg.recharts-surface` with a non-zero width. |
| Settle | Recharts' entry animations are left on (no upstream prop is changed). The page is saved once `body.innerHTML` has not changed for 300ms and is still unchanged 700ms later (Pie waits 400ms before animating). |
| Save | `out/charts/<name>.html`, `<body data-golden="charts/<name>">`, stylesheet `../golden.css`, body = the frame's outerHTML. The `chart` example is saved to `out/chart.html` with the example wrapper directly in `<body data-golden="chart">`, as the SSR goldens place examples. |

## Canonical widths

The upstream charts page is a 3-column grid. At the 1280px viewport the checks use, one column is 384px and a
full-width chart (`chart-area-interactive`, `chart-bar-interactive`, `chart-line-interactive`) spans 1232px. Both
the golden and our page render a chart inside

```
<div data-chart-frame="regular" style="width: 384px;">  ...ComponentPreview wrapper...  </div>
<div data-chart-frame="full" style="width: 1232px;">    ...ComponentPreview wrapper...  </div>
```

`ChartContainer` is `aspect-video` unless the chart overrides it, so heights follow from the width. The frame has no
`data-slot`, so it is invisible to the slot-paired checks.

## Hover goldens

Every chart that renders a `ChartTooltip` (67 of the 70) also has `out/charts/<name>.hover.html`: the same page with
the real pointer resting on a canonical point and the tooltip open. The tooltip is detected by
`.recharts-tooltip-wrapper .cn-chart-tooltip`; the radix base `ChartTooltipContent` emits no `data-slot`, its root
carries the `cn-chart-tooltip` class.

| Chart kind | Pointer position |
| --- | --- |
| Cartesian (area, bar, line, tooltip) | horizontal centre of the third category, vertical centre of the plot area. For `layout="vertical"` bar charts, the vertical centre of the third category, horizontal centre of the plot area. Category bounds are found by sweeping the pointer across the plot area in 2px steps and watching the tooltip change. |
| Pie, radial | a point inside the second data sector (the interior point nearest the sector's bounding-box centre). |
| Radar | halfway from the chart centre towards the second angle-axis tick; for a radar without an angle axis, towards the second polygon vertex. |

The coordinates (viewport pixels, page not scrolled) are recorded in `out/charts/manifest.json` under `hover`
together with the kind, the target and the tooltip selector, so `check_runtime` can move the pointer to the same
point on our page and compare.

## Charts inside blocks

The dashboard-01 block's "Total Visitors" card (`ChartAreaInteractive` from
`upstream/shadcn/radix/blocks/dashboard-01/components/chart-area-interactive.tsx`) is also a browser golden; the
block's own SSR golden `out/blocks/dashboard-01.html` keeps its empty Recharts shell. `charts/harness.html?name=blocks/dashboard-01`
renders the upstream card alone (no ComponentPreview wrapper, the block has none) inside

```
<div data-chart-frame="block" style="width: 1096px;">
```

1096px is the card's width in the block at the 1440x900 viewport the block checks use, measured on the block page:
1440 - sidebar 288 (`--sidebar-width: calc(var(--spacing) * 72)`) - inset margin 8 - the `px-6` of the wrapping
`<div class="px-4 lg:px-6">` on both sides (2 x 24). The chart container inside the card's `sm:px-6` content is
1048 x 250 (`aspect-auto h-[250px] w-full`), the card 1096 x 394, as in the block. At this width the ToggleGroup is
shown and the Select hidden (`@[767px]/card`).

`render_charts.py` takes it at a 1440x900 viewport and writes, next to the block's SSR golden:

| File | Page |
| --- | --- |
| `out/blocks/dashboard-01.chart.html` | the card after load (`timeRange` = `90d`) |
| `out/blocks/dashboard-01.chart.hover.html` | the pointer on the canonical cartesian point (third category) |
| `out/blocks/dashboard-01.chart.30d.html`, `.chart.7d.html` | a fresh page, then the real pointer clicks the upstream ToggleGroupItem "Last 30 days" / "Last 7 days" (the upstream state change), saved once the DOM settles |

`python charts/render_charts.py blocks/dashboard-01` re-renders only these. The manifest entry is `blocks/dashboard-01`
(`viewport`, `frameWidth`, `golden`, `state`, `initial`, `variants`, and a `hover` whose `dx`, `dy` are relative to the
top-left corner of the chart surface, because the chart sits below the fold of the block). The block lists of the
checks skip `<name>.chart*.html`. `check_dom dashboard-01` draws our block at 1440x900 and compares its
`.recharts-wrapper` with `dashboard-01.chart.html`; `check_runtime dashboard-01` replays the hover against the hover
golden and picks each range with the ToggleGroup (and one with the Select), comparing the redrawn chart and the toggle
item states with the golden of that range. Our card draws it with
`ui.chart_from_spec(chart_spec('dashboard-01-chart-area-interactive'), id='_R_5a_', class='aspect-auto h-[250px] w-full')`;
the spec (`flask_basecoat/data/charts/dashboard-01-chart-area-interactive.json`) holds the upstream rows, the
`var(--primary)` config, the gradients (desktop stops 1.0 / 0.1, mobile 0.8 / 0.1), no legend, the `sinceDays` filter
relative to 2024-06-30 and `onMedia` for upstream's `useIsMobile` effect (7 days below 768px).

## Manifest

`out/charts/manifest.json`, one entry per chart:

```
{ group, fullWidth, width, height,          // the frame's rendered box
  surface: { width, height },               // the first svg.recharts-surface
  slots: [...], rechartsClasses: [...],     // distinct data-slot values and recharts-* classes in the page
  hover: { x, y, kind, target, axis, scrollY, tooltipSelector, slots } | null }
```
