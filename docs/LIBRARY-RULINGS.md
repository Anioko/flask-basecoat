# Library rulings

The one log of decisions about how a shadcn component becomes a macro in this library. The class parity test (`tests/test_shadcn_class_parity.py`) is the definition of done; this log records what the parity test alone does not settle.

How it works:
- A builder who meets a gap (shadcn does something this library cannot copy as is, or two readings are possible) stops and states the gap in its report. It never settles the gap itself.
- The library reviewer rules on it here, one entry per ruling: the gap, the decision, the reason, and the test that enforces it.
- A gap that needs a product call, such as a component shadcn does not have and the product needs, goes to the product lead before it is ruled.
- A ruling is changed only by a later entry that names the earlier one.

## Rulings

### R1. The source of truth for every component (24 Oct 2026)
- **Gap:** shadcn's registry JSON and the component files sometimes differ (the label component's registry entry still carries an older variant).
- **Decision:** the authority is `components/ui/<name>.tsx` in the shadcn-examples fork the parity test reads; the registry JSON is not used.
- **Reason:** the component files are what shadcn renders today and what the hosted examples are built from.
- **Enforced by:** `tests/test_shadcn_class_parity.py`, which reads only the `.tsx` files.

### R2. A component is checked in every part a person sees, open and closed (24 Oct 2026)
- **Gap:** the select passed parity while its open panel rendered with no classes, because the test checked the trigger alone.
- **Decision:** a component's parity case asserts every part its `.tsx` file defines (for select: trigger, value, group, label, content, item, separator, scroll buttons). The open state of an overlay (select, dropdown, popover, dialog, sheet, tooltip) is part of the component, not an optional extra.
- **Reason:** the open panel is what a person sees and judges.
- **Enforced by:** the per-part cases in the parity test (select since PR 9); open-panel snapshots and a computed-look test per overlay component.

### R3. Radix-only classes may be dropped, by name, with the reason in the test (24 Oct 2026)
- **Gap:** shadcn's overlays carry utilities that only Radix sets: `data-[state=open|closed]:animate-*`, `data-[side=...]:translate-*`, and `--radix-*` size variables. This library's popovers are not Radix.
- **Decision:** those utilities, and only those, may be left out. Each one left out is named in the parity test with the reason. Every other class of the part stays, including background, border, radius, shadow, padding, size limits and overflow.
- **Reason:** keep shadcn's look without copying behaviour hooks nothing here triggers.
- **Enforced by:** the select parity case, which lists the dropped classes. Every later overlay component follows the same pattern.

### R4. Tests assert shadcn's rendered values, not the earlier Basecoat style (24 Oct 2026)
- **Gap:** the table-styling browser tests asserted Basecoat's old table (2px header border, 12px cell padding, a header background). Those tests failed on the canonical branch too.
- **Decision:** the tests assert shadcn's table: 1px row and header borders in a visible colour, `p-2` cells (8px), no header background, and a hover that changes the row background. Where a macro does not render what the `.tsx` file renders, the macro is fixed, not the test.
- **Reason:** this library ports shadcn verbatim; a test of another design system's look is a test of the wrong thing.
- **Enforced by:** `tests/test_table_styling_browser.py`, with the reason at the top of the file.

### R5. The stylesheet is generated, never hand-merged (24 Oct 2026)
- **Gap:** every component branch regenerates `app/static/styles/app.css`, so branches conflict in it, and a regeneration from too few templates dropped the table utilities.
- **Decision:** `app.css` is regenerated from the full template set (`npm install`, then `npm run build:css`) as the last step after merging the canonical branch. A conflict in it is resolved by regenerating, never by editing. A regenerated sheet that drops utilities another template uses is a defect.
- **Reason:** a generated file has one correct content for a given set of templates.
- **Enforced by:** `tests/test_table_styling_browser.py` and the parity test, run after every regeneration.

