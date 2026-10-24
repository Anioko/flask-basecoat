# REPORT: canvases and capability map in Flask-Basecoat (fbcanvas01)

Branch `feat/canvases-capability-map`, cut from the library at 07ee928. Nothing pushed. The library owner reviews and pushes.

## Summary
- 14 strategy canvases, each a macro under `basecoat/canvas/`, each with Northwind Logistics data (`data/canvases/<slug>.json`), an example page (`/examples/canvas/<slug>`) and the shared frame (view switch, one marked scroll region, list route, edit Sheet).
- Capability-map family under `basecoat/capability_map/`: map, tree, applications by capability, planning, four dialogs. Pages at `/examples/capability/<slug>`. Grouped by `capability_type`.
- check_page `--browser` on a live server: all 19 new pages print `SHADCN COMPOSED`, content fidelity 100.0%, no off-token colour, no overflow at 390 (output of the run was kept in /tmp/pagechecks.txt and is reproduced by the command at the end).
- check_ratchet: 426 of 426 files clean. Full suite: 830 passed, 12 skipped, 1 failed, 4 collection errors, all five from before this work (see Tests).
- Registry: `flask_basecoat/canvases.py` (one list; examples blueprint, gallery, tests and docs read it). Gallery index lists both families. `docs/MACROS.md` has the entries (hand-written `docs/MACROS-canvas.md`, appended by the generator).

## Decisions you should check (the departures)
1. **I changed `compliance/scripts/check_page.py`.** It had no Tier C mode, and the brief asks for results "at its C tier". Three commits, all additive or fixes:
   - `form` check: for a page with one `data-entelim-form` element it requires `role="region"` with a name, `tabindex="0"`, `overflow-x-auto`, geometry only through `--x --y --w --h --col --row`, a ToggleGroup named "... view" and a Table. The marked region counts as one region in the density check. A page without a marked region is checked exactly as before (the 27 blocks and the reference page pass; `tests/test_check_page.py` 37 passed after the change).
   - the form check skips the chart's own wrapper styles (blue ocean).
   - `--browser` token scan: `walk` in `COLLECT_JS` never reached declarations because current Chromium gives every style rule an empty `cssRules`; it collected 4 custom properties, so chart greys and the destructive colour were flagged off-token. The fix only adds token values to the allowed set. This is a defect in the tool, not in the pages, but it is the one change you might not want; revert it alone and the chart and destructive colours will flag.
2. **Ramp: heat is a swatch or bar, the text sits on the card.** A full tile fill cannot hold text at 4.5:1 for both the library's neutral tokens and the brand tokens with five distinguishable steps (the two flip at different steps; for example step 80 needs light text on neutral and dark text on brand). So every tile shows a heat bar and a swatch beside the figure in words ("Maturity 3/5, Defined"). Recognisable-form-v1 says "every box is shaded"; this is a band, not a fill.
3. **Chart ramp tokens not used for maturity.** `--chart-1..5` are an unordered hue set under the brand decision, so maturity is one sequential ramp of `--primary` at 20/40/60/80/100 percent (`bg-primary/20` ... `bg-primary`), step 0 a dashed outline.
4. `cn-sheet-close` / `cn-dialog-close` are written as `absolute top-4 right-4` (the check does not know the cn- class and the pinned CSS defines it as exactly that).
5. Capability grouping: roots are grouped by their own `capability_type`; sub-capabilities nest under their parent whatever their own type; the table views group every capability by its own type. A value that is empty or not one of the three goes in "Type not set". `type`, `domain` and the parent's value are never read (tested).
6. Applications by capability groups capabilities by type (as the addition says), not applications by technical domain as the source did; the application domain is only counted in a stat card.

## Ramp distances (OKLab, closest pair of the five steps, Machado severity 1.0 in linear sRGB)
Modelled by `python scripts/capability_ramp.py`; asserted by `tests/test_capability_ramp.py` (threshold 0.08).

| Token set, theme | normal | protanopia | deuteranopia | tritanopia |
|---|---|---|---|---|
| Library tokens (neutral), light | 0.147 | 0.147 | 0.147 | 0.147 |
| Library tokens, dark | 0.127 | 0.127 | 0.127 | 0.127 |
| Entelim brand tokens, light | 0.100 | 0.099 | 0.101 | **0.080** |
| Entelim brand tokens, dark | 0.093 | 0.097 | 0.091 | 0.093 |

Measured again on real browser pixels (colour-mix over the card, 8-bit): minimum 0.08004, again brand light, tritanopia, steps 80 and 100. **That pair passes by 0.00004.** If you want margin, `20/38/56/76/100` gives 0.0906 measured, at the cost of the opacity list in criteria 1.5 (20, 40, 60, 80, 100); `20/40/60/78/100` gives 0.083. I kept the criteria's steps. Step 0 (no fill) against step 20 is 0.099 to 0.168 in every case, and is also marked by a dashed outline. A text label or number accompanies every swatch.

## Canvases
Form tiers follow the registry. Check column: static `check_page` and `--browser`, both SHADCN COMPOSED at 100.0%.

