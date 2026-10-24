# Chart specs

One JSON file per upstream chart (`chart-*.json`, 70 files), generated from the pinned sources in
`compliance/upstream/shadcn/charts/` by `compliance/scripts/extract-charts.ts` (TypeScript compiler API; nothing in
the upstream code is executed). Regenerate from the repo root:

```
compliance/golden/node_modules/.bin/tsx compliance/scripts/extract-charts.ts [chart-name ...]
```

## Value encoding

| In the TSX | In the JSON |
| --- | --- |
| string, number, boolean, array and object literals, and top-level `const`s made of them | the literal value |
| boolean shorthand attribute (`accessibilityLayer`) | `true` |
| arrow or function expression (`tickFormatter`, `shape`, `Label content`, `useCallback(fn)`) | the source text as a string; its JSON path is listed in `functionProps` |
| a lucide icon component (`icon: TrendingUp`) | `{"icon": "trending-up", "component": "TrendingUp"}` |
| a `useState` value or setter | `{"state": "<name>"}` / `{"setState": "<name>"}` |
| a JSX element that is not one of the parts below | `{"tag", "props", "children"}` |
| anything else (derived data, template strings, `.map()` loops, comparisons) | `{"unresolved": "<source>"}`, also listed in `unresolved` |

Source text is whitespace-collapsed. An `unresolved` entry is never guessed; the runtime port reads its `source`.

## Schema

```
{
  name, group, fullWidth, description,            // group and fullWidth from charts-app/charts.tsx
  card: {
    props?,                                       // attributes on <Card> (className, data-chart)
    title, description,                           // CardTitle / CardDescription text
    headerClassName, contentClassName, footerClassName,
    footer: [{ text, icons: [lucide names], className, wrappers?: [className of enclosing divs] }]
  },
  chart: {
    type: area | bar | line | pie | radar | radial,
    component,                                    // AreaChart, BarChart, ...
    container: { id, className },                 // ChartContainer
    config: { <key>: { label, color?, theme?, icon? } },
    data,                                         // the chart element's data rows (or unresolved)
    dataSource?: { name, rows },                  // when data is derived: the top-level array it is computed from
    props: { margin, layout, stackOffset, startAngle, endAngle, innerRadius, outerRadius, barSize, ... },
    series: [{ component: Area|Bar|Line|Pie|Radar|RadialBar, dataKey, type, stackId, fill, stroke, fillOpacity,
               strokeWidth, radius, dot, activeDot, shape, label, ...every other prop,
               labelList?: [LabelList props], labels?: [Label props], children?: [other children] }],
    axes: [{ component: XAxis|YAxis|PolarAngleAxis|PolarRadiusAxis, ...props, labels?, labelList?, children? }],
    grid: { component: CartesianGrid|PolarGrid, ...props } | null,
    tooltip: { cursor, ...ChartTooltip props, content: "ChartTooltipContent",
               indicator, hideLabel, hideIndicator, nameKey, labelKey, formatter, labelFormatter, className } | null,
    legend: { ...ChartLegend props, content: "ChartLegendContent", nameKey, className, ... } | null,
    labels: [Label props placed directly in the chart],
    defs?: [{ tag: "linearGradient", props, children: [{ tag: "stop", props }] }],
    other?: [any other direct child]
  },
  interactive: null | {
    state: [{ name, setter, initial }],
    controls: [
      { component: "Select", value, onValueChange, trigger, placeholder, content, items: [{ value, className, label }] | unresolved },
      { component: "button", props, repeat: unresolved }
    ],
    derived: { <local const>: source }             // useMemo / filtered data / ids, as source text
  },
  functionProps: [JSON paths whose value is function source text],
  unresolved: [{ path, source, reason }]
}
```

Props appear only when the upstream chart passes them; Recharts defaults are not filled in.

## Values written by hand

Five charts build part of their props from component state or `.map()` loops, which the extractor leaves as
`unresolved`. Those values were read from the upstream TSX and written into the spec; each file lists them under
`resolvedByHand` (path, upstream source, resolution) and its `unresolved` list is empty. Re-running the extractor
overwrites them, so re-apply them after a regeneration.