### R6. Components register through the gallery registry (24 Oct 2026)
- **Gap:** each component added its gallery and docs entries at the same place in three shared files, so every second component branch conflicted.
- **Decision:** once the registry is on the canonical branch, a component registers with one file under `flask_basecoat/gallery_entries/`. It never edits `gallery.py`, `gallery.html` or `component_detail.html` to add itself.
- **Reason:** independent components must merge in any order.
- **Enforced by:** the registry's identical-output test (the gallery index and docs pages render the same before and after migration).

### R7. Each test run uses its own port (24 Oct 2026)
- **Gap:** the live-server fixture bound port 5100, so two runs on one machine aborted each other with "Address already in use" and reported every browser test as an error.
- **Decision:** the port comes from `TEST_SERVER_PORT` (default 5100), and every builder and reviewer exports its own before every test run, including the parity test.
- **Reason:** a result produced while another run holds the port is not a result.
- **Enforced by:** `tests/live_server.py` (PR 6). A report whose suite errors with "Address already in use" is re-run, never accepted.

### R8. References are shadcn's own MIT sources (24 Oct 2026)
- **Gap:** third-party shadcn collections (for example paid dashboard-shell packs) offer layouts that look similar.
- **Decision:** the only references are shadcn's own component files and shadcn's own blocks (for the application shell, `sidebar.tsx` and the `dashboard-01` block). Third-party collections are not a reference.
- **Reason:** the target is shadcn itself; a third party's interpretation adds a second design system and often a licence question.
- **Enforced by:** the parity test reads only shadcn's files. The fidelity harness measures against shadcn's hosted examples and `https://ui.shadcn.com/view/new-york-v4/dashboard-01`.

### R9. Accessibility outranks verbatim for serious and critical findings (24 Oct 2026)
- **Gap:** gate X9 in criteria-v2 allows any accessibility finding the shadcn original already has. The accessibility standard forbids serious and critical findings outright. The ready-to-show gate (WCAG 2.2 AA, no serious failures) agrees with the standard.
- **Decision:** a serious or critical finding is fixed even when the original has it. The fix is recorded as a departure in the page's row: the original's finding, the change, and the WCAG criterion. Moderate and minor findings the original carries are allowed and listed in the conformance report.
- **Reason:** a buyer's procurement review judges the product against WCAG, not against shadcn.
- **Enforced by:** X9 reads "no serious or critical finding; no moderate or minor finding beyond the original's own". criteria-v3 carries the change.

### R10. Form control borders reach 3:1 (24 Oct 2026)
- **Gap:** shadcn's neutral theme draws input borders at oklch(0.922 0 0) on white: 1.26 to 1, measured. WCAG 2.2 criterion 1.4.11 asks 3 to 1 for the boundary that identifies a control. In light mode, the border is the only thing marking an empty input's edge.
- **Decision:** the `--input` token, used for the borders of input, select, textarea, checkbox, radio and switch, takes a value that reaches 3 to 1 against background and card in light and dark. In light mode that is oklch(0.669 0 0) or darker. The `--border` token for cards, tables and separators stays shadcn's, because those lines are decorative. The ui-designer sets the exact values and checks them by script.
- **Reason:** the same as R9.
- **Enforced by:** the token diff in the tier gate allows this one token change, and the contrast check measures it.

### R11. The font is the golden renders' font (24 Oct 2026)
- **Gap:** shadcn's pinned theme leaves `--font-sans` to the project. Entelim uses Inter today. The structure and pixel gates compare against golden renders.
- **Decision:** Entelim's `--font-sans` is the font the library's golden renders use, read from the golden pipeline when the canonical library lands.
- **Reason:** a different font fails every page's pixel gate on text alone.
- **Enforced by:** the token diff, and the pixel gate.

