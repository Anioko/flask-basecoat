# Flask-Basecoat

The shadcn/ui design system for Flask and Jinja2. Every component in the shadcn/ui registry and every
block (sidebars, logins, signups, the dashboard) is a Jinja macro, styled by the upstream shadcn stylesheet
and driven by a small dependency-free runtime. Nothing is approximated: the package is built from a pinned
copy of the shadcn/ui sources and checked against them in a browser.

## What you get

- 65 components, 406 macros: Accordion to Tooltip, including Combobox, Command, Data Table, Date Picker,
  Input OTP, Sidebar, Resizable, Carousel, Chart, Sonner toasts, Field and Input Group.
- 27 blocks ported part for part: sidebar-01 to sidebar-16, login-01 to login-05, signup-01 to signup-05, dashboard-01.
- The upstream look, not a re-implementation: the shipped stylesheet is compiled from shadcn's own
  Tailwind v4 pipeline (the shadcn stylesheet, the Vega style pack and the neutral theme) with light and dark mode.
- Behaviour without React: dialogs, sheets, drawers, menus, popovers, tooltips, selects, comboboxes, command
  palettes, tabs, accordions, toggles, sliders, OTP inputs, carousels, resizable panels, the sidebar, toasts,
  calendars and charts work from static HTML with keyboard navigation, focus management and ARIA state.
- WTForms adapter: `ui.render_form(form)` and `ui.render_field(form.email)` render fields with server-side
  validation state the way shadcn's Field component does.
- A compliance harness that proves all of the above against the pinned upstream sources on every build.

## Install

```bash
pip install Flask-Basecoat
```

```python
from flask import Flask
from flask_basecoat import Basecoat

app = Flask(__name__)
Basecoat(app)
```

```html
<!doctype html>
<html lang="en" class="style-vega">
<head>
  {{ basecoat.css() }}
  {{ basecoat.js() }}
</head>
<body class="bg-background text-foreground">
  {% import 'basecoat/index.html' as ui %}
  {{ ui.button(text='Save changes') }}
</body>
</html>
```

Add `class="dark"` to `<html>` for dark mode. Any element with `data-theme-toggle` switches it.

## Using the macros

Every macro is one upstream part, named after the React component in snake_case. Content goes in `text=`
or a `{% call %}` block; `class`, `id` and `attrs={}` are always accepted; state is passed by name.

```jinja
{% import 'basecoat/index.html' as ui %}

{{ ui.button(text='Delete', variant='destructive', size='sm') }}
{% call ui.button(variant='outline', href=url_for('main.index')) %}{{ lucide('arrow-left') }} Back{% endcall %}

{% call ui.card(class='w-full max-w-sm') %}
  {% call ui.card_header() %}
    {{ ui.card_title(text='Login to your account') }}
    {{ ui.card_description(text='Enter your email below to login to your account') }}
  {% endcall %}
  {% call ui.card_content() %}
    {% call ui.field() %}
      {{ ui.field_label(text='Email', for_='email') }}
      {{ ui.input(id='email', type='email', placeholder='m@example.com', required=true) }}
    {% endcall %}
  {% endcall %}
{% endcall %}

{% call ui.dialog() %}
  {{ ui.dialog_trigger(text='Edit profile', variant='outline') }}
  {{ ui.dialog_overlay() }}
  {% call ui.dialog_content() %}
    {% call ui.dialog_header() %}
      {{ ui.dialog_title(text='Edit profile') }}
      {{ ui.dialog_description(text="Make changes to your profile here. Click save when you're done.") }}
    {% endcall %}
    {% call ui.dialog_footer() %}
      {{ ui.dialog_close(text='Cancel', variant='outline', size='default') }}
      {{ ui.button(text='Save changes', type='submit') }}
    {% endcall %}
    {% call ui.dialog_close(variant='ghost', size='icon-sm', class='cn-dialog-close') %}{{ lucide('x') }}<span class="sr-only">Close</span>{% endcall %}
  {% endcall %}
{% endcall %}

{% call ui.dropdown_menu() %}
  {{ ui.dropdown_menu_trigger(text='Open', variant='outline') }}
  {% call ui.dropdown_menu_content(align='end') %}
    {{ ui.dropdown_menu_label(text='My Account') }}
    {{ ui.dropdown_menu_separator() }}
    {{ ui.dropdown_menu_item(text='Profile') }}
    {{ ui.dropdown_menu_checkbox_item(text='Status bar', checked=true) }}
    {{ ui.dropdown_menu_item(text='Log out', variant='destructive') }}
  {% endcall %}
{% endcall %}

{% call ui.tabs() %}
  {% call ui.tabs_list() %}
    {{ ui.tabs_trigger(text='Account', active=true) }}
    {{ ui.tabs_trigger(text='Password') }}
  {% endcall %}
  {% call ui.tabs_content(active=true) %}...{% endcall %}
  {% call ui.tabs_content() %}...{% endcall %}
{% endcall %}

{{ ui.render_form(form, submit_text='Create account') }}
```

