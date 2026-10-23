import unittest
from flask import Flask, render_template_string
from flask_basecoat import Basecoat


class BasecoatMacrosTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'test-secret'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.basecoat = Basecoat(self.app)
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_button_default(self):
        tmpl = "{% from 'basecoat/button.html' import button %}{{ button(text='Click Me') }}"
        rendered = render_template_string(tmpl)
        self.assertIn('btn btn-primary', rendered)
        self.assertIn('Click Me', rendered)

    def test_button_variants(self):
        for variant in ['destructive', 'outline', 'secondary', 'ghost', 'link']:
            tmpl = f"{{% from 'basecoat/button.html' import button %}}{{{{ button(text='V', variant='{variant}') }}}}"
            rendered = render_template_string(tmpl)
            self.assertIn(f'btn-{variant}', rendered)

    def test_button_as_link(self):
        tmpl = "{% from 'basecoat/button.html' import button %}{{ button(text='Link', href='/target') }}"
        rendered = render_template_string(tmpl)
        self.assertIn('<a href="/target"', rendered)
        self.assertIn('btn btn-primary', rendered)

    def test_button_loading(self):
        tmpl = "{% from 'basecoat/button.html' import button %}{{ button(text='Saving', loading=true) }}"
        rendered = render_template_string(tmpl)
        self.assertIn('disabled', rendered)
        self.assertIn('animate-spin', rendered)

    def test_badge_variants(self):
        tmpl = "{% from 'basecoat/badge.html' import badge %}{{ badge(text='Live', variant='secondary') }}"
        rendered = render_template_string(tmpl)
        self.assertIn('badge badge-secondary', rendered)
        self.assertIn('Live', rendered)

    def test_card_structure(self):
        tmpl = """
        {% from 'basecoat/card.html' import card %}
        {% call card(title='Card Title', description='Card Desc') %}
            <p>Body Content</p>
        {% endcall %}
        """
        rendered = render_template_string(tmpl)
        self.assertIn('card', rendered)
        self.assertIn('Card Title', rendered)
        self.assertIn('Card Desc', rendered)
        self.assertIn('Body Content', rendered)

    def test_empty_state(self):
        tmpl = "{% from 'basecoat/empty_state.html' import empty_state %}{{ empty_state(title='Nothing Here', cta_text='Create First', cta_href='/new') }}"
        rendered = render_template_string(tmpl)
        self.assertIn('Nothing Here', rendered)
        self.assertIn('Create First', rendered)
        self.assertIn('href="/new"', rendered)

    def test_table_with_rows(self):
        tmpl = "{% from 'basecoat/table.html' import table %}{{ table(columns=['Name', 'Role'], rows=[['Alice', 'Admin']]) }}"
        rendered = render_template_string(tmpl)
        self.assertIn('Alice', rendered)
        self.assertIn('Admin', rendered)
        self.assertIn('<table class="table', rendered)

    def test_table_empty_state_fallback(self):
        tmpl = "{% from 'basecoat/table.html' import table %}{{ table(columns=['Name'], rows=[], empty_title='No Users') }}"
        rendered = render_template_string(tmpl)
        self.assertIn('No Users', rendered)
        self.assertNotIn('<table class="table', rendered)

    def test_dialog_modal(self):
        tmpl = """
        {% from 'basecoat/dialog.html' import dialog %}
        {% call dialog(id='modal-1', title='Warning', trigger_text='Launch') %}
            <p>Confirmation message</p>
        {% endcall %}
        """
        rendered = render_template_string(tmpl)
        self.assertIn('id="modal-1"', rendered)
        self.assertIn('showModal()', rendered)
        self.assertIn('Warning', rendered)
        self.assertIn('Confirmation message', rendered)

    def test_dropdown_menu(self):
        tmpl = """
        {% from 'basecoat/dropdown.html' import dropdown %}
        {{ dropdown(trigger_text='Menu', items=[{'text': 'Item 1', 'href': '/item1'}, {'divider': true}, {'text': 'Delete', 'variant': 'destructive'}]) }}
        """
        rendered = render_template_string(tmpl)
        self.assertIn('dropdown-menu', rendered)
        self.assertIn('data-popover', rendered)
        self.assertIn('role="menu"', rendered)
        self.assertIn('Item 1', rendered)
        self.assertIn('text-destructive', rendered)

    def test_tabs_structure(self):
        tmpl = """
        {% from 'basecoat/tabs.html' import tabs, tab_panel %}
        {% call tabs(tabs_list=[('tab1', 'First'), ('tab2', 'Second')], default_tab='tab1', id='test-tab') %}
            {% call tab_panel('tab1', default_tab='tab1', tabs_id='test-tab') %}Content 1{% endcall %}
            {% call tab_panel('tab2', default_tab='tab1', tabs_id='test-tab') %}Content 2{% endcall %}
        {% endcall %}
        """
        rendered = render_template_string(tmpl)
        self.assertIn('role="tablist"', rendered)
        self.assertIn('role="tab"', rendered)
        self.assertIn('role="tabpanel"', rendered)
        self.assertIn('Content 1', rendered)
        self.assertIn('Content 2', rendered)

    def test_skeleton_loading(self):
        tmpl = "{% from 'basecoat/skeleton.html' import skeleton, skeleton_table %}{{ skeleton(class='h-4 w-20') }}{{ skeleton_table(rows=2, cols=2) }}"
        rendered = render_template_string(tmpl)
        self.assertIn('animate-pulse', rendered)


if __name__ == '__main__':
    unittest.main()