| Canvas | Form | Built | Differs from the source, and why |
|---|---|---|---|
| Business Model Canvas | C4 | Osterwalder and Pigneur ten-column grid, nine blocks, canonical DOM order, CC BY-SA credit line | Notes are chips, not a textarea (recognisable-form rule 5). Hairline-shared-border technique is not possible on a Card, so blocks are Cards with a gap inside one bordered wrapper. |
| Lean Canvas | C4 | Maurya's form, numbers 1 to 9, three sub-areas, equal money halves | Sub-areas follow the notes instead of sitting at the foot of the block. |
| Value Proposition Canvas | C4 | Value Map square, Customer Profile circle, Fit column, SVG outlines | Circle is cut by one horizontal and one vertical line, not three rays (rectangular Cards). 1500px natural width. Credit line says CC BY-SA, copied from the BMC pattern, **not verified for this canvas**. |
| SWOT | C2 | Helpful/Harmful by Internal/External matrix | Row headers unrotated text. |
| PESTLE | C2 | 3x2, P E S / T L E | Impact badges of the preview dropped (not in the published form). |
| Porter's Five Forces | C2 | cross, arrows inward | Intensity badges dropped. |
| Ansoff Matrix | C2 | products across, markets down, risk row | none beyond layout. |
| Balanced Scorecard | C2 | vision at centre, four perspectives, cause-and-effect arrows, a Table per perspective | Customer on the right and Internal on the left (the preview's placement; the commonly drawn figure swaps them, and I could not open the original). Not editable. |
| Blue Ocean | C2 | strategy canvas line chart (`ui.chart_from_spec`) plus four actions | Four actions are not editable (the edit script would rebuild the list and drop the score rows). |
| McKinsey 7S | C2 | hexagon, Shared Values centre, hard and soft S | Preview had hard on top and soft below; changed to the hexagon **from memory of the published figure, not checked against a source**. No arrowheads. |
| Empathy Map | C4 | Says, Thinks, Does, Feels around the user, Pains and Gains strip | XPLANE four-quadrant form, not the See/Hear variant. No avatar. Credit line carries no licence claim (not verified). |
| Product Vision Board | C4 | Vision, then four columns (Pichler) | Credit line carries no licence claim (not verified). |
| OKR | C2 | objectives, key results with `ui.progress`, score derived from start, current, target | Three objectives not one; no destructive badge (Off track is default variant, icon and words). |
| Wardley Map | C1 | axes, four stages, 13 components as keyboard buttons, dependencies, dashed movements, Sheet per component | HTML overlay plus SVG instead of one SVG; arrowheads are two short lines (`marker` is not an allowed element). |

Each has a list route (a real Table with the same rows) and Tab reaches every control. Note boxes are editable through the shared Sheet.

## Capability map
- **Map** (C2): Heat by ToggleGroup (maturity, importance, investment), legend of Badges with swatch and word, bands Strategic, Operational, Supporting, then "Type not set" (the example data has one untyped capability with one child), tiles nesting sub-capabilities with disclosure, name opens a detail Sheet, Map|List view.
- **Tree** (C2): same data as an indented tree with disclosure buttons; Tree|Table view.
- **Applications by capability** (C2): one Table with a row group per type, "Coverage view" filter (all, or capabilities without an application), four section cards.
- **Planning** (Tier B, no marked region): four section cards and the gap Table (below Managed, most urgent first).
- **Dialogs** (Tier B): form (type has the three values and "Not set"; a sub-capability's type and level are locked), map details, type descriptions, delete confirmation naming the sub-capabilities that go with it. Saving announces the result and emits `basecoat:capability-save` / `basecoat:capability-delete`; the example pages store nothing.

## Not done, or worse than the source
- Source live editing of the capability map (adding and deleting tiles in the page) is not carried over; the dialogs emit events instead. Planning has no roadmap tab and no investment tab; the maturity-trend chart of the source application page is not on applications by capability.
- No scroll-snap and no tap-to-open editor on a phone for the canvases (recognisable-form 4); the region scrolls and the Sheet opens from the pencil button.
- Not checked by a person: that each form is recognised at a glance beside its reference image (the 7S hexagon and the balanced scorecard most need it); text colour on matrix cells is not applicable (text is never on a step).
- The 390 screenshots of the first group were looked at only in part; the browser tests check scroll and column count for every page.
- Playwright tests use their own free-port server and `make_app`; run them with `--noconftest` in parallel, or without it alone (the repo's session fixture binds port 5100).
- `origin/feat/shadcn-100-compliance` had one commit this branch does not contain when I started (git reported the branches diverged); rebase before the PR.

## Tests
New: `tests/test_canvases.py`, `tests/test_canvases_browser.py` (render, keyboard to every control, list view, phone scroll and column count, light and dark, edit sheet, per canvas), `tests/test_canvas_{balanced_scorecard,okr,blue_ocean,wardley_mapping}.py`, `tests/test_capability_map.py` (grouping, never dropped, old `type` key not read, headings in order for all three views, pages at their tier, browser behaviour), `tests/test_capability_ramp.py`.
Full suite (`python -m pytest -q --continue-on-collection-errors`, 22 minutes): **830 passed, 12 skipped, 1 failed, 4 errors.**
- The failure, `tests/test_shadcn_components.py::test_block_dom_matches_upstream[dashboard-01]` (chart tick labels `May 16` against `May 15`, a date-dependent chart), fails identically on the untouched base commit 07ee928. Not caused by this work, not fixed.
- The four errors (`test_flash_messages`, `test_forms_browser`, `test_sidebar_browser`, `test_table_styling_browser`) are `ModuleNotFoundError: selenium` at collection; selenium is not installed in this environment. Same on the base commit.
- The 12 skips are the generic tests that need `boxes` data, for the four structured canvases (they have their own test files).
Reproduce:
```
python -m pytest -q
python compliance/scripts/check_ratchet.py
python compliance/scripts/check_page.py http://127.0.0.1:<port>/examples/canvas/<slug> --nearest dashboard-01 --browser
python scripts/capability_ramp.py
```
