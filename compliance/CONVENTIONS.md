# Component authoring contract (working notes for builders)

Every shadcn/ui registry component (65) and block (27) is ported to Jinja. The upstream React
source is pinned under `compliance/upstream/shadcn/radix` and the rendered upstream DOM for every
component example and block lives in `compliance/golden/out/*.html`. The golden DOM is the target:
our page for a component must produce the same `data-slot` elements, in the same order, with the
same class set and the same state attributes. `python compliance/scripts/check_dom.py <name>` says
whether it does.

## Files

| What | Where |
| --- | --- |
| Macros for component `<name>` | `flask_basecoat/templates/basecoat/<name>.html` (registry name, hyphens kept) |
| Component page (port of upstream `<name>-example.tsx`) | `flask_basecoat/templates/basecoat/pages/components/<name>.html` |
| Block page (port of upstream `blocks/<name>/page.tsx`) | `flask_basecoat/templates/basecoat/pages/blocks/<name>.html` |
| Behaviour script for `<name>` | `flask_basecoat/static/js/src/components/<name>.js` |
| Upstream source | `compliance/upstream/shadcn/radix/ui/<name>.tsx`, examples in `../examples/<name>-example.tsx` |
| Recipe (generated) | `compliance/recipes/<name>.json` |
| Golden DOM | `compliance/golden/out/<name>.html`, blocks in `compliance/golden/out/blocks/<name>.html` |

## Macro rules

1. One macro per exported upstream component, snake_case of the React name:
   `Button` → `button`, `CardHeader` → `card_header`, `DropdownMenuCheckboxItem` → `dropdown_menu_checkbox_item`.
2. Each macro renders exactly the element the React component renders (`div`, `button`, `span`, `a`,
   `nav`, `table`...), with `data-slot` and the full class string from the recipe JSON (`base_classes`,
   plus the cva `variants` classes for the chosen `variant`/`size`), then `class` from the caller appended.
   Class order does not matter; the set must match.
3. State attributes follow Radix exactly as the golden DOM shows them: `data-state="open|closed"`,
   `"active|inactive"`, `"checked|unchecked"`, `"on|off"`, `"expanded|collapsed"`; `aria-expanded`,
   `aria-selected`, `aria-checked`, `aria-pressed`, `aria-haspopup`, `role`, `data-orientation`,
   `data-variant`, `data-size`, `data-side`, `data-align`, `data-inset`, `data-disabled`, `disabled`.
4. Every macro accepts `class=''`, `id=none`, and `attrs={}` (extra attributes rendered verbatim through
   `attrs()` from `basecoat/_base.html`). Content comes from `caller()` when the macro is called with
   `{% call %}`, otherwise from a `text` argument. Macros never emit raw colours, palette classes or
   hex values; everything visual comes from the `cn-*` classes and tokens.
5. Icons: `{{ lucide('chevron-down', 'size-4') }}` renders the same SVG lucide-react emits
   (`class="lucide lucide-chevron-down size-4"`). Use the icon the upstream TSX names in its
   `lucide="..."` prop (PascalCase → kebab-case, drop `Icon`).
6. Interactive parts are static HTML plus `data-state`; behaviour lives in
   `flask_basecoat/static/js/src/components/<name>.js`, registered with
   `FlaskBasecoat.register('<name>', { init(root) {...} })` and selected by `data-slot`.
   Floating content (menus, popovers, tooltips, select lists) is marked `data-floating` and positioned
   by the core (`FlaskBasecoat.float(trigger, content, {side, align, sideOffset})`).
7. Pages import the barrel: `{% import 'basecoat/index.html' as ui %}` and the example wrapper
   `{% from 'basecoat/_example.html' import example, example_wrapper %}`. A page reproduces the
   upstream example section by section, same titles, same elements, same order.

## Self-check before reporting done

```
python compliance/scripts/check_dom.py <name>        # DOM parity with the golden markup
python compliance/scripts/check_recipes.py <name>    # every data-slot carries its recipe classes
python -m pytest tests/test_shadcn_components.py -k <name> -q
```

A component is done when all three pass. Report the actual output, not a summary of it.
