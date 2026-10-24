# REPORT: look round R16 on the canvases and the capability map (fbcanvas01b)

Branch `feat/canvases-capability-map`. Nothing pushed. This round changes the look of every canvas and capability page and applies the library owner's review notes on round 1. [REPORT-fbcanvas01.md](REPORT-fbcanvas01.md) still describes round 1; where this report contradicts it, this one is later.

## Summary
- All 19 pages print `SHADCN COMPOSED` at 100.0% content fidelity with `check_page --browser` on a live server (14 canvases, 5 capability pages). `check_ratchet`: 426 of 426 files clean.
- Text on tinted surfaces, measured on browser pixels in the Entelim brand tokens: **no text under 4.5:1 in light or dark** (lowest 4.53). With the library's own neutral tokens the capability chips fail on steps 3 and 4 (see Contrast). That is a limit of the neutral token file, not of the page.
- Ramp 20/38/56/76/100: closest pair of the five steps is **0.0896 OKLab** (threshold 0.08, was 0.08004). Step 76 is drawn at 80 in dark mode so its text holds 4.5:1.
- Side-by-side screenshots against the fork, 60 files, in `shots/fbcanvas01b/` (left fork, right token version; 14 canvases and the capability map; 1440 and 390; light and dark).
- Full suite: 869 passed, 12 skipped, 1 failed, 4 collection errors; the failure and the four errors are the same five as in round 1 and on the base commit (see Tests).

## What changed
**Capability map family** (map, tree, applications by capability, planning; `capability_map/_parts.html` is the shared source)
- Each capability is a Card on the card surface: one lucide icon (`capability_icon`, name keywords then the type's icon, every name in `icons.py`), name at `text-base`, two lines of description, a **filled Badge chip in the ramp step with the level in words** ("Managed, 4/5"; "High importance" and "Medium investment" for the other two measures), `L0` and "n sub" Badges, the owner line, and the Button "Show n sub-capabilities" / "Hide n sub-capabilities". No coloured edge, no stripe, no solid fill: the test `test_capability_card_has_icon_chip_in_words_owner_and_a_button_for_sub_capabilities` asserts it. Sub-capabilities are sibling Cards below the parent, indented with padding, never a card in a card.
- Heat switch (maturity, importance, investment) recolours the chips and swaps their words. The legend above the map is a row of filled chips, one per step, with the word inside, and "Not assessed" dashed.
- Type groups: header band tinted `bg-chart-1/10 border-chart-1/30` (Strategic), chart-2 (Operational), chart-3 (Supporting), neutral muted (Type not set), each with its icon (target, settings, shield, circle-help), description and a count Badge. In the applications table the group row carries the same tint and icon.
- Planning: the gap bar is the Progress macro with a ramp token on its indicator (gap 1 to 4 maps to steps 2 to 5); the words "3 levels" sit beside it. Priority Badges are unchanged (the existing destructive, default, secondary and outline variants).
- Empty group: Empty macro with what is missing, why, and an "Add a strategic capability" Button that opens the existing form dialog.

**Canvases** (`canvas/_frame.html`; every canvas that has boxes, plus Balanced Scorecard, OKR and Blue Ocean)
- One note card per entry (Item macro, `variant=outline size=xs`), one `<li>` per entry, no bulleted text.
- Header band per box: zone tint (`bg-chart-n/10`, `border-chart-n/30`), the zone name as text, the icon, the title, the entry count Badge (kept in step when a note is saved), the framework's question visible, the "i" popover (guidance and "Example from Northwind Logistics: ...", taken from the canvas's own seed data) and the edit button, both icon-only buttons with a tooltip.
- A hover card per note card: type (from canvas-archimate-mapping), box, canvas, owner, last change.
- Empty state (Empty macro): "No channels yet", the framework question and "Add the first entry, or pick one from your model", with an "Add to Channels" Button that opens the edit Sheet. It is in the page, hidden, when the box has entries, and the script shows or hides it on save. The list route's empty row reads "Empty. Add the first entry from the canvas view." The words "Nothing here yet", "No data" and "N/A" appear on no canvas (tested for all 14).
- Metadata in one file: `flask_basecoat/data/canvases/_boxes.json` (zone, zone label, element type, guidance per box), read through `canvas_box_meta`.
- Zones (chart token and framework zone): BMC infrastructure chart-3 (partners, activities, resources), offer chart-1, customers chart-2 (relationships, channels, segments), finance chart-5. Lean: problem 2, solution 3, offer 1, customers 4, finance 5. Value Proposition: value map 1, customer profile 2. SWOT: helpful 3, harmful 2. Porter: rivalry 1, threat from outside 2, bargaining power 4. Ansoff: one zone per quadrant. 7S: hard 1, soft 2, core 5. Empathy: who 1, what they express 4, results 2. Vision board: vision 1, customers 2, product 3, business 5. PESTLE has no zones in the published form: all six share chart-1.
- The note script (`canvas.js`) clones a `<template data-canvas-note-template>`, so a note added from the Sheet is the same note card with its hover card.

