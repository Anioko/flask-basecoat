# REPORT: capability map and tree open collapsed (fbcanvas01c)

Branch `feat/canvases-capability-map`, on top of 24590ba. Nothing pushed.

## What changed
- `capability_map/capability-map.html` and `capability-tree.html`: every capability's toggle starts `aria-expanded="false"` and every `data-cap-children` container starts `hidden`. Before, level-0 capabilities started open. The first screen now shows each top-level capability and its maturity chip.
- No JS change. `capability-map.js` already reads the initial state from `aria-expanded`, and the heat switch only touches chips, words and legends, so open or closed state survives it. "Expand all", "Collapse all" and each capability's own "Show n sub-capabilities" button work as before.
- The same collapsed default applies to the tree and to any page that uses these two macros.

## Tests
- New `test_browser_opens_collapsed_and_expand_all_opens_every_capability` (map and tree): all toggles are `false` and no children are visible on load; top-level chips are visible; one capability's button opens only its own subs; a heat switch to Investment and back keeps it open; "Expand all" opens every capability; "Collapse all" closes them.
- `test_browser_keyboard_opens_detail_and_toggles_a_tile` needed a change: its target (a level-2 capability) now sits under a collapsed parent, so the test clicks "Expand all" first.
- `tests/test_capability_map.py`: 34 passed. I did not re-run the full suite; the change is two templates, so I ran only the capability tests.
- `check_page --browser` on a live server: `SHADCN COMPOSED` on all 19 pages (14 canvases, 5 capability). `check_ratchet`: 426/426 files clean.

## Screenshots (`shots/fbcanvas01c/`)
`capability-map-{1440,390}-{light,dark}.png`, taken with `?brand=entelim`, plus `capability-map-1440-light-expanded.png` after "Expand all". I viewed the 1440 light image (collapsed, chips and "Show n sub-capabilities" visible). I did not open the other four by eye.

## Not done
- Contrast was not re-measured. Collapsing hides sub-capability chips, but the chip classes are unchanged.
