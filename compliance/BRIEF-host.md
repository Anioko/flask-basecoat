# Brief: migrate the demo application and example screens to the component macros

The package now ships one macro per shadcn/ui part (see `compliance/CONVENTIONS.md`, barrel
`flask_basecoat/templates/basecoat/index.html`, pages under `flask_basecoat/templates/basecoat/pages/`
for working examples of every macro). The demo application (`app/templates/**`) and the example screens
(`flask_basecoat/templates/examples/*.html`) still use the previous API (`bc.button(text=..., icon=...)`,
`btn btn-primary`, raw `<button>`/`<input>` tags, Tailwind palette colours, hex values, lucide `<i data-lucide>`
tags and a CDN Basecoat 0.3 stylesheet). Bring them to the same standard as the component pages.

## What "done" means for a template

1. It extends a layout whose `<html>` carries `class="style-vega"`, loads `{{ url_for('static', filename='styles/app.css') }}`
   (the demo app build) or `{{ basecoat.css() }}` (package build) and `{{ basecoat.js() }}`; nothing from a CDN,
   no `lucide@latest` script, no Basecoat 0.3 assets.
2. Every button, badge, card, input, select, textarea, checkbox, switch, radio, tabs, table, dialog, dropdown
   menu, tooltip, avatar, separator, alert, breadcrumb, pagination, sidebar, skeleton, progress, toast and
   empty state is a macro call from `{% import 'basecoat/index.html' as ui %}`. Raw `<button>`, `<input>`,
   `<select>`, `<textarea>` are not allowed (hidden inputs and CSRF fields are the only exception).
3. Colour comes from tokens only: `bg-background`, `text-muted-foreground`, `border-border`, `bg-primary`,
   `text-destructive`, `bg-muted`, `bg-accent`, `bg-card`, `text-card-foreground`, `bg-popover`, `ring-ring`,
   `bg-sidebar`, chart tokens. No `text-gray-600`, `bg-blue-500`, `#18181b`, `rgb(...)`.
4. Icons: `{{ lucide('name', 'size-4') }}` (kebab-case lucide names). No `<i data-lucide>`.
5. WTForms fields render through `ui.render_field(form.field)` / `ui.render_form(form)`.
6. Flash messages render through the toast runtime: in the layout, emit
   `{% for category, message in get_flashed_messages(with_categories=true) %}<template data-fb-flash data-variant="{{ 'error' if category in ('error','danger') else category }}">{{ message }}</template>{% endfor %}`.
7. Layout, copy and behaviour of the screen stay what they were; only the implementation changes.
   Where a screen reproduced a shadcn application screen, make it look like the upstream block
   (`flask_basecoat/templates/basecoat/pages/blocks/*.html` show the canonical login, signup, dashboard and sidebar layouts).

## Macro API in one minute