**Brand tokens, opt-in.** The library's chart tokens are neutral greys, so tints on the default theme are grey; that is what you saw. `flask_basecoat/static/css/entelim-brand.css` carries foundations-v1 section 8 (primary, ring, chart-1 to chart-5, light and dark); the example layout links it when the URL has `?brand=entelim`. All screenshots and the contrast run use it. Remove the file and the layout line if you do not want it in the library.

**Review notes from round 1**
- Ramp 20/38/56/76/100: `_parts.html`, `capability-map.js`, `scripts/capability_ramp.py`; the test class assertion follows; the 0.08 threshold assertion still holds at 0.0896 (and is not lowered).
- McKinsey 7S arrangement checked against a published figure. The figure I could read is the Wikimedia Commons file "McKinsey 7S framework.svg", the figure on the Wikipedia page "McKinsey 7S Framework" (rendered and read on 24 October 2026). It is a hexagon with a vertex at the top and bottom, the centre reading "Superordinate Goals (Shared Values)", and clockwise from the top: Strategy, Structure, Systems, Staff, Style, Skills. Round 1 had a flat-topped hexagon with Skills, Style and Staff in a different order; it is now the published one. Limits: this is a redrawing, not the 1980 article's own figure (Waterman, Peters and Phillips, "Structure Is Not Organization", Business Horizons, June 1980, which I could not retrieve; the image on tompeters.com returned 404). The hard (Strategy, Structure, Systems) and soft (Skills, Style, Staff, Shared Values) grouping is from Tom Peters's own history of the model (tompeters.com, "A Brief History of the 7-S Model"). The figure itself does not mark hard and soft.
- Credit lines: I have read no licence text, so every licence claim is removed (BMC, Lean, Value Proposition "CC BY-SA", Wardley "CC BY-SA 4.0"). Lines now name author and work only. If you want licences back, someone needs to read the licence pages.
- help-and-overlays-v1 on every canvas box: question visible, empty state with action, tooltips on icon-only buttons, hover card per note, "i" popover with an example (all tested).

## Contrast (4.5:1 on tinted surfaces)
Method: `scripts/contrast_check.py <server>` loads every page in light and dark at 1440, composes each text element's background layer by layer the way the browser paints it, and computes WCAG contrast. A text counts as "tinted" when a layer between it and the page is partly transparent or it sits in a ramp chip. Minimum ratio per page (all tinted texts on the page, both themes together counted in the first column):