### R12. One board (24 Oct 2026)
- **Decision:** every board in Entelim is the one board component, built to Tier C4. Kibo UI's Kanban (MIT) supplies its structure. shadcn.io's public preview is the bar for behaviour only, with no code copied and nothing bought. A second board is a defect.
- **Amends R8:** where shadcn has no original for a pattern (a board, a combobox with custom actions), Kibo UI's MIT sources may supply its structure, built only from shadcn components. Its licence is recorded with the entry. Paid collections stay excluded.
- **Enforced by:** a reuse-register entry, and a ratchet counting drag-and-column markup outside the board component.

### R13. The content grid is shadcn's, named per page and checked (24 Oct 2026)
- **Gap:** criteria-v3 checks the frame (sidebar, inset, site header) exactly, and limits a page to 6 regions. It does not name how the regions are arranged inside the content area. Until a page's golden render exists (290 of 406), nothing stops a builder inventing its own arrangement and spacing. Those are the near-invisible lines the founder pointed to on shadcn's sidebar blocks.
- **Decision:** every signed-in page arranges its regions with one of four content grids, copied class for class from pinned originals, and its port-map row names which one:
  1. **G1, dashboard (dashboard-01):** `@container/main flex flex-1 flex-col gap-2`, then `flex flex-col gap-4 py-4 md:gap-6 md:py-6`. Rows sit in `px-4 lg:px-6`. A stat row uses `grid grid-cols-1 gap-4 @xl/main:grid-cols-2 @5xl/main:grid-cols-4`.
  2. **G2, three up and one full (sidebar blocks):** `flex flex-1 flex-col gap-4 p-4`, then `grid auto-rows-min gap-4 md:grid-cols-3`, then one `flex-1` region.
  3. **G3, single column (record detail, settings, form):** the G1 outer wrapper, then one column of Cards at `gap-4 md:gap-6`.
  4. **G4, Tier C form region:** the G1 outer wrapper, then the one marked form region at full width.
  The grey boxes in shadcn's blocks (`aspect-video rounded-xl bg-muted/50`) are placeholders, so a real region is a Card or a table card and never a grey box. Signed-in pages use G1's padding. G2 is used only where its three-up arrangement is the job.
- **Enforced by:** a new `grid` field in each page row. The tier gate checks the content wrapper's classes against the named grid on every page, now, without waiting for golden renders. Any other gap, padding or column class on a region wrapper fails.
- **Addition, 24 October (form grids and bento grids):**
  - **Fields side by side inside a form** use shadcn's own field grid from the pinned signup-03 and signup-04 forms: `grid grid-cols-2 gap-4`, or `grid grid-cols-3 gap-4` with `col-span-2`, inside a FieldGroup. Two short related fields share a row (first and last name; city and state; start and end date). Long or unrelated fields stay one per row. shadcn.io's field-grid example shows the same layout, and our source is the official one.
  - **Bento grids** (uneven tiles of different sizes, as on shadcndesign.com) are a landing-page device from an independent, mostly paid source. They are not used on signed-in pages, where G1 to G4 apply. On the public site, a feature section may use an uneven grid only from a free source whose licence the library owner has read and recorded. The paid blocks need the founder's decision on spend.

