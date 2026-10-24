"""Extension wiring: blueprints, asset tags, the WTForms demo and the example screens."""
import unittest

from flask import Flask

from flask_basecoat import Basecoat


def make():
    app = Flask(__name__)
    app.config.update(SECRET_KEY='test-secret', BASECOAT_GALLERY_ENABLED=True, WTF_CSRF_ENABLED=False)
    Basecoat(app)
    return app


class BasecoatExtensionTestCase(unittest.TestCase):
    def test_extension_registers_blueprints_and_globals(self):
        app = make()
        self.assertIn('basecoat', app.blueprints)
        self.assertIn('basecoat_gallery', app.blueprints)
        self.assertIn('basecoat_examples', app.blueprints)
        self.assertIn('lucide', app.jinja_env.globals)
        self.assertIn('slot', app.jinja_env.globals)
        self.assertIn('tw', app.jinja_env.globals)
        with app.test_request_context():
            self.assertIn("flask-basecoat.min.css", Basecoat(app).css())
            self.assertIn('flask-basecoat.js', Basecoat(app).js())

    def test_gallery_index_and_forms_page(self):
        client = make().test_client()
        r = client.get('/basecoat/')
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        self.assertIn('class="style-vega', html)
        self.assertIn('>button<', html)
        self.assertIn('>sidebar-07<', html)
        r = client.get('/basecoat/gallery')
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        self.assertIn('data-slot="field"', html)
        self.assertIn('data-slot="input"', html)
        self.assertIn('Create account', html)

    def test_gallery_form_submission_success(self):
        client = make().test_client()
        r = client.post('/basecoat/gallery', data={
            'name': 'Jane Developer', 'email': 'jane@example.com', 'role': 'lead', 'bio': 'Full-stack lead', 'terms': 'y',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        self.assertIn('Demo form submitted successfully', html)
        self.assertIn('data-fb-flash', html)

    def test_gallery_form_submission_validation_error(self):
        client = make().test_client()
        r = client.post('/basecoat/gallery', data={'name': 'a', 'email': 'invalid'})
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        self.assertIn('aria-invalid="true"', html)
        self.assertIn('data-slot="field-error"', html)
        self.assertIn('Please correct the validation errors', html)

    def test_examples_endpoints(self):
        client = make().test_client()
        for path, needles in {
            '/examples/': ['style-vega'],
            '/examples/authentication': ['Acme Inc'],
            '/examples/dashboard': ['Total Revenue'],
            '/examples/tasks': ['TASK-8782'],
            '/examples/pricing': ['Most Popular'],
        }.items():
            r = client.get(path)
            self.assertEqual(r.status_code, 200, path)
            html = r.get_data(as_text=True)
            for n in needles:
                self.assertIn(n, html, path)
            self.assertNotIn('cdn.jsdelivr.net', html, path)
            self.assertNotIn('data-lucide', html, path)
            self.assertNotIn('btn btn-', html, path)

    def test_examples_use_only_tokens_and_macros(self):
        import pathlib
        import re
        root = pathlib.Path(__file__).resolve().parents[1] / 'flask_basecoat' / 'templates' / 'examples'
        palette = re.compile(r'\b(?:bg|text|border|ring)-(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}\b|#[0-9a-fA-F]{6}\b')
        offenders = {}
        for f in root.glob('*.html'):
            hits = palette.findall(f.read_text(encoding='utf8'))
            if hits:
                offenders[f.name] = hits[:5]
        self.assertEqual(offenders, {})
