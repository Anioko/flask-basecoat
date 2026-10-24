# Page gates: what each one reads

`compliance/scripts/check_page.py` is the one page checker. Its gates live in `compliance/scripts/page_gates.py`. Rules come from
criteria-v3 (A2, A5, B2, B8, B9, X9, section 1.5), the library rulings R9, R15 and R16, and help-and-overlays-v1.

## Reading a result

- `PASS` / `FAIL <gate> (n)` per gate, with the first twelve failures. Exit status 1 when any selected gate fails.
- A2 prints `structure: {"percent": ..., "first_difference": {...}}`. The percent is matching nodes over the larger tree. The first
  difference names the node on the page, the node in the original and the path to it.
- A5 prints the percent of differing pixels for `light 1440`, `light 390`, `dark 1440` and `dark 390`. A pixel differs when any channel
  differs by more than 12 of 255. A page that is taller or wider than the golden counts the extra area as different.
- Gates that do not apply (no named original, no chart, no marked region) print nothing to fail; the survey marks them `n/a`.

## A2 normalisation

Text, attributes, `data-*` values and the inside of icons (`svg`) are dropped. A tree is the nesting of `tag[data-slot]`. Runs of identical
sibling units collapse to one. A chart (`data-slot="chart"`) and the sidebar header (a brand slot) are leaves. Closed menus, popovers and
dialogs are not part of the tree, as in the frame check.

## A5 masks

Painted grey before the screenshot: every text run (one box per line), every chart container, avatar, `img`, `video` and `canvas`. For
Tier B and C the content area of the sidebar inset is painted too, so only the frame is compared. The golden is the neutral render; the
branded golden of criteria 1.6 does not exist yet, so brand token values would show as differences until it does.

## R9

The rules axe disables are those of `check_a11y.py` (`region`, `landmark-one-main`, `page-has-heading-one`, `bypass`). The same scan runs on the
golden render and gives "the original's" moderate and minor counts. A departure suppresses only serious and critical findings of its rule,
and only when it gives the rule, the WCAG criterion and a reason.

## Tier C markup contract

The library has no Tier C macros yet. These are the slots and attributes the gates read; the macros that land should emit them.

| Form | Marker | Slots and attributes the gate reads |
|---|---|---|
| C1 diagram | `data-entelim-form="c1"` | one `data-slot="diagram"` root holding one `svg role="img"` with a name; each node `data-slot="diagram-element"` with `data-element-type` (an ArchiMate 3.2 element type) and a `text` label; each edge `data-slot="diagram-relationship"` with `data-relationship-type`; markers under `defs`. Colours only theme tokens and the notation tokens (`success`, `warning`, `layer-*`, each with `-emphasis`); a `layer-*` colour must be the element's own layer. A named Table (or ItemGroup) with one row per element is the list alternative |
| C2 heat map | `c2` | a named `<table>` (caption or `aria-label`) with header cells and rectangular rows; every `td` has a text value; a coloured cell's text is a number or High, Medium, Low, Red, Amber, Green; at most 5 fill steps |
| C3 timeline | `c3` | `data-slot="timeline-axis"` with at least 2 `timeline-tick` children that have text; `timeline-row` per item holding a `timeline-bar` whose `style` is `--x` and `--w`; `timeline-today` with text; a named Table with one row per bar, whose dates match the bars' `data-start` and `data-end` |
| C4 canvas | `c4` | nine Cards titled with the CardTitle wording of the business model canvas, placed with `col-start-*`, `col-span-*`, `row-start-*`, `row-span-*` in a `grid-cols-10` container (five visual columns; ten so the money strip splits in half) |
| C5 document | `c5` | one `h1`; heading levels never skip; numbered headings run without gaps; the first `h2` is a summary, answer, recommendation or decision (or carries `data-answer-first`), with no table, figure or list before it |

Every C1 to C4 region keeps its shape on a phone: an `overflow-x-auto` element that is `role="region"`, `tabindex="0"` and named. Inline
style inside a region holds only `--x`, `--y`, `--w`, `--h`, `--col`, `--row`.

### One diagram engine (R15)

On every page, whether or not it has a C1 region, the check fails: a `<script>` whose source or body belongs to another diagram engine
(mermaid, cytoscape, joint, dagre, elk, gojs, konva, fabric, vis-network, react-flow, bpmn-js, drawio, svg-pan-zoom, jsplumb and the like);
markup those engines emit; an arrowed `line`, `path` or `polyline` outside `data-slot="diagram"`; a `data-panzoom` or `pan-zoom` surface
outside it; and, inside a diagram, any shape not inside a `diagram-element`, `diagram-relationship` or `diagram-notation` group.

## Not covered

C4's Kanban board (stage list, WIP counts, "Move to" menu) and the ArchiMate relationship validity table (which element may connect to which)
have no gate here. The A3 class-set, A4 computed-style and A6/A8 gates of criteria-v3 are not part of this change.
