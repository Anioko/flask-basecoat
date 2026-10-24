"""Unit tests for the checkbox macro: every state renders the shadcn classes, ARIA and data attributes."""
import unittest

from bs4 import BeautifulSoup
from flask import Flask, render_template_string

from flask_basecoat import Basecoat

ROOT_CLASSES = (
    "peer border-input dark:bg-input/30 data-[state=checked]:bg-primary "
    "data-[state=checked]:text-primary-foreground dark:data-[state=checked]:bg-primary "
    "data-[state=checked]:border-primary focus-visible:border-ring focus-visible:ring-ring/50 "
    "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 "
    "aria-invalid:border-destructive size-4 shrink-0 rounded-[4px] border shadow-xs "
    "transition-shadow outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50"
).split()
INDICATOR_CLASSES = "flex items-center justify-center text-current transition-none".split()


class CheckboxMacroTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        Basecoat(self.app)
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def render(self, args='', caller=None):
        body = "{% from 'basecoat/checkbox.html' import checkbox %}"
        if caller is None:
            body += "{{ checkbox(" + args + ") }}"
        else:
            body += "{% call checkbox(" + args + ") %}" + caller + "{% endcall %}"
        return BeautifulSoup(render_template_string(body), 'html.parser')

    def root(self, soup):
        return soup.find(attrs={'data-slot': 'checkbox'})

    def test_default_has_shadcn_classes_and_slots(self):
        soup = self.render()
        root = self.root(soup)
        self.assertEqual(root.get('class'), ROOT_CLASSES)
        self.assertEqual(root['role'], 'checkbox')
        self.assertEqual(root['aria-checked'], 'false')
        self.assertEqual(root['data-state'], 'unchecked')
        self.assertEqual(soup.find(attrs={'data-slot': 'checkbox-indicator'}).get('class'), INDICATOR_CLASSES)
        self.assertIsNone(soup.find('svg'))

    def test_checked(self):
        root = self.root(self.render("checked=true"))
        self.assertEqual(root['aria-checked'], 'true')
        self.assertEqual(root['data-state'], 'checked')
        self.assertEqual(root.get('class'), ROOT_CLASSES)
        self.assertIsNotNone(root.find('svg'))

    def test_indeterminate(self):
        root = self.root(self.render("indeterminate=true"))
        self.assertEqual(root['aria-checked'], 'mixed')
        self.assertEqual(root['data-state'], 'indeterminate')
        self.assertIsNotNone(root.find('svg'))

    def test_disabled(self):
        root = self.root(self.render("disabled=true"))
        self.assertTrue(root.has_attr('disabled'))
        self.assertIn('disabled:opacity-50', root['class'])

    def test_invalid_and_required(self):
        root = self.root(self.render("invalid=true, required=true"))
        self.assertEqual(root['aria-invalid'], 'true')
        self.assertEqual(root['aria-required'], 'true')
        self.assertIn('aria-invalid:border-destructive', root['class'])

    def test_plain_has_no_optional_aria(self):
        root = self.root(self.render())
        for attr in ('aria-invalid', 'aria-required', 'disabled', 'aria-label'):
            self.assertFalse(root.has_attr(attr), attr)

    def test_id_aria_label_and_extra_class(self):
        root = self.root(self.render("id='c1', aria_label='Select all', class='mt-1'"))
        self.assertEqual(root['id'], 'c1')
        self.assertEqual(root['aria-label'], 'Select all')
        self.assertEqual(root.get('class'), ROOT_CLASSES + ['mt-1'])

    def test_name_renders_hidden_form_input(self):
        soup = self.render("name='terms', value='yes', checked=true, required=true")
        field = soup.find('input')
        self.assertEqual(field['name'], 'terms')
        self.assertEqual(field['value'], 'yes')
        self.assertTrue(field.has_attr('checked'))
        self.assertTrue(field.has_attr('required'))
        self.assertTrue(field.has_attr('hidden'))
        self.assertEqual(field['aria-hidden'], 'true')

    def test_no_name_no_form_input(self):
        self.assertIsNone(self.render().find('input'))

    def test_caller_slot_renders_beside_box(self):
        soup = self.render("id='c2'", caller="<label for='c2'>Accept</label>")
        field = soup.find(attrs={'data-slot': 'checkbox-field'})
        self.assertIsNotNone(field)
        self.assertEqual(field.find('label').text, 'Accept')
        self.assertIsNotNone(field.find(attrs={'data-slot': 'checkbox'}))

    def test_no_raw_colour_or_inline_style(self):
        html = str(self.render("checked=true, invalid=true"))
        self.assertNotIn('style=', html)
        self.assertNotRegex(html, r'#[0-9a-fA-F]{3,6}\b|rgb\(|\b(bg|text|border)-(white|black|red|blue|gray|slate)-?\d*\b')


if __name__ == '__main__':
    unittest.main()