| Chart | Path | Written as |
| --- | --- | --- |
| `chart-area-interactive` | `chart.data` | the `chartData` rows; the time-range filter is `interactive.runtime.derive` (`sinceDays`: rows at most 90/30/7 days before 2024-06-30, chosen by the `timeRange` state, initial `90d`) |
| `chart-bar-interactive` | `chart.series[0].fill` | `{"$template": "var(--color-{activeChart})"}` |
| `chart-bar-interactive`, `chart-line-interactive` | `interactive.controls[0].repeat` | one button per key (`desktop`, `mobile`) with its config label and the column total |
| `chart-bar-interactive`, `chart-line-interactive` | `interactive.controls[0].props.data-active` | `true` on the button of the active chart |
| `chart-line-interactive` | `chart.series[0].stroke` | `{"$template": "var(--color-{activeChart})"}` |
| `chart-bar-negative` | `chart.series[0].children[1]` | `chart.series[0].cells`: `var(--chart-1)` for positive rows, `var(--chart-2)` otherwise |
| `chart-pie-interactive` | `interactive.state.activeMonth.initial` | `"january"` (`desktopData[0].month`) |
| `chart-pie-interactive` | `interactive.controls[0].items` | one item per month with a config entry: value, label and colour swatch; `interactive.runtime.computed.activeIndex` is the index of the active month |

## From recipe to runtime spec

`flask_basecoat/charts.py` (`runtime_spec`) turns a recipe into the spec the `chart_from_spec` macro embeds and
the runtime draws: the `chart` part plus `interactive.runtime`, with every function source replaced by a named
formatter. `scripts/gen_chart_pages.py` writes the specs to `flask_basecoat/data/charts/<name>.json` and the pages to
`flask_basecoat/templates/basecoat/pages/charts/<name>.html`.

### Named formatters

A spec carries no JavaScript. Each function-valued prop is `{"$fn": "<name>", ...arguments}`; the registry is
`flask_basecoat/static/js/src/components/chart-format.js` (`window.FlaskBasecoatChart.formatters`), and
`FUNCTION_SOURCES` in `charts.py` maps every upstream function source to its entry.

| Name | Arguments | Used for |
| --- | --- | --- |
| `slice` | `start`, `end` | `tickFormatter={(value) => value.slice(0, 3)}` |
| `localeDate` | `locale`, `options` | date tick and label formatters (`toLocaleDateString`) |
| `configLabel` | | `chartConfig[value]?.label` (ticks, LabelList) |
| `configLabelOfFirstDataKey` | | `labelFormatter={(_, payload) => chartConfig[payload[0].dataKey].label}` |
| `unitValue` | `unit`, `wrap` | tooltip `formatter` showing label, value and unit |
| `unitValueWithTotal` | `unit`, `keys`, `after` | tooltip `formatter` with a Total row after the row with index `after` |
| `centerText` | `lines`, `dominantBaseline` | `Label content` drawing centred text in a pie or radial chart; a line value is `{"text"}`, `{"sum": key}`, `{"pick": key, "index"}` or `{"pickSum": [keys], "index"}` |
| `activeRectangle` | `index`, `props`, `strokeFromPayload` | Bar `shape` highlighting one bar |
| `activeSector` | `index`, `grow` | Pie `shape` enlarging one sector |
| `activeSectorRing` | `index`, `grow`, `ring` | Pie `shape` enlarging one sector and drawing a ring around it |
| `payloadDot` | `r` | Line `dot` coloured with the row fill |
| `iconDot` | `icon`, `size`, `fill`, `stroke` | Line `dot` drawn as a lucide icon |
| `payloadText` | `key`, `fill` | Pie `label` showing a field of the row |
| `stackedTick` | `keys`, `labelKey`, `firstDy` | PolarAngleAxis `tick` with two values and the category |

Interactive specs also use `derive` (`sinceDays`) and `computed` (`indexOf`) entries, implemented next to the chart
runtime in `chart.js`. An `index` argument may be `{"state": name}` to follow the chart state.
