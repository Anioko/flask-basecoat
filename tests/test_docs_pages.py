import unittest

from app import create_app, db


class DocsPagesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_blocks_overview_page(self):
        response = self.client.get('/docs/blocks')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Shadcn blocks inventory', response.data)
        self.assertIn(b'Blocks Overview', response.data)

    def test_category_page_renders(self):
        response = self.client.get('/docs/blocks/sidebar')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sidebar blocks', response.data)
        self.assertIn(b'View block details', response.data)

    def test_block_detail_page_renders(self):
        response = self.client.get('/docs/blocks/sidebar/sidebar-01')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ui.shadcn.com/blocks/sidebar-01', response.data)
        self.assertIn(b'Categories', response.data)
        self.assertIn(b'Nebula UI', response.data)

    def test_dashboard_block_has_preview(self):
        response = self.client.get('/docs/blocks/dashboard/dashboard-01')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Growth overview', response.data)
        self.assertIn(b'Active users', response.data)

    def test_invalid_category_returns_404(self):
        response = self.client.get('/docs/blocks/not-real')
        self.assertEqual(response.status_code, 404)

    def test_block_outside_category_returns_404(self):
        response = self.client.get('/docs/blocks/sidebar/dashboard-01')
        self.assertEqual(response.status_code, 404)

    def test_login_block_preview(self):
        response = self.client.get('/docs/blocks/login/login-01')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)
        self.assertIn(b'Sign in to continue', response.data)

    def test_calendar_block_preview(self):
        response = self.client.get('/docs/blocks/calendar/calendar-05')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'range selection', response.data.lower())
        self.assertIn(b'apply', response.data.lower())

    def test_calendar_block_from_secondary_category(self):
        response = self.client.get('/docs/blocks/date/calendar-01')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'single date', response.data.lower())

    def test_drawer_category_page_renders(self):
        response = self.client.get('/docs/blocks/drawer')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Drawer blocks', response.data)

    def test_drawer_block_preview(self):
        response = self.client.get('/docs/blocks/drawer/drawer-01')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Project settings', response.data)
        self.assertIn(b'Nebula Launch', response.data)

    def test_pricing_category_page_renders(self):
        response = self.client.get('/docs/blocks/pricing')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Pricing blocks', response.data)
        self.assertIn(b'View block details', response.data)

    def test_pricing_block_preview(self):
        response = self.client.get('/docs/blocks/pricing/pricing-02')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Simple pricing for growing product teams', response.data)
        self.assertIn(b'Billing', response.data)
        self.assertIn(b'Upgrade', response.data)

    def test_faq_category_page_renders(self):
        response = self.client.get('/docs/blocks/faq')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'FAQ blocks', response.data)
        self.assertIn(b'View block details', response.data)

    def test_faq_block_preview(self):
        response = self.client.get('/docs/blocks/faq/faq-01')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Answers for Flask-Basecoat teams', response.data)
        self.assertIn(b'Read migration guide', response.data)
        self.assertIn(b'Semantic UI', response.data)

    def test_testimonial_category_page_renders(self):
        response = self.client.get('/docs/blocks/testimonial')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Testimonial blocks', response.data)
        self.assertIn(b'View block details', response.data)

    def test_testimonial_block_preview(self):
        response = self.client.get('/docs/blocks/testimonial/testimonial-02')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Loved by scaling product teams', response.data)
        self.assertIn(b'Read the full case study', response.data)
        self.assertIn(b'Snapshot of Q3 customer sentiment surveys', response.data)

    def test_feature_category_page_renders(self):
        response = self.client.get('/docs/blocks/feature')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Feature blocks', response.data)
        self.assertIn(b'View block details', response.data)

    def test_feature_block_preview(self):
        response = self.client.get('/docs/blocks/feature/feature-03')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Operational excellence out of the box', response.data)
        self.assertIn(b'+42%', response.data)
        self.assertIn(b'Release guardrails', response.data)

    def test_cta_category_page_renders(self):
        response = self.client.get('/docs/blocks/cta')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CTA blocks', response.data)
        self.assertIn(b'View block details', response.data)

    def test_cta_block_preview(self):
        response = self.client.get('/docs/blocks/cta/cta-01')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Launch your next experience in days', response.data)
        self.assertIn(b'Trusted by teams shipping weekly', response.data)
        self.assertIn(b'Start free trial', response.data)

    def test_hero_category_page_renders(self):
        response = self.client.get('/docs/blocks/hero')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hero blocks', response.data)
        self.assertIn(b'View block details', response.data)

    def test_hero_block_preview(self):
        response = self.client.get('/docs/blocks/hero/hero-01')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ship product journeys in days, not months', response.data)
        self.assertIn(b'Browse blocks', response.data)
        self.assertIn(b'Trusted by product teams', response.data)
