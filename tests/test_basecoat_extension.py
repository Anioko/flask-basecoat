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
        self.assertIn('Olivia', resp_dash.get_data(as_text=True))

        # 4. /examples/tasks
        resp_tasks = client.get('/examples/tasks')
        self.assertEqual(resp_tasks.status_code, 200)
        self.assertIn('Tasks', resp_tasks.get_data(as_text=True))
        self.assertIn('TASK-8782', resp_tasks.get_data(as_text=True))

        # 5. /examples/pricing
        resp_pricing = client.get('/examples/pricing')
        self.assertEqual(resp_pricing.status_code, 200)
        self.assertIn('Pricing', resp_pricing.get_data(as_text=True))
        self.assertIn('Most Popular', resp_pricing.get_data(as_text=True))

        # 6. /examples/profile
        resp_profile = client.get('/examples/profile')
        self.assertEqual(resp_profile.status_code, 200)
        self.assertIn('John Doe', resp_profile.get_data(as_text=True))
        self.assertIn('Personal', resp_profile.get_data(as_text=True))

        # 7. /examples/projects
        resp_projects = client.get('/examples/projects')
        self.assertEqual(resp_projects.status_code, 200)
        self.assertIn('Projects Board', resp_projects.get_data(as_text=True))
        self.assertIn('Mobile App', resp_projects.get_data(as_text=True))

        # 8. /examples/changelog
        resp_changelog = client.get('/examples/changelog')
        self.assertEqual(resp_changelog.status_code, 200)
        self.assertIn('What', resp_changelog.get_data(as_text=True))
        self.assertIn('4.3.0', resp_changelog.get_data(as_text=True))

        # 9. /examples/coming-soon
        resp_cs = client.get('/examples/coming-soon')
        self.assertEqual(resp_cs.status_code, 200)
        self.assertIn('Coming Soon', resp_cs.get_data(as_text=True))
        self.assertIn('Get notified', resp_cs.get_data(as_text=True))

        # 10. /examples/blog
        resp_blog = client.get('/examples/blog')
        self.assertEqual(resp_blog.status_code, 200)
        self.assertIn('Recent Posts', resp_blog.get_data(as_text=True))
        self.assertIn('Mastering UI Elements', resp_blog.get_data(as_text=True))

        # 11. /examples/onboarding
        resp_onboard = client.get('/examples/onboarding')
        self.assertEqual(resp_onboard.status_code, 200)
        self.assertIn('Personal Account', resp_onboard.get_data(as_text=True))
        self.assertIn('Personal Account', resp_onboard.get_data(as_text=True))
        self.assertIn('Corporate Account', resp_onboard.get_data(as_text=True))

        # 12. /examples/chat
        resp_chat = client.get('/examples/chat')
        self.assertEqual(resp_chat.status_code, 200)
        self.assertIn('Messages', resp_chat.get_data(as_text=True))
        self.assertIn('Shannon Baker', resp_chat.get_data(as_text=True))

        # 13. /examples/ai-chat
        resp_ai = client.get('/examples/ai-chat')
        self.assertEqual(resp_ai.status_code, 200)
        self.assertIn('Welcome, John Doe', resp_ai.get_data(as_text=True))
        self.assertIn('Best icons library', resp_ai.get_data(as_text=True))

        # 14. /examples/playground
        resp_play = client.get('/examples/playground')
        self.assertEqual(resp_play.status_code, 200)
        self.assertIn('Playground', resp_play.get_data(as_text=True))
        self.assertIn('text-davinci-003', resp_play.get_data(as_text=True))

        # 15. /examples/product-list
        resp_plist = client.get('/examples/product-list')
        self.assertEqual(resp_plist.status_code, 200)
        self.assertIn('iPhone 14 Pro Max', resp_plist.get_data(as_text=True))
        self.assertIn('Sony WH-1000XM5', resp_plist.get_data(as_text=True))

        # 16. /examples/product-detail
        resp_pdetail = client.get('/examples/product-detail')
        self.assertEqual(resp_pdetail.status_code, 200)
        self.assertIn('Stonewind Trekker', resp_pdetail.get_data(as_text=True))
        self.assertIn('Jacket', resp_pdetail.get_data(as_text=True))

        # 17. /examples/kanban
        resp_kanban = client.get('/examples/kanban')
        self.assertEqual(resp_kanban.status_code, 200)
        self.assertIn('Sprint Board', resp_kanban.get_data(as_text=True))
        self.assertIn('Q2 2025', resp_kanban.get_data(as_text=True))
        self.assertIn('Backlog', resp_kanban.get_data(as_text=True))

        # 18. /examples/shopping-cart
        resp_cart = client.get('/examples/shopping-cart')
        self.assertEqual(resp_cart.status_code, 200)
        self.assertIn('Briefcase', resp_cart.get_data(as_text=True))
        self.assertIn('Emporio Armani', resp_cart.get_data(as_text=True))
        self.assertIn('Confirm Order', resp_cart.get_data(as_text=True))

        # 19. /examples/checkout
        resp_checkout = client.get('/examples/checkout')
        self.assertEqual(resp_checkout.status_code, 200)
        self.assertIn('Pick Delivery Method', resp_checkout.get_data(as_text=True))
        self.assertIn('Shipping Information', resp_checkout.get_data(as_text=True))

        # 20. /examples/add-product
        resp_addprod = client.get('/examples/add-product')
        self.assertEqual(resp_addprod.status_code, 200)
        self.assertIn('General', resp_addprod.get_data(as_text=True))
        self.assertIn('Product Name', resp_addprod.get_data(as_text=True))
        self.assertIn('Variations', resp_addprod.get_data(as_text=True))

        # 21. /examples/mail
        resp_mail = client.get('/examples/mail')
        self.assertEqual(resp_mail.status_code, 200)
        self.assertIn('Alicia Koch', resp_mail.get_data(as_text=True))
        self.assertIn('Meeting Tomorrow', resp_mail.get_data(as_text=True))
        self.assertIn('William Smith', resp_mail.get_data(as_text=True))

        # 22. /examples/calendar
        resp_cal = client.get('/examples/calendar')
        self.assertEqual(resp_cal.status_code, 200)
        self.assertIn('October 2026', resp_cal.get_data(as_text=True))
        self.assertIn('New event', resp_cal.get_data(as_text=True))
        self.assertIn('Today', resp_cal.get_data(as_text=True))

        # 23. /examples/file-manager
        resp_fm = client.get('/examples/file-manager')
        self.assertEqual(resp_fm.status_code, 200)
        self.assertIn('File Manager', resp_fm.get_data(as_text=True))
        self.assertIn('Upload', resp_fm.get_data(as_text=True))
        self.assertIn('Arion', resp_fm.get_data(as_text=True))

        # 24. /examples/two-factor
        resp_2fa = client.get('/examples/two-factor')
        self.assertEqual(resp_2fa.status_code, 200)
        self.assertIn('Two-step verification', resp_2fa.get_data(as_text=True))
        self.assertIn('john.doe@example.com', resp_2fa.get_data(as_text=True))

        # 25. /examples/task-detail
        resp_tdetail = client.get('/examples/task-detail')
        self.assertEqual(resp_tdetail.status_code, 200)
        self.assertIn('Workplace Safety Guide', resp_tdetail.get_data(as_text=True))
        self.assertIn('Phase 1', resp_tdetail.get_data(as_text=True))

        # 26. /examples/blog-detail
        resp_bdetail = client.get('/examples/blog-detail')
        self.assertEqual(resp_bdetail.status_code, 200)
        self.assertIn('The Best Way to Write a Recurring Email Newsletter', resp_bdetail.get_data(as_text=True))
        self.assertIn('Esther Howard', resp_bdetail.get_data(as_text=True))

        # 27. /examples/notifications
        resp_notif = client.get('/examples/notifications')
        self.assertEqual(resp_notif.status_code, 200)
        self.assertIn('Notifications', resp_notif.get_data(as_text=True))
        self.assertIn('Olivia Grant', resp_notif.get_data(as_text=True))
        self.assertIn('Mark all as read', resp_notif.get_data(as_text=True))


    def test_templates_zero_hardcoded_colors(self):
        """Merge Gate: Assert ZERO hardcoded hex colors exist in template examples."""
        import re
        from pathlib import Path

        hex_pattern = re.compile(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b')
        examples_dir = Path(__file__).resolve().parent.parent / 'flask_basecoat' / 'templates' / 'examples'
        self.assertTrue(examples_dir.is_dir(), f"Examples directory not found: {examples_dir}")

        violations = []
        for p in examples_dir.glob('*.html'):
            text = p.read_text(encoding='utf-8', errors='ignore')
            matches = hex_pattern.findall(text)
            real = [m for m in matches if m.lower() not in ['#fff', '#000']]
            if real:
                violations.append(f"{p.name}: {set(real)}")

        self.assertEqual(violations, [], f"Hardcoded hex colors found in templates (merge gate rejects): {violations}")

if __name__ == '__main__':
    unittest.main()
