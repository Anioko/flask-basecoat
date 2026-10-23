import unittest
from flask import Flask, render_template_string
from werkzeug.datastructures import MultiDict
from wtforms import Form, StringField, BooleanField, SelectField, TextAreaField, validators
from flask_basecoat import Basecoat


class SampleForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25), validators.InputRequired()], description="Your public username.")
    email = StringField('Email', [validators.Email(), validators.InputRequired()])
    bio = TextAreaField('Bio', [validators.Optional()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('member', 'Member')])
    agree = BooleanField('I agree to the terms', [validators.InputRequired()])


class WTFormsAdapterTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'test-secret'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.basecoat = Basecoat(self.app)
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_render_field_valid(self):
        form = SampleForm(data={'username': 'octocat', 'email': 'octo@github.com'})
        tmpl = "{% from 'basecoat/form.html' import render_field %}{{ render_field(form.username) }}"
        rendered = render_template_string(tmpl, form=form)
        self.assertIn('for="username"', rendered)
        self.assertIn('Username', rendered)
        self.assertIn('value="octocat"', rendered)
        self.assertIn('class="input', rendered)
        self.assertNotIn('border-destructive', rendered)

    def test_render_field_with_validation_errors(self):
        form = SampleForm(formdata=MultiDict([('username', 'ab'), ('email', 'not-an-email')]))
        form.validate()
        self.assertTrue(len(form.username.errors) > 0)
        
        tmpl = "{% from 'basecoat/form.html' import render_field %}{{ render_field(form.username) }}"
        rendered = render_template_string(tmpl, form=form)
        self.assertIn('border-destructive', rendered)
        self.assertIn('text-destructive', rendered)
        self.assertIn('Field must be between 4 and 25 characters long', rendered)

    def test_render_boolean_field(self):
        form = SampleForm()
        tmpl = "{% from 'basecoat/form.html' import render_field %}{{ render_field(form.agree) }}"
        rendered = render_template_string(tmpl, form=form)
        self.assertIn('type="checkbox"', rendered)
        self.assertIn('I agree to the terms', rendered)

    def test_render_select_field(self):
        form = SampleForm()
        tmpl = "{% from 'basecoat/form.html' import render_field %}{{ render_field(form.role) }}"
        rendered = render_template_string(tmpl, form=form)
        self.assertIn('<select', rendered)
        self.assertIn('Admin', rendered)
        self.assertIn('Member', rendered)

    def test_render_form_complete(self):
        form = SampleForm()
        tmpl = "{% from 'basecoat/form.html' import render_form %}{{ render_form(form, action='/submit', submit_text='Save User') }}"
        rendered = render_template_string(tmpl, form=form)
        self.assertIn('<form action="/submit"', rendered)
        self.assertIn('Save User', rendered)
        self.assertIn('Username', rendered)
        self.assertIn('Email', rendered)


if __name__ == '__main__':
    unittest.main()