```jinja
{% import 'basecoat/index.html' as ui %}
{{ ui.button(text='Save', type='submit') }}                       variant: default|secondary|outline|ghost|destructive|link; size: default|xs|sm|lg|icon|icon-xs|icon-sm|icon-lg
{% call ui.button(variant='outline', size='sm', href=url_for('main.index')) %}{{ lucide('arrow-left') }} Back{% endcall %}
{{ ui.badge(text='Live', variant='secondary') }}
{% call ui.card(class='w-full max-w-sm') %}{% call ui.card_header() %}{{ ui.card_title(text='Title') }}{{ ui.card_description(text='Desc') }}{% endcall %}{% call ui.card_content() %}...{% endcall %}{% call ui.card_footer() %}...{% endcall %}{% endcall %}
{% call ui.field() %}{{ ui.field_label(text='Email', for_='email') }}{{ ui.input(id='email', name='email', type='email', placeholder='m@example.com') }}{{ ui.field_description(text='Help text') }}{% endcall %}
{{ ui.checkbox(id='terms', name='terms', checked=true) }} {{ ui.label(text='Accept', for_='terms') }}
{{ ui.switch(id='n', name='notifications') }}
{% call ui.tabs() %}{% call ui.tabs_list() %}{{ ui.tabs_trigger(text='Overview', active=true, attrs={'data-value': 'overview'}) }}{{ ui.tabs_trigger(text='Reports', attrs={'data-value': 'reports'}) }}{% endcall %}{% call ui.tabs_content(active=true, attrs={'data-value': 'overview'}) %}...{% endcall %}{% call ui.tabs_content(attrs={'data-value': 'reports'}) %}...{% endcall %}{% endcall %}
{% call ui.table_container() %}{% call ui.table() %}{% call ui.table_header() %}{% call ui.table_row() %}{{ ui.table_head(text='Name') }}{% endcall %}{% endcall %}{% call ui.table_body() %}{% call ui.table_row() %}{{ ui.table_cell(text='Ada') }}{% endcall %}{% endcall %}{% endcall %}{% endcall %}
{% call ui.dropdown_menu() %}{% call ui.dropdown_menu_trigger(variant='ghost', size='icon') %}{{ lucide('ellipsis') }}{% endcall %}{% call ui.dropdown_menu_content(align='end') %}{{ ui.dropdown_menu_item(text='Edit') }}{{ ui.dropdown_menu_separator() }}{{ ui.dropdown_menu_item(text='Delete', variant='destructive') }}{% endcall %}{% endcall %}
{% call ui.dialog() %}{{ ui.dialog_trigger(text='Open', variant='outline') }}{{ ui.dialog_overlay() }}{% call ui.dialog_content() %}{% call ui.dialog_header() %}{{ ui.dialog_title(text='Title') }}{% endcall %}...{% call ui.dialog_close(variant='ghost', size='icon-sm', class='cn-dialog-close') %}{{ lucide('x') }}<span class="sr-only">Close</span>{% endcall %}{% endcall %}{% endcall %}
{% call ui.tooltip() %}{{ ui.tooltip_trigger(text='Hover', variant='outline') }}{{ ui.tooltip_content(text='Tip') }}{% endcall %}
{% call ui.avatar() %}{{ ui.avatar_image(src=url, alt='') }}{{ ui.avatar_fallback(text='AO') }}{% endcall %}
{{ ui.separator() }}  {{ ui.skeleton(class='h-4 w-32') }}  {{ ui.progress(value=60) }}
{% call ui.alert(variant='destructive') %}{{ lucide('circle-alert') }}{{ ui.alert_title(text='Error') }}{{ ui.alert_description(text='...') }}{% endcall %}
{% call ui.empty() %}{% call ui.empty_header() %}{% call ui.empty_media(variant='icon') %}{{ lucide('inbox') }}{% endcall %}{{ ui.empty_title(text='No items') }}{{ ui.empty_description(text='...') }}{% endcall %}{% endcall %}
```

Every macro takes `class`, `id`, `attrs={...}` and content through `text=` or `{% call %}`; state through
`open`, `active`, `checked`, `pressed`, `disabled`, `invalid`, `required`, `orientation`, `side`, `align`, `href`, `type`.
The sidebar family (`ui.sidebar_wrapper`, `ui.sidebar`, `ui.sidebar_header`, `ui.sidebar_content`, `ui.sidebar_group`,
`ui.sidebar_group_label`, `ui.sidebar_menu`, `ui.sidebar_menu_item`, `ui.sidebar_menu_button`, `ui.sidebar_inset`,
`ui.sidebar_trigger`, `ui.sidebar_footer`, `ui.sidebar_rail`) is shown in `pages/blocks/sidebar-07.html`.

## Verify before reporting

```
python compliance/scripts/check_ratchet.py                      # must list none of your files
python compliance/scripts/check_recipes.py --url /path/of/page  # every data-slot element carries its recipe
python -m pytest tests -q -x                                     # the application still renders
```

Do not edit anything under `flask_basecoat/templates/basecoat/`, `flask_basecoat/slots.py`, `scripts/` or
`compliance/` and do not commit. Report the real output of the commands and list every file you changed.
