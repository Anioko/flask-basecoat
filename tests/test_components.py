"""Test cases for shadcn/ui components documentation."""

import unittest
from app import create_app, db


class ComponentsTestCase(unittest.TestCase):
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

    def test_components_overview_page_renders(self):
        response = self.client.get('/docs/components')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'shadcn/ui Components', response.data)
        self.assertIn(b'components available', response.data)

    def test_button_component_page_renders(self):
        response = self.client.get('/docs/components/button')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Button', response.data)
        self.assertIn(b'Primary Button', response.data)
        self.assertIn(b'Secondary Button', response.data)
        self.assertIn(b'Jinja macro', response.data)
        self.assertIn(b'/basecoat/gallery/button', response.data)

    def test_card_component_page_renders(self):
        response = self.client.get('/docs/components/card')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Card', response.data)
        self.assertIn(b'Card Title', response.data)
        self.assertIn(b'Interactive Card', response.data)

    def test_badge_component_page_renders(self):
        response = self.client.get('/docs/components/badge')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Badge', response.data)
        self.assertIn(b'Default Badge', response.data)

    def test_alert_component_page_renders(self):
        response = self.client.get('/docs/components/alert')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Alert', response.data)
        self.assertIn(b'Default Alert', response.data)

    def test_avatar_component_page_renders(self):
        response = self.client.get('/docs/components/avatar')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Avatar', response.data)
        self.assertIn(b'User Avatar', response.data)

    def test_input_component_page_renders(self):
        response = self.client.get('/docs/components/input')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Input', response.data)
        self.assertIn(b'Default Input', response.data)

    def test_tooltip_component_page_renders(self):
        response = self.client.get('/docs/components/tooltip')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Tooltip', response.data)
        self.assertIn(b'Default', response.data)

    def test_tabs_component_page_renders(self):
        response = self.client.get('/docs/components/tabs')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Tabs', response.data)
        self.assertIn(b'Account', response.data)

    def test_dialog_component_page_renders(self):
        response = self.client.get('/docs/components/dialog')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dialog', response.data)
        self.assertIn(b'Open', response.data)

    def test_popover_component_page_renders(self):
        response = self.client.get('/docs/components/popover')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Popover', response.data)
        self.assertIn(b'Dimensions', response.data)

    def test_breadcrumb_component_page_renders(self):
        response = self.client.get('/docs/components/breadcrumb')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Breadcrumb', response.data)
        self.assertIn(b'Home', response.data)

    def test_separator_component_page_renders(self):
        response = self.client.get('/docs/components/separator')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Separator', response.data)

    def test_command_component_page_renders(self):
        response = self.client.get('/docs/components/command')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Command', response.data)
        self.assertIn(b'search', response.data)

    def test_dropdown_component_page_renders(self):
        response = self.client.get('/docs/components/dropdown')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dropdown', response.data)
        self.assertIn(b'Open', response.data)

    def test_sheet_component_page_renders(self):
        response = self.client.get('/docs/components/sheet')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sheet', response.data)

    def test_skeleton_component_page_renders(self):
        response = self.client.get('/docs/components/skeleton')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Skeleton', response.data)

    def test_table_component_page_renders(self):
        response = self.client.get('/docs/components/table')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Table', response.data)
        self.assertIn(b'Invoice', response.data)

    def test_switch_component_page_renders(self):
        response = self.client.get('/docs/components/switch')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Switch', response.data)

    def test_slider_component_page_renders(self):
        response = self.client.get('/docs/components/slider')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Slider', response.data)

    def test_invalid_component_returns_404(self):
        response = self.client.get('/docs/components/nonexistent')
        self.assertEqual(response.status_code, 404)

    def test_components_overview_shows_all_components(self):
        response = self.client.get('/docs/components')
        self.assertEqual(response.status_code, 200)
        # Check that key components are listed
        self.assertIn(b'Button', response.data)
        self.assertIn(b'Card', response.data)
        self.assertIn(b'Badge', response.data)
        self.assertIn(b'Alert', response.data)
        self.assertIn(b'Avatar', response.data)
        self.assertIn(b'Input', response.data)
        # Check new components
        self.assertIn(b'Tooltip', response.data)
        self.assertIn(b'Tabs', response.data)
        self.assertIn(b'Dialog', response.data)
        self.assertIn(b'Table', response.data)
        self.assertIn(b'Switch', response.data)

    def test_component_styling_present(self):
        response = self.client.get('/docs/components/button')
        self.assertEqual(response.status_code, 200)
        # Check that component examples are rendered
        self.assertIn(b'btn-primary', response.data)
        self.assertIn(b'btn-secondary', response.data)
        self.assertIn(b'btn-outline', response.data)


if __name__ == '__main__':
    unittest.main()