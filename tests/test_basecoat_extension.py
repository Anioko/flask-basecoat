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

        # 5. /examples/pricing
        resp_pricing = client.get('/examples/pricing')
        self.assertEqual(resp_pricing.status_code, 200)
        self.assertIn('Simple, transparent pricing', resp_pricing.get_data(as_text=True))
        self.assertIn('Enterprise', resp_pricing.get_data(as_text=True))

        # 6. /examples/profile
        resp_profile = client.get('/examples/profile')
        self.assertEqual(resp_profile.status_code, 200)
        self.assertIn('Account Center', resp_profile.get_data(as_text=True))
        self.assertIn('John Doe', resp_profile.get_data(as_text=True))

        # 7. /examples/projects
        resp_projects = client.get('/examples/projects')
        self.assertEqual(resp_projects.status_code, 200)
        self.assertIn('Projects', resp_projects.get_data(as_text=True))
        self.assertIn('Mobile Banking Redesign', resp_projects.get_data(as_text=True))

        # 8. /examples/changelog
        resp_changelog = client.get('/examples/changelog')
        self.assertEqual(resp_changelog.status_code, 200)
        self.assertIn('Changelog', resp_changelog.get_data(as_text=True))
        self.assertIn('v1.2.0', resp_changelog.get_data(as_text=True))

        # 9. /examples/coming-soon
        resp_cs = client.get('/examples/coming-soon')
        self.assertEqual(resp_cs.status_code, 200)
        self.assertIn('Something extraordinary is on the way', resp_cs.get_data(as_text=True))
        self.assertIn('Launching Q4 2026', resp_cs.get_data(as_text=True))

        # 10. /examples/blog
        resp_blog = client.get('/examples/blog')
        self.assertEqual(resp_blog.status_code, 200)
        self.assertIn('Acme Journal', resp_blog.get_data(as_text=True))
        self.assertIn('Recent Articles', resp_blog.get_data(as_text=True))

        # 11. /examples/onboarding
        resp_onboard = client.get('/examples/onboarding')
        self.assertEqual(resp_onboard.status_code, 200)
        self.assertIn('Organization', resp_onboard.get_data(as_text=True))
        self.assertIn('Account Purpose', resp_onboard.get_data(as_text=True))

        # 12. /examples/chat
        resp_chat = client.get('/examples/chat')
        self.assertEqual(resp_chat.status_code, 200)
        self.assertIn('Acme Messenger', resp_chat.get_data(as_text=True))
        self.assertIn('Shannon Baker', resp_chat.get_data(as_text=True))

        # 13. /examples/ai-chat
        resp_ai = client.get('/examples/ai-chat')
        self.assertEqual(resp_ai.status_code, 200)
        self.assertIn('Acme Copilot AI', resp_ai.get_data(as_text=True))
        self.assertIn('Welcome, John Doe', resp_ai.get_data(as_text=True))

        # 14. /examples/playground
        resp_play = client.get('/examples/playground')
        self.assertEqual(resp_play.status_code, 200)
        self.assertIn('Playground', resp_play.get_data(as_text=True))
        self.assertIn('System Instructions', resp_play.get_data(as_text=True))

        # 15. /examples/product-list
        resp_plist = client.get('/examples/product-list')
        self.assertEqual(resp_plist.status_code, 200)
        self.assertIn('Acme Store', resp_plist.get_data(as_text=True))
        self.assertIn('Studio Pro Active Headphones', resp_plist.get_data(as_text=True))

        # 16. /examples/product-detail
        resp_pdetail = client.get('/examples/product-detail')
        self.assertEqual(resp_pdetail.status_code, 200)
        self.assertIn('Technical Specifications', resp_pdetail.get_data(as_text=True))
        self.assertIn('Studio Pro Active Headphones', resp_pdetail.get_data(as_text=True))

        # 17. /examples/kanban
        resp_kanban = client.get('/examples/kanban')
        self.assertEqual(resp_kanban.status_code, 200)
        self.assertIn('Sprint 42', resp_kanban.get_data(as_text=True))
        self.assertIn('Backlog', resp_kanban.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
