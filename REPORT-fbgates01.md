# REPORT-fbgates01

Branch `feat/page-check-gates` (cut from `feat/shadcn-100-compliance`). Nothing pushed. Commits: toast fix, `load_spec` chart id (own commit), gates.

## 0. The failing flash test
**Cause:** a page defect. Tailwind v4 emits `group-hover:` inside `@media (hover:hover)`. Headless Chrome under Selenium reports `hover:none`, so the toast close button (`opacity-0 group-hover/toast:opacity-100`) stayed invisible while hovered; `is_displayed()` was false. Touch and keyboard users had the same problem. **Fix:** `focus-visible:opacity-100 [@media(hover:none)]:opacity-100` in `toast.js`, rebuilt JS and CSS. The flash tests also used a hard-coded `localhost:5100`; they now use the live server's address, and `BASECOAT_TEST_PORT` overrides the port (worktrees collide on 5100).
**Not verified:** I could not read the CI logs (no `gh`). `requirements-dev.txt` and the workflow do not install selenium, so check how CI runs these files.
**Suite result:** see section 5 (one unrelated pre-existing failure).

## 1. How each check runs
All are flags of `python compliance/scripts/check_page.py <page> ...`; `--gates` runs them all; `--tier A|B|C`; `--survey out.md` runs everything on the library's pages. Details: `AGENTS.md` and `docs/PAGE-GATES.md`.

| Gate | Command | Notes |
|---|---|---|
| A2 | `--nearest X --structure --tier A` | tree of `tag[data-slot]`; text, attributes and icon internals dropped; consecutive identical siblings collapsed; charts and the sidebar header are leaves. Percent = matched nodes / larger tree. Prints the first differing node. Tier B/C: frame must be 100% (B2) |
| A5 | `--pixels --tier A` | text runs, chart containers, avatars, images painted grey; 1440 and 390, light and dark; a pixel differs above 12/255. Tier A 0.5% of page; B/C 2% of the frame (B8). Compared with the neutral golden (no branded golden exists yet) |
| B9 | `--charts [--rendered]` | spec must carry `"chart": "<pinned id>"` (`load_spec` now sets it); family (chart + series components), series <= original and <= 5, colour tokens limited to chart-1..5, muted-foreground and what the pinned chart itself carries (criteria 1.1c) |
| R9 | `--a11y [--departures f.json]` | axe, WCAG 2.2 AA, 4 configurations. Serious/critical fail unless a departure with rule, WCAG criterion and reason is recorded; moderate/minor only beyond the golden's count |
| C1-C5 | `--forms [--form c4]` | per marked region; C1 plus R15 on every page |
| help | `--help-text` | placeholders, icon-only buttons (name + Tooltip), native `title`, R16 |

**Assumptions to confirm:** the library has no Tier C macros, so the slot names (`diagram`, `diagram-element`, `timeline-bar` ...) are my contract (table in `docs/PAGE-GATES.md`). C3 accepts `--x`/`--w` only (criteria 1.5 also allows grid classes and SVG attributes). R16 detects an ordered measure as two or more opacity steps (20-100) of one chart token in one place, or an element inside `data-measure`. "Icon-only" excludes comboboxes. Not covered: the C4 Kanban board, the ArchiMate relationship validity table, A3/A4/A6/A8.
**Test fixtures:** `tests/test_check_page_gates.py` has a passing and a broken fixture per gate, including a mermaid/cytoscape/react-flow second-engine fixture for R15.

## 2. Result on the 27 blocks (each against its own golden, Tier A)
| gate | pass | fail | n/a |
|---|---|---|---|
| A2 | 27 | 0 | 0 |
| A5 | 26 | 1 | 0 |
| B9 | 1 | 0 | 26 (no chart) |
| R9 | 13 | 14 | 0 |
| forms | 27 | 0 | 0 |
| placeholders | 27 | 0 | 0 |
| icon-buttons | 9 | 18 | 0 |
| native-titles | 16 | 11 | 0 |
| R16 | 27 | 0 | 0 |

