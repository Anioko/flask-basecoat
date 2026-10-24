# fbsidebar07: sidebar-07 collapses to a 3rem icon rail

Branch `fix/sidebar-07-icon-rail`. Not pushed.

## Cause
`sidebar-07.html` rendered `ui.sidebar(variant='sidebar')`. Upstream is `<Sidebar collapsible="icon">`. The `collapsible` argument was
also swallowed by the slot recipe, so it never reached the DOM, and `sidebar.js` (which reads `data-collapsible-mode`) fell back to
`offcanvas`: collapsing slid the whole sidebar away.

## Commits
1. `feat(sidebar)`: `slots.py` emits `data-collapsible-mode` for `ui.sidebar(collapsible='icon'|'offcanvas')`. Additive, the only change to the macro layer. `collapsible='none'` is unchanged.
2. `feat(tooltip)`: `popover.js` (+ rebuilt `flask-basecoat.js`). A tooltip content marked `data-sidebar-tooltip` pairs with the menu button right before it and opens only when the sidebar is `collapsed` and the window is at least 768px wide (upstream `hidden={state !== "collapsed" || isMobile}`). No second tooltip or sidebar implementation.
3. `fix(sidebar-07)`: `collapsible='icon'`, and a `ui.tooltip_content(side='right')` after each of Playground, Models, Documentation and Settings (the four buttons upstream gives a `tooltip`), plus `tests/test_sidebar_icon_rail_browser.py`.
4. `fix(sidebar-09)`: the outer sidebar is `collapsible="icon"` upstream; it was the default.

## Other sidebar blocks against upstream `collapsible`
Upstream sets it on sidebar-07 (`icon`), sidebar-09 (outer `icon`, inner `none`), dashboard-01 (`offcanvas`, the default), and `none` on
09 inner, 10 actions, 13 dialog, 15 right. Every other sidebar-01..16 omits it (default `offcanvas`). Only 07 and 09 differed.
09's inner `none` sidebars were already correct.

## Evidence
- Browser test (Playwright, `tests/test_sidebar_icon_rail_browser.py`): expanded container 256px; collapsed 48px with `data-collapsible="icon"`,
  icons visible, labels clipped outside the button, group label opacity 0, header and footer buttons at most 48px; four tooltips shown on hover in
  the collapsed state with the right text; none shown when expanded; trigger reopens to 256px. 5 pass. With `test_sidebar`, `test_slots`, `test_check_page`: 76 pass.
- `check_page.py http://127.0.0.1:<port>/basecoat/blocks/sidebar-07 --nearest sidebar-07 --browser` and the same for `sidebar-09`: `SHADCN COMPOSED`, 100%.
- `check_ratchet.py`: 382/382 files clean.
- Screenshots in `shots/fbsidebar07/`: expanded and collapsed (Models tooltip showing) at 1440, drawer at 390, light and dark.

## Things to know
- Run against the bare test app (a path, not a URL), `--browser` reports off-token colours because that app serves no stylesheet. Use a URL on a real server.
- `tests/live_server.py` hardcodes port 5100 on this branch (R7's `TEST_SERVER_PORT` is not here yet). I ran with a local, uncommitted patch to avoid another worktree's port.
- The 390px drawer is about 203px wide, not upstream's 18rem (288px). It is as before this change and I left it alone.
- The "Projects" group is hidden when collapsed (`group-data-[collapsible=icon]:hidden`), as upstream.
- The Playwright test skips when playwright or Chromium is missing; other browser tests here use Selenium, which is not installed on this machine.