| Page | tinted texts | Brand light | Brand dark | Neutral light | Neutral dark |
|---|---|---|---|---|---|
| canvas/ansoff-matrix | 74 | 4.62 | 7.26 | 4.62 | 7.26 |
| canvas/balanced-scorecard | 176 | 4.74 | 6.94 | 4.74 | 6.94 |
| canvas/blue-ocean | 94 | 4.74 | 6.94 | 4.74 | 6.94 |
| canvas/business-model-canvas | 154 | 7.09 | 7.84 | 7.02 | 7.45 |
| canvas/empathy-map | 106 | 7.18 | 7.62 | 7.12 | 7.45 |
| canvas/lean-canvas | 170 | 4.74 | 6.94 | 4.74 | 6.94 |
| canvas/mckinsey-7s | 112 | 7.09 | 7.84 | 7.02 | 7.45 |
| canvas/okr | 274 | 4.74 | 6.66 | 4.74 | 6.94 |
| canvas/pestle-analysis | 92 | 7.18 | 7.94 | 7.57 | 7.45 |
| canvas/porters-five-forces | 76 | 7.18 | 7.62 | 7.12 | 7.45 |
| canvas/product-vision-board | 74 | 7.09 | 7.84 | 7.02 | 7.45 |
| canvas/swot-analysis | 86 | 4.62 | 7.26 | 4.62 | 7.26 |
| canvas/value-proposition-canvas | 98 | 4.62 | 7.26 | 4.62 | 7.26 |
| canvas/wardley-mapping | 56 | 4.62 | 7.26 | 4.62 | 7.26 |
| capability/applications-by-capability | 142 | 5.22 | 4.53 | 2.37 | 3.57 |
| capability/capability-dialogs | 5 | - | 15.43 | - | 15.43 |
| capability/capability-map | 143 | 5.22 | 4.53 | 2.37 | 3.31 |
| capability/capability-planning | 207 | 5.22 | 4.53 | 2.37 | 3.57 |
| capability/capability-tree | 124 | 5.22 | 4.53 | 2.37 | 3.57 |
Findings:
- **First measurement failed, then was fixed.** With the question and zone label in `text-muted-foreground` on a 10% tint, light mode measured 3.98 to 4.26. Muted-foreground is 4.7:1 on plain white, so a tint of more than about 4% under it cannot reach 4.5. The question and zone label are now `text-foreground/70` (a token at 70 percent), which keeps them visibly muted and puts the lowest band text at 7.09 (light) and 6.66 (dark). R16 says "the question in muted text": it is muted in appearance, not in token.
- Brand tokens: lowest figure 4.53, the dark step-4 chip ("Managed") with `text-primary-foreground` on `bg-primary/80`. Light chips: step 1 to 4 `text-foreground` (14.62, 10.82, 7.79, 5.24 from `capability_ramp.py`), step 5 `text-primary-foreground` 5.93.
- **Neutral library tokens fail on ramp chips** (light 2.37, dark 3.31 to 3.57 on steps 3 and 4). The neutral primary is near black, so the step that needs light text on neutral needs dark text on the brand blue, and one class cannot serve both. I optimised for the brand tokens, which are Entelim's. A host app that uses the neutral theme gets chips under 4.5 at steps 3 and 4. Fixing it needs per-token-set text classes or a contrast-aware colour.
- The shadcn destructive Badge and Button recipes (`bg-destructive/10 text-destructive`) measure 3.97 in light mode (priority "Critical" on planning, "Delete" on dialogs). That is the upstream recipe, which you told me to keep; the script lists them apart and does not count them.
- Chip colours were checked through the ramp model (`scripts/capability_ramp.py`) and through browser pixels; the dark step 4 uses 80 instead of 76 because 76 gives 4.37.

## Fork comparison
How the fork was rendered: it is a Next.js app with a database, so I did not run it. I bundled its own React components (`components/canvas/*.tsx`, `components/capability-map/capability-map-viewer.tsx`) with esbuild, rendered them with `react-dom/server` and styled them with the fork's own `globals.css` through Tailwind (work directory `/tmp/forkrender`, outside the repo; `scripts/fork_side_by_side.py` takes the rendered pages). The fork's canvases are text areas, so each field holds our Northwind notes joined by line breaks; initial state only (nothing hovered or expanded). Only the capability **map** was compared; the tree, applications and planning fork components were not rendered, so those three pages have no fork screenshot (their right half would be the token version beside the map). Screenshots show the first 5200 pixels.

**Token version at least as clear as the fork**
- *Dark mode, everywhere.* The fork's cards are light fills with white-on-grey text in dark mode (Business Model Canvas: note text roughly 1.5 to 2:1 on grey-lilac). The token version holds 6.9 to 7.9:1 in dark.
- *Capability map, colour meaning.* The fork's red, orange, amber, lime and green fills make the value a colour with a small "M: 3/5" in a faded white pill. The chip carries the level in words, the legend sits above, and the heat switch is a labelled ToggleGroup. The fork's Heat Map Select showed empty in the render.
- *Notes.* One card per note, with a hover card, against a text area (BMC, Lean, Vision Board and others).
- *Sections tell apart in both themes* by a band with the zone name in text and an icon, not by hue alone.
- *Colour-blind reading.* The fork's red-to-green series is the classic failure; the ramp is one hue in five steps, 0.0896 apart at worst.

