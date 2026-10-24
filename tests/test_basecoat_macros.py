import unittest
from flask import Flask, render_template_string
from flask_basecoat import Basecoat


class BasecoatMacrosTestCase(unittest.TestCase):
    """
    Tests for basecoat macros. Updated for shadcn-parity components.

    Note: These macros were replaced with shadcn-parity versions that use
    different signatures (content= instead of text=, low-level building blocks
    instead of high-level convenience parameters). See test_shadcn_class_parity.py
    for comprehensive class parity tests.
    """

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
        # Reason: shadcn button uses content= instead of text=, classes are shadcn not btn-*
        tmpl = "{% from 'basecoat/button.html' import button %}{{ button(content='Click Me') }}"
        rendered = render_template_string(tmpl)
        self.assertIn('inline-flex items-center justify-center', rendered)
        self.assertIn('Click Me', rendered)

    def test_button_variants(self):
        # Reason: shadcn button variant classes are bg-* not btn-*
        for variant in ['destructive', 'outline', 'secondary', 'ghost', 'link']:
            tmpl = f"{{% from 'basecoat/button.html' import button %}}{{{{ button(content='V', variant='{variant}') }}}}"
            rendered = render_template_string(tmpl)
            # Just verify it renders without error - variant styles are tested in parity tests
            self.assertIn('V', rendered)

    @unittest.skip("Reason: shadcn button doesn't have href/as_child params - caller must wrap in <a> tag")
    def test_button_as_link(self):
        pass

    @unittest.skip("Reason: shadcn button doesn't have built-in loading state - handled by caller")
    def test_button_loading(self):
        pass

    def test_badge_variants(self):
        # Reason: shadcn badge uses content= instead of text=, classes are border/bg-* not badge-*
        tmpl = "{% from 'basecoat/badge.html' import badge %}{{ badge(content='Live', variant='secondary') }}"
        rendered = render_template_string(tmpl)
        self.assertIn('inline-flex items-center', rendered)
        self.assertIn('Live', rendered)

    @unittest.skip("Reason: shadcn card is low-level building block, no title/description params - caller builds structure")
    def test_card_structure(self):
        pass

    def test_empty_state(self):
        # Reason: empty_state is legacy component, not replaced by shadcn
        tmpl = "{% from 'basecoat/empty_state.html' import empty_state %}{{ empty_state(title='Nothing Here', cta_text='Create First', cta_href='/new') }}"
        rendered = render_template_string(tmpl)
        self.assertIn('Nothing Here', rendered)
        self.assertIn('Create First', rendered)
        self.assertIn('href="/new"', rendered)

    @unittest.skip("Reason: shadcn table is low-level building block, no columns/rows params - caller builds structure with table_header/table_row/table_cell")
    def test_table_with_rows(self):
        pass

    def test_table_with_caller(self):
        # Reason: shadcn table takes content= not caller
        tmpl = """
        {% from 'basecoat/table.html' import table %}
        {{ table(content='<thead><tr><th>Custom Header</th></tr></thead><tbody><tr><td>Custom Cell</td></tr></tbody>') }}
        """
        rendered = render_template_string(tmpl)
        self.assertIn('Custom Header', rendered)
        self.assertIn('Custom Cell', rendered)
        self.assertIn('<table', rendered)

    @unittest.skip("Reason: shadcn table doesn't handle empty states - caller must implement")
    def test_table_empty_state_fallback(self):
        pass

    @unittest.skip("Reason: shadcn dialog is low-level building block, no id/title/trigger_text params - caller builds with dialog_overlay/dialog_content/dialog_header/dialog_title")
    def test_dialog_modal(self):
        pass

    @unittest.skip("Reason: shadcn dropdown-menu is low-level building block, no trigger_text/items params - caller builds with dropdown_menu_content/dropdown_menu_item")
    def test_dropdown_menu(self):
        pass

    @unittest.skip("Reason: shadcn tabs is low-level building block, no tabs_list/default_tab params - caller builds with tabs_list/tabs_trigger/tabs_content")
    def test_tabs_structure(self):
        pass

    def test_skeleton_loading(self):
        # Reason: shadcn skeleton is minimal, no skeleton_table helper
        tmpl = "{% from 'basecoat/skeleton.html' import skeleton %}{{ skeleton(class='h-4 w-20') }}"
        rendered = render_template_string(tmpl)
        self.assertIn('animate-pulse', rendered)


if __name__ == '__main__':
    unittest.main()