Icons: `{{ lucide('chevron-down', 'size-4') }}` renders the same SVG lucide-react emits.
Toasts: `FlaskBasecoat.toast.success('Saved')` in JavaScript, or `data-fb-toast="Saved"` on any element;
flashed messages become toasts through `<template data-fb-flash data-variant="success">...</template>`.

The gallery at `/basecoat/` (enabled in debug and testing, or with `BASECOAT_GALLERY_ENABLED = True`) shows
every component page and block, each a port of the upstream example. `/examples/` holds 27 application screens
built with the macros, and `/basecoat/gallery` the WTForms adapter with live validation.

## Building pages with an AI coding agent

`AGENTS.md` is the procedure for agents (and people) building new pages: pick the nearest shadcn original, reuse its
frame, lay rows out with the originals' recipes (`docs/LAYOUT.md`), write every part with a macro
(`docs/MACROS.md` lists them all), and prove the result with
`compliance/scripts/check_page.py`, which reports whether a page is composed only of shadcn parts inside the frame of
a shadcn original. `flask_basecoat/templates/examples/reference/portfolio.html` (served at
`/examples/reference/portfolio`) is a dashboard built that way. A Claude skill with the same steps is in
`skills/flask-basecoat/`.

## How compliance is proven

`compliance/upstream/` pins shadcn-ui/ui (commit e55b60b, 23 October 2026): the component sources, the
examples, the blocks, the Vega style pack and the neutral theme. `compliance/golden/` renders every upstream
example and block with React to static HTML, the reference DOM. From the same pinned sources:

- `compliance/scripts/extract_recipes.py` extracts each part's class recipe from the TSX; `scripts/gen_macros.py`
  turns them into macros backed by `flask_basecoat/slots.py`, which also applies tailwind-merge rules and the
  Radix state contract (`data-state`, `aria-*`, `role`, `data-orientation`).
- The shipped stylesheet is compiled from the upstream pipeline: Tailwind v4, tw-animate, shadcn's stylesheet,
  the theme mapping, the neutral tokens and the Vega style pack.

`python scripts/shadcn_compliance.py --browser` runs the checks and writes `compliance/REPORT.json`:

| Check | What it compares |
| --- | --- |
| coverage | every registry component and block has a macro file, a page and a barrel export |
| dom | our pages against the golden DOM: data-slot elements, order, class sets, state attributes |
| recipes | every rendered part carries exactly its upstream class recipe |
| tokens | the stylesheet's light and dark variables against the upstream neutral theme |
| styles | computed styles of every part in headless Chromium, light and dark, against the golden pages |
| a11y | axe-core on every page: no accessibility findings beyond upstream's own |
| runtime | pages load without script errors; popups, menus, tabs, toggles and sliders behave like Radix |
| ratchet | application templates contain no raw colours, raw form controls or legacy class names |
| tests | the pytest suite, including a parametrised test per component and block |

The GitHub Actions workflow in `.github/workflows/compliance.yml` runs the same checks on every push and
fails the build when generated files drift from the pinned sources.

## Development

```bash
npm install && (cd compliance/golden && npm install)
pip install -r requirements.txt -r requirements-dev.txt
python -m playwright install chromium

npm run golden          # render the upstream examples and blocks to compliance/golden/out
npm run build           # compile the demo stylesheet and the package stylesheet
python scripts/build_js.py
python scripts/shadcn_compliance.py --browser
python manage.py runserver
```

To take a new upstream version, update `compliance/upstream/PINS.json`, refresh the pinned sources, then run
`python compliance/scripts/gen_theme.py`, `npm run golden`, `python compliance/scripts/extract_recipes.py`,
`python scripts/gen_macros.py --force`, `python scripts/gen_pages.py --force` and the compliance run.

## License

MIT