**Where the token version is not as clear as the fork, and why**
- *Light mode, section hue strength.* The fork's bands are strong pastel fills; the token bands are 10% tints with a 30% rule, paler by design (R16 forbids saturated fills behind body text). The groups are still easy to tell apart, but the Business Model Canvas tints (chart-3 green, chart-1 blue, chart-2 orange, chart-5 plum) are less vivid than the fork's.
- *Dark mode tint is faint.* 10% of a chart token over the dark card is a small step; zones are told apart mainly by the zone label and the rule. Raising to 15% would cost contrast on the muted text I have already moved to foreground/70.
- *Heat at a glance.* The fork floods a whole card with the heat colour, so a map reads like a heat map from across the room. The token version colours a chip only; this is the owner's rule (no solid saturated card fills). The map reads as a list of cards with chips, so a quick scan for "where are the weak ones" is slower. Counting the step in the legend and the chip text is the compensation.
- *Page length.* All sub-capabilities of level-0 groups open by default are cards, so the map is 4609 px tall at 1440 against about 1900 for the fork (which starts collapsed).
- *Four canvases whose fork is a four-field text form* (Balanced Scorecard, OKR, Blue Ocean, Wardley) are not like for like: the fork shows four boxes of text, the token versions are the published forms.
- The fork uses its own fonts' weights, which the render lacks (lighter titles); I did not equalise them.

## Not done, or less than asked
- **Wardley Map**: it is a graph, not boxes, so there are no note cards, bands or count Badge; components are buttons with a Sheet each. Not tinted.
- **Balanced Scorecard**: the four perspectives get the band, icon, question, count, "i" popover and tint, but their entries stay as Table rows (four fields each: objective, measure, target, initiative); one note card per entry would lose the fields. Not editable (as in round 1).
- **OKR**: the objective card gets the band (count of key results, "i", tint); key results stay as rows with Progress, score and status. Not editable.
- **Blue Ocean**: the four actions are note cards with bands; the chart card is unchanged. Not editable.
- **Hover card content is thin.** Type, box and canvas are real. Owner and last change cannot be real: a plain entry is a line of text, not a linked model element. The card says so ("Not assigned. Link the entry to a model element to set one."). There is no element page to link to, so I put no link.
- Hover card on a note whose trigger is also the control that opens the edit Sheet: clicking the text opens the Sheet for its box. I did not stack the hover card over a Sheet.
- The "i" example is the first two notes of the Northwind seed, not an authored example per box; the guidance text is authored (65 boxes in `_boxes.json`).
- The 390 px screenshots show the page as the phone sees it (canvases scroll sideways inside their region); the fork stacks. I looked at the Business Model Canvas 1440 dark side-by-side, and the capability map and popover and hover card in a browser. I did **not** inspect the other 58 screenshots one by one.
- No empty-state screenshot: the example data fills every box; it is covered by `test_an_empty_box_says_what_is_missing_and_offers_an_action_and_a_full_box_hides_it`.

## Tests
New: `tests/test_canvas_r16.py` (per canvas: one note card and one hover card per entry, band tint and icon and question and count and popover example and tooltips, empty state, banned words, BMC zones, capability card, group tints, chip text colours). Changed: `test_canvases.py`, `test_canvases_browser.py`, `test_canvas_blue_ocean.py` (note text is read from `[data-note-text]`; a marker now appears in the note card, its hover card and the list), `test_capability_map.py` (chip selector, toggle button by id), `test_capability_ramp.py` (steps).

Full suite (`python -m pytest -q --continue-on-collection-errors`, 36 minutes): **869 passed, 12 skipped, 1 failed, 4 errors.** The failure is `test_shadcn_components.py::test_block_dom_matches_upstream[dashboard-01]` (a date-dependent chart tick); the errors are `ModuleNotFoundError: selenium` in `test_flash_messages`, `test_forms_browser`, `test_sidebar_browser`, `test_table_styling_browser`. All five are identical to round 1 and to the base commit. Playwright browser tests for the canvases and the capability map are inside the 869.

Reproduce:
```
python scripts/contrast_check.py http://127.0.0.1:<port>            # add --neutral for the library tokens
python scripts/capability_ramp.py
python compliance/scripts/check_page.py http://127.0.0.1:<port>/examples/canvas/<slug> --nearest dashboard-01 --browser
python compliance/scripts/check_ratchet.py
python scripts/fork_side_by_side.py http://127.0.0.1:<port> /tmp/forkrender shots/fbcanvas01b
```
