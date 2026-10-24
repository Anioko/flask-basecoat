# Brief: port the floating parts of the popup components

React renders dialog, menu, popover, select and toast contents through portals only while open, so the
golden markup (`compliance/golden/out/<name>.html`) and the generated pages
(`flask_basecoat/templates/basecoat/pages/components/<name>.html`) contain the triggers but not the
contents. Your job is to add the contents, exactly as the upstream example defines them, so every
popup on the page opens with the right markup and the runtime (`flask_basecoat/static/js/flask-basecoat.js`)
can drive it.

Read first: `compliance/CONVENTIONS.md`, then the upstream example
`compliance/upstream/shadcn/radix/examples/<name>-example.tsx` and the component source
`compliance/upstream/shadcn/radix/ui/<name>.tsx`.

## How a popup is written

Every popup family has a wrapper macro that renders a `display: contents` div grouping the parts, and
one macro per upstream part (names are snake_case of the React component). Put the trigger and all
content parts inside the wrapper:

```jinja
{% call ui.dialog() %}
  {{ ui.dialog_trigger(text='Edit Profile', variant='outline') }}
  {{ ui.dialog_overlay() }}
  {% call ui.dialog_content() %}
    {% call ui.dialog_header() %}
      {{ ui.dialog_title(text='Edit profile') }}
      {{ ui.dialog_description(text="Make changes to your profile here. Click save when you're done.") }}
    {% endcall %}
    ... fields exactly as in the TSX, using ui.field, ui.field_label, ui.input ...
    {% call ui.dialog_footer() %}
      {{ ui.dialog_close(text='Cancel', variant='outline', size='default') }}
      {{ ui.button(text='Save changes', type='submit') }}
    {% endcall %}
    {% call ui.dialog_close(variant='ghost', size='icon-sm', class='cn-dialog-close') %}{{ lucide('x') }}<span class="sr-only">Close</span>{% endcall %}
  {% endcall %}
{% endcall %}
```

Upstream `DialogContent` and `SheetContent` render that X close button themselves (`showCloseButton`
defaults to true): a ghost icon-sm Button with class `cn-dialog-close` / `cn-sheet-close` containing the
`x` icon and a visually hidden "Close". Add it as the last child of every dialog/sheet content unless the
example passes `showCloseButton={false}`. Read the component TSX for every part: when a part is rendered
through `<Button asChild>` or `buttonVariants`, pass `variant`/`size`; when it carries a fixed class string
(`className="cn-..."` or `cn("cn-...", className)`), the macro already emits it.

The generated page already contains the trigger line for each example section (for instance
`{{ ui.dialog_trigger(text='Edit Profile', variant='outline') }}`). Wrap it in the family wrapper and add
the content after it. Keep everything else on the page untouched; the DOM parity check compares the
page against the golden markup and ignores closed popup contents, so the page must still pass.

Part macros per family (all exported from `basecoat/index.html` as `ui.<name>`):