- **A5 fails:** sidebar-09 (1.49% at 1440, light and dark; 390 is 0%).
- **R9 fails (14):** dashboard-01, login-03, login-04, sidebar-05, 07, 08, 09, 10, 11, 12, 15, 16, signup-03, signup-04. All are findings the shadcn original also has (colour-contrast, button-name, list/listitem, target-size, label-content-name-mismatch); R9 fails them by design until fixed or recorded as departures. None is recorded yet.
- **icon-buttons fails (18):** dashboard-01, login-04, sidebar-01, sidebar-02, sidebar-03, sidebar-04, sidebar-05, sidebar-06, sidebar-07, sidebar-08, sidebar-09, sidebar-10, sidebar-11, sidebar-12, sidebar-14, sidebar-15, sidebar-16, signup-04. The originals' icon buttons (sidebar trigger, row menus) carry no Tooltip.
- **native-titles fails (11):** sidebar-01, sidebar-02, sidebar-03, sidebar-05, sidebar-06, sidebar-07, sidebar-10, sidebar-11, sidebar-12, sidebar-14, sidebar-15 (`SidebarRail` has `title="Toggle Sidebar"`).
Full table: section 6.

## 3. Result on the example pages (56)
| gate | pass | fail | n/a |
|---|---|---|---|
| A2 | 1 | 0 | 55 (no original named) |
| A5 | 0 | 1 | 55 |
| B9 | 0 | 9 | 47 |
| R9 | 19 | 37 | 0 |
| forms | 56 | 0 | 0 |
| placeholders | 56 | 0 | 0 |
| icon-buttons | 23 | 33 | 0 |
| native-titles | 47 | 9 | 0 |
| R16 | 56 | 0 | 0 |

- **reference/portfolio** (the only page naming an original): A2 passes the frame (whole page 76.77% of dashboard-01's tree); **fails B9** (chart coloured `var(--primary)`, not chart-1/2); **fails A5/B8** (2.28% at 1440 against the 2% limit, 35.2% at 390); fails R9 and icon-buttons. I did not change the page or the checks.
- **B9 fails (9):** reference/portfolio, dashboards/analytics, dashboards/insights, dashboards/marketing, dashboards/overview, dashboards/pipeline, dashboards/sales, admin-dashboard, payment-admin-dashboard. The six dashboards and the ported admin screens draw charts through their own `chart` macro, with no pinned chart id.
- **R9:** most common: colour-contrast (72 findings across configurations), label-content-name-mismatch, button-name, aria-required-children, scrollable-region-focusable.
- Placeholders, forms (no marked regions exist, R15 clean) and R16 pass everywhere. No example uses a Tier C form yet.

## 4. Pages that now fail
Every FAIL in sections 2 and 3, for the reasons stated. No check was loosened. Two heuristics were tightened after false positives in the first survey (data-step on sliders, tints of different tokens counted as a ramp).

## 5. Full suite
Run in a scratch venv with selenium (`BASECOAT_TEST_PORT=5173`), twice in a row, on the final commit:

- run 1: 727 passed, 1 failed; run 2: 727 passed, 1 failed.
- The one failure, `tests/test_shadcn_components.py::test_block_dom_matches_upstream[dashboard-01]`, is **not green and not mine**: it also fails on the base commit `8863c9f` (checked in a throwaway worktree) and without my `load_spec` change. The chart's tick text and x positions differ from the golden (for example 'May 16' against 'May 22', x 524 against 512.5), which looks like a chart-width or date effect of this machine. I did not change it or the golden. So "green twice in a row" is **not met** here; the suite is green apart from that one test. Please see whether it fails in your CI.
- An earlier run also failed 12 `test_forms_browser` tests, because that file hard-coded `localhost:5100` and my port override exposed it. It now uses the live server address (own commit).

## 6. Raw tables
Per-page tables are in the survey output (`check_page.py --survey`); re-run to regenerate (about 8 minutes per group).