### R14. Patterns for the six jobs without one, the code block, and four unplaced capabilities (24 Oct 2026)
Each pattern is built only from pinned shadcn components. Its source is named and it enters the pattern register under the next number.
- **P32 Notification list.** A bell Button (ghost, icon) with a Badge count opens a Popover holding a list of Item rows (icon, title, time, unread dot) and a "Mark all read" link button. The source is the pinned dashboard-01 nav-user menu structure and the `item` component. The full history is a Tier B list page using P03. No toast stack and no custom drawer.
- **P33 Saved filters.** A DropdownMenu or Combobox of saved views next to the P02 filter bar, with "Save current view" opening a Dialog holding one Field. Applied filters show as Badge chips with a remove button. Built on P02 and Kibo's `combobox/custom-actions` group for parts. One saved-view control per list page.
- **P34 Schedule picker.** A Popover holding a Calendar, plus a Select for time and one for repeat (none, daily, weekly, monthly). Built from shadcn's date-picker composition (Popover plus Calendar). The value reads back in words ("Every Monday at 09:00") under the Field.
- **P35 Weights editor.** One Field row per criterion: a Label, a Slider (0 to 100, step 5), and the number shown with `tabular-nums`. A total row stays visible, and the save Button is disabled until the weights total 100, with an inline Field error otherwise. Built from the pinned `slider` and `field` components. Keyboard: arrow keys move by one step, and page up and down by 25.
- **P36 Compare two records.** One Table whose first column names each attribute and whose next two columns hold the two records' values. Differing rows are marked with a Badge "Differs", never by colour alone, and a Switch shows only differences. Built from the pinned `table`, `badge` and `switch` components. No side-by-side free-form cards.
- **ADM ring.** The TOGAF ADM cycle is Tier C1 (diagram canvas). It has its recognisable form: the preliminary phase, eight phases A to H in a ring around Requirements Management, with the current phase marked by label and outline. The form region is SVG drawn from tokens, and the accessible alternative is an ordered list of phases with status. It joins the C1 macro family. It is not a new tier.
- **Code block with copy.** Not new: shadcn's pinned registry has `code-block` (ui/code-block.tsx, with code-block-example.tsx). Use it, ported verbatim as a Tier A component, for the public API page and any code shown in the product.
- **Unplaced capabilities.** Service dependency mapping extends the model's application and service detail page and the impact page: a dependencies region using P03 and the C1 diagram, both reading the model's relationships. Service ownership and support model extends the same detail page: an owner and support region using P18 to link an owner, reading the one owner store. Initiative-to-objective traceability extends the initiative detail page with a P18 link and a traceability region. Human oversight specification extends the AI governance record page as a P10 sectioned form.
- **R14 addition, P35 shares variant.** When the weights are shares of something that need not be fully allocated (a team's share of time across technologies, for example), P35 runs in "at most 100" mode. Save is allowed at any total up to 100. The remainder is shown as its own row, "Unassigned", with its number, and a total above 100 is an inline Field error. The row names the mode: `P35-weights-editor` (exactly 100) or `P35-weights-editor:at-most` (up to 100).

### R15. One diagram engine (24 Oct 2026)
- **Decision:** Entelim has one ArchiMate drawing engine, the Composer. The library may carry ArchiMate parts only as the Composer's components: element shapes for all 60 types, notation, palette, relationship line styles and arrowheads as macros and tokens that the Composer renders with. It may not carry a second editor with its own model, layout or save path. BPMN process diagrams and database diagrams have no Entelim equivalent. Each may be a C1 component on the same engine's canvas (pan, zoom, select, connect), reading the one model store.
- **Reason:** two drawing engines for one model was a recorded defect in the readiness review of 20 September (owner: the lead, under the reuse rule).
- **Enforced by:** the C1 form check fails any diagram not rendered through the one engine, or any page carrying a second engine's script. The import brief for the diagram editors states this.

### R16. Colour carries meaning, from tokens only (24 Oct 2026)
- **Gap:** the redesigned capability map turned every heat-map card grey. The founder compared it with the original "fork" design (amber and lime fills, tinted section bands, icons) and found the fork clearer. The fork is right that colour should carry meaning, but its raw amber and lime break dark mode, the brand and colour-blind reading.
- **Decision:**
  - An ordered measure (maturity, importance, investment, risk level) is drawn with the ordered brand ramp, always with the value as text beside it and a legend.
  - Groups and zones (capability types, canvas zones) may carry a low-opacity tint of a chart token on their header band (`bg-chart-n/10`, `border-chart-n/30`).
  - Saturated fills behind body text are not allowed.
  - Canvas boxes show one note card per entry, never a block of bulleted text.
  - Body text keeps 4.5:1 on every tinted surface, in both themes.
- **Enforced by:**
  - the token check (no raw palette colours);
  - the Tier C form check (the value as text beside each colour, the legend present);
  - the contrast check on tinted surfaces.
