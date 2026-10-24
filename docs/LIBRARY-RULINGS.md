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
