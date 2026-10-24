"""The WTForms adapter renders fields through the shadcn Field parts with server-side validation state."""
import unittest

from flask import Flask, render_template_string
from werkzeug.datastructures import MultiDict
from wtforms import Form, StringField, BooleanField, SelectField, validators

from flask_basecoat import Basecoat


class UserForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25), validators.InputRequired()])
    email = StringField('Email', [validators.Email(), validators.InputRequired()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('member', 'Member')])
    terms = BooleanField('I agree to the terms')


IMPORT = "{% import 'basecoat/index.html' as ui %}"


class WTFormsAdapterTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(SECRET_KEY='test', WTF_CSRF_ENABLED=False)
        Basecoat(self.app)
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def render(self, tmpl, **ctx):
        return render_template_string(IMPORT + tmpl, **ctx)

    def test_render_field_valid(self):
        form = UserForm(data={'username': 'octocat'})
        html = self.render("{{ ui.render_field(form.username) }}", form=form)
        self.assertIn('data-slot="field"', html)
        self.assertIn('data-slot="field-label"', html)
        self.assertIn('for="username"', html)
        self.assertIn('value="octocat"', html)
        self.assertIn('data-slot="input"', html)
        self.assertNotIn('aria-invalid', html)

    def test_render_field_with_validation_errors(self):
        form = UserForm(MultiDict({'username': 'a', 'email': 'x@example.com'}))
        form.validate()
        html = self.render("{{ ui.render_field(form.username) }}", form=form)
        self.assertIn('data-invalid="true"', html)
        self.assertIn('aria-invalid="true"', html)
        self.assertIn('data-slot="field-error"', html)
        self.assertIn('role="alert"', html)
        self.assertIn('Field must be between 4 and 25 characters long', html)

    def test_render_boolean_field(self):
        form = UserForm()
        html = self.render("{{ ui.render_field(form.terms) }}", form=form)
        self.assertIn('data-slot="checkbox"', html)
        self.assertIn('role="checkbox"', html)
        self.assertIn('data-orientation="horizontal"', html)
        self.assertIn('I agree to the terms', html)

    def test_render_select_field(self):
        form = UserForm(data={'role': 'member'})
        html = self.render("{{ ui.render_field(form.role) }}", form=form)
        self.assertIn('data-slot="native-select"', html)
        self.assertIn('<select', html)
        self.assertIn('Admin', html)
        self.assertIn('value="member" selected', html.replace('selected=""', 'selected'))

    def test_render_form_complete(self):
        form = UserForm()
        html = self.render("{{ ui.render_form(form, action='/submit', submit_text='Save User') }}", form=form)
        self.assertIn('<form action="/submit"', html)
        self.assertIn('data-slot="field-group"', html)
        self.assertIn('Save User', html)
        self.assertIn('type="submit"', html)
        self.assertIn('Username', html)
        self.assertIn('Email', html)

    def test_no_raw_colours_in_adapter_output(self):
        import re
        form = UserForm(MultiDict({'username': 'a'}))
        form.validate()
        html = self.render("{{ ui.render_form(form) }}", form=form)
        self.assertEqual(re.findall(r'\b(?:text|bg|border)-(?:red|gray|slate|zinc)-\d+\b', html), [])