- dialog: dialog, dialog_trigger, dialog_overlay, dialog_content, dialog_header, dialog_title, dialog_description, dialog_footer, dialog_close
- alert-dialog: alert_dialog, alert_dialog_trigger, alert_dialog_overlay, alert_dialog_content, alert_dialog_header, alert_dialog_media, alert_dialog_title, alert_dialog_description, alert_dialog_footer, alert_dialog_action, alert_dialog_cancel
- sheet: sheet, sheet_trigger, sheet_overlay, sheet_content (pass side='left|right|top|bottom'), sheet_header, sheet_title, sheet_description, sheet_footer, sheet_close
- drawer: drawer, drawer_trigger, drawer_overlay, drawer_content (side as above), drawer_header, drawer_title, drawer_description, drawer_footer, drawer_close
- popover: popover, popover_trigger, popover_anchor, popover_content (side, align), popover_header, popover_title, popover_description
- hover-card: hover_card, hover_card_trigger, hover_card_content (side, align)
- tooltip: tooltip, tooltip_trigger, tooltip_content (side, align). A tooltip trigger that is not a button: pass tag='span' or as_=none.
- dropdown-menu: dropdown_menu, dropdown_menu_trigger, dropdown_menu_content (align, side), dropdown_menu_group, dropdown_menu_label (inset=true), dropdown_menu_item (variant='destructive', inset=true, disabled=true, href=), dropdown_menu_checkbox_item (checked=true), dropdown_menu_radio_group, dropdown_menu_radio_item (checked=true, value=), dropdown_menu_separator, dropdown_menu_shortcut, dropdown_menu_sub (wrapper for a submenu), dropdown_menu_sub_trigger, dropdown_menu_sub_content
- context-menu: the same parts with the context_menu_ prefix; the trigger is a span (context_menu_trigger).
- menubar: menubar (the bar, already on the page), menubar_menu (wrapper for one menu), menubar_trigger, menubar_content, menubar_item, menubar_checkbox_item, menubar_radio_group, menubar_radio_item, menubar_label, menubar_separator, menubar_shortcut, menubar_sub, menubar_sub_trigger, menubar_sub_content
- select: select (wrapper), select_trigger, select_value, select_content, select_group, select_label, select_item (value=, checked=true, disabled=true), select_separator, select_scroll_up_button, select_scroll_down_button
- combobox: combobox (wrapper), combobox_trigger, combobox_value, combobox_clear, combobox_content, combobox_list, combobox_group, combobox_label, combobox_item (value=), combobox_empty, combobox_separator, combobox_chips, combobox_chip, combobox_chip_remove, combobox_chip_input
- command: command, command_input_wrapper, command_input, command_list, command_empty, command_group, command_item, command_separator, command_shortcut; command_dialog = a dialog whose content holds a command.
- sonner / toast: a `{{ ui.button(...) }}` trigger with `attrs={'data-fb-toast': 'Event has been created', 'data-fb-toast-description': '...'}` shows a toast through the runtime.

Checkbox and radio menu items render their indicator automatically (`dropdown_menu_checkbox_item_indicator`
is inserted by the macro when needed is not available; add it as the TSX does:
`{% call ui.dropdown_menu_checkbox_item(checked=true) %}{% call ui.dropdown_menu_checkbox_item_indicator() %}{{ lucide('check') }}{% endcall %}Status Bar{% endcall %}`).

Rules:
- Text, order, icons, variants, sizes and classes come from the TSX. Icons: `lucide="CheckIcon"` → `{{ lucide('check') }}`.
  Upstream class strings passed as `className` go to `class=`.
- Macros emit data-slot, recipe classes and state; never write `cn-*` classes or data-state by hand.
- Use `ui.field`, `ui.field_label`, `ui.input`, `ui.textarea`, `ui.checkbox`, `ui.switch`, `ui.tabs*`, `ui.kbd`,
  `ui.native_select*`, `ui.input_group*` for the forms inside dialogs, exactly as the example composes them.
- No raw `<button>`, `<input>`, `<select>`, `<textarea>`; no palette colours; no hex values.
- Do not edit macro files, `slots.py`, the generator scripts or the golden files. If a macro cannot express
  something the TSX needs, say so precisely in your final report instead of working around it.

## Verify before reporting

```
python compliance/scripts/check_dom.py <name>
python compliance/scripts/check_recipes.py <name>
python compliance/scripts/check_ratchet.py | grep pages/components/<name>
```

All three must be clean. Then open the page in headless Chromium and confirm each popup opens and closes:

```
python - <<'EOF'
from playwright.sync_api import sync_playwright
import threading; from werkzeug.serving import make_server
from flask_basecoat.testing import make_app
srv = make_server('127.0.0.1', 0, make_app(), threaded=True); threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as p:
    page = p.chromium.launch().new_page()
    page.goto(f'http://127.0.0.1:{srv.server_port}/basecoat/components/<name>')
    errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
    for t in page.query_selector_all('[data-slot="<name>-trigger"]'):
        t.click(); page.wait_for_timeout(100)
        print('open:', page.evaluate("document.querySelectorAll('[data-slot=\"<name>-content\"][data-state=open]').length"))
        page.keyboard.press('Escape'); page.wait_for_timeout(100)
    print('errors:', errors)
EOF
```

Report the real output of each command.
