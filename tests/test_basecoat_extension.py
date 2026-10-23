import unittest
from flask import Flask
from flask_basecoat import Basecoat


class BasecoatExtensionTestCase(unittest.TestCase):
    def test_extension_init_and_gallery_endpoint(self):
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret'
        app.config['BASECOAT_GALLERY_ENABLED'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        basecoat = Basecoat(app)
        
        # Verify blueprints
        self.assertIn('basecoat', app.blueprints)
        self.assertIn('basecoat_gallery', app.blueprints)
        self.assertIn('basecoat_examples', app.blueprints)
        
        # Test client GET /basecoat/gallery
        client = app.test_client()
        response = client.get('/basecoat/gallery')
        self.assertEqual(response.status_code, 200)
        
        html = response.get_data(as_text=True)
        self.assertIn('Basecoat UI Component Gallery', html)
        self.assertIn('btn btn-primary', html)
        self.assertIn('badge badge-primary', html)
        self.assertIn('Confirm Action', html)

    def test_gallery_form_submission_success(self):
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret'
        app.config['BASECOAT_GALLERY_ENABLED'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        Basecoat(app)
        client = app.test_client()
        
        # Valid POST
        response = client.post('/basecoat/gallery', data={
            'name': 'Jane Developer',
            'email': 'jane@example.com',
            'role': 'lead',
            'bio': 'Full-stack lead',
            'terms': 'y'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Demo form submitted successfully', html)

    def test_gallery_form_submission_validation_error(self):
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret'
        app.config['BASECOAT_GALLERY_ENABLED'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        Basecoat(app)
        client = app.test_client()
        
        # Invalid POST (missing email, short name)
        response = client.post('/basecoat/gallery', data={
            'name': 'a',
            'email': 'invalid'
        })
        
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('border-destructive', html)
        self.assertIn('Please correct the validation errors', html)

    def test_examples_endpoints(self):
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret'
        app.config['WTF_CSRF_ENABLED'] = False
        
        Basecoat(app)
        client = app.test_client()
        
        # 1. /examples index
        resp = client.get('/examples/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Application Screen Examples', resp.get_data(as_text=True))
        
        # 2. /examples/authentication
        resp_auth = client.get('/examples/authentication')
        self.assertEqual(resp_auth.status_code, 200)
        self.assertIn('Create an account', resp_auth.get_data(as_text=True))
        self.assertIn('Acme Inc', resp_auth.get_data(as_text=True))
        
        # 3. /examples/dashboard
        resp_dash = client.get('/examples/dashboard')
        self.assertEqual(resp_dash.status_code, 200)
        self.assertIn('Dashboard', resp_dash.get_data(as_text=True))
        self.assertIn('Total Revenue', resp_dash.get_data(as_text=True))
        self.assertIn('Recent Sales', resp_dash.get_data(as_text=True))
        
        # 4. /examples/tasks
        resp_tasks = client.get('/examples/tasks')
        self.assertEqual(resp_tasks.status_code, 200)
        self.assertIn('Tasks', resp_tasks.get_data(as_text=True))
        self.assertIn('TASK-8782', resp_tasks.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
