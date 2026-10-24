"""The six dashboard example screens render with the shared frame, real charts and the expected sections."""
import re
import unittest

from flask_basecoat.testing import make_app
from flask_basecoat.examples import examples_bp, DASHBOARDS

SECTIONS = {
    'marketing': ['Key insights', 'Revenue overview', 'Sales distribution', 'Campaign performance', 'Top selling products'],
    'sales': ['Orders', 'Sales report', 'Weekly sales', 'Best selling products', 'Top projects', 'Daily activities'],
    'overview': ['Revenue updates', 'Monthly earnings', 'Yearly breakup', 'Sales from locations', 'Recent transactions', 'Upcoming schedules'],
    'analytics': ['Key insights', 'Website visits', 'Customer segmentation', 'Conversion rate', 'Top selling products'],
    'insights': ['Analytics dashboard', 'Revenue updates', 'Weekly stats', 'Top campaigns', 'Sales by country'],
    'pipeline': ['Total customers', 'Revenue overview', 'Revenue sources', 'Sales funnel', 'Lead sources', 'Recent events'],
}


class DashboardsTest(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        if 'basecoat_examples' not in self.app.blueprints:
            self.app.register_blueprint(examples_bp, url_prefix='/examples')
        self.client = self.app.test_client()

    def test_every_dashboard_renders(self):
        for name in DASHBOARDS:
            with self.subTest(name=name):
                r = self.client.get(f'/examples/dashboards/{name}')
                self.assertEqual(r.status_code, 200)
                html = r.get_data(as_text=True)
                self.assertIn('class="style-vega', html)
                self.assertIn('data-slot="sidebar-wrapper"', html)
                for section in SECTIONS[name]:
                    self.assertIn(section, html)
                self.assertGreaterEqual(html.count('data-slot="chart"'), 2)

    def test_active_dashboard_is_marked_in_the_sidebar(self):
        html = self.client.get('/examples/dashboards/insights').get_data(as_text=True)
        active = re.findall(r'<a[^>]*data-slot="sidebar-menu-button"[^>]*data-active="true"[^>]*>.*?</a>', html, re.S)
        self.assertEqual(len(active), 1)
        self.assertIn('Insights', active[0])

    def test_chart_data_is_valid_json_in_attributes(self):
        import json
        html = self.client.get('/examples/dashboards/marketing').get_data(as_text=True)
        from html import unescape
        payloads = re.findall(r'data-chart-data="([^"]+)"', html)
        self.assertTrue(payloads)
        for p in payloads:
            self.assertIsInstance(json.loads(unescape(p)), list)

    def test_unknown_dashboard_is_404(self):
        self.assertEqual(self.client.get('/examples/dashboards/nope').status_code, 404)

    def test_default_route_is_marketing(self):
        self.assertIn('Marketing dashboard', self.client.get('/examples/dashboards/').get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
