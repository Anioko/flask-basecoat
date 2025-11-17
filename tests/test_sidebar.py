"""
Unit and integration tests for sidebar components
"""
import unittest
from flask import url_for
from app import create_app, db
from app.models import User, Role


class SidebarRoutesTestCase(unittest.TestCase):
    """Test sidebar routes and views"""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        # Create test user
        Role.insert_roles()
        self.user = User(
            email='test@example.com',
            password='password',
            confirmed=True
        )
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_sidebar_demo_route_exists(self):
        """Test that /sidebar-demo route exists"""
        with self.app.test_request_context():
            url = url_for('main.sidebar_demo')
            self.assertEqual(url, '/sidebar-demo')

    def test_sidebar_demo_new_route_exists(self):
        """Test that /sidebar-demo-new route exists"""
        with self.app.test_request_context():
            url = url_for('main.sidebar_demo_new')
            self.assertEqual(url, '/sidebar-demo-new')

    def test_sidebar_demo_renders(self):
        """Test that sidebar demo page renders without errors"""
        response = self.client.get('/sidebar-demo')
        self.assertEqual(response.status_code, 200)

    def test_sidebar_demo_new_renders(self):
        """Test that new sidebar demo page renders without errors"""
        response = self.client.get('/sidebar-demo-new')
        self.assertEqual(response.status_code, 200)

    def test_sidebar_demo_new_contains_required_elements(self):
        """Test that sidebar demo contains required HTML elements"""
        response = self.client.get('/sidebar-demo-new')
        html = response.data.decode('utf-8')

        # Check for sidebar container
        self.assertIn('id="main-sidebar"', html)
        self.assertIn('class="sidebar', html)

        # Check for navigation items
        self.assertIn('Dashboard', html)
        self.assertIn('Projects', html)
        self.assertIn('Settings', html)

        # Check for JavaScript includes
        self.assertIn('sidebar.js', html)

    def test_sidebar_demo_new_guest_user(self):
        """Test sidebar with guest user (not authenticated)"""
        response = self.client.get('/sidebar-demo-new')
        html = response.data.decode('utf-8')

        # Guest user should be shown
        self.assertIn('guest@example.com', html)
        self.assertIn('Guest User', html)

    def test_sidebar_macro_imports(self):
        """Test that sidebar macros template exists and is importable"""
        from jinja2 import TemplateNotFound
        try:
            template = self.app.jinja_env.get_template('macros/sidebar_macros.html')
            self.assertIsNotNone(template)
        except TemplateNotFound:
            self.fail("sidebar_macros.html template not found")


class SidebarJavaScriptTestCase(unittest.TestCase):
    """Test sidebar JavaScript file"""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def test_sidebar_js_exists(self):
        """Test that sidebar.js file is accessible"""
        response = self.client.get('/static/scripts/sidebar.js')
        self.assertEqual(response.status_code, 200)

    def test_sidebar_js_contains_class(self):
        """Test that sidebar.js contains Sidebar class"""
        response = self.client.get('/static/scripts/sidebar.js')
        js_content = response.data.decode('utf-8')

        # Check for Sidebar class definition
        self.assertIn('class Sidebar', js_content)
        self.assertIn('constructor(sidebarElement)', js_content)

    def test_sidebar_js_contains_required_methods(self):
        """Test that sidebar.js contains required methods"""
        response = self.client.get('/static/scripts/sidebar.js')
        js_content = response.data.decode('utf-8')

        # Check for required methods
        self.assertIn('toggle()', js_content)
        self.assertIn('setState(state)', js_content)
        self.assertIn('toggleGroup(group)', js_content)
        self.assertIn('expandGroup(group)', js_content)
        self.assertIn('collapseGroup(group)', js_content)


class SidebarTemplateTestCase(unittest.TestCase):
    """Test sidebar template macros"""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_sidebar_macro_renders_basic(self):
        """Test basic sidebar macro rendering"""
        template_string = """
        {% import 'macros/sidebar_macros.html' as sb %}
        {{ sb.sidebar(id='test-sidebar', items=[], user=None) }}
        """
        template = self.app.jinja_env.from_string(template_string)
        html = template.render()

        self.assertIn('id="test-sidebar"', html)
        self.assertIn('class="sidebar', html)

    def test_sidebar_macro_renders_with_items(self):
        """Test sidebar macro with navigation items"""
        template_string = """
        {% import 'macros/sidebar_macros.html' as sb %}
        {% set items = [
            {'label': 'Home', 'href': '/'},
            {'label': 'About', 'href': '/about'}
        ] %}
        {{ sb.sidebar(id='test-sidebar', items=items, user=None) }}
        """
        template = self.app.jinja_env.from_string(template_string)
        html = template.render()

        self.assertIn('Home', html)
        self.assertIn('About', html)

    def test_sidebar_macro_renders_nested_items(self):
        """Test sidebar macro with nested navigation"""
        template_string = """
        {% import 'macros/sidebar_macros.html' as sb %}
        {% set items = [
            {
                'label': 'Projects',
                'children': [
                    {'label': 'Active', 'href': '/projects/active'},
                    {'label': 'Archived', 'href': '/projects/archived'}
                ]
            }
        ] %}
        {{ sb.sidebar(id='test-sidebar', items=items, user=None) }}
        """
        template = self.app.jinja_env.from_string(template_string)
        html = template.render()

        self.assertIn('Projects', html)
        self.assertIn('Active', html)
        self.assertIn('Archived', html)
        self.assertIn('sidebar-group', html)

    def test_breadcrumb_macro_renders(self):
        """Test breadcrumb macro rendering"""
        template_string = """
        {% import 'macros/sidebar_macros.html' as sb %}
        {% set items = [
            {'label': 'Home', 'href': '/'},
            {'label': 'Components', 'href': '/components'},
            {'label': 'Sidebar', 'href': '/components/sidebar'}
        ] %}
        {{ sb.breadcrumb(items) }}
        """
        template = self.app.jinja_env.from_string(template_string)
        html = template.render()

        self.assertIn('Home', html)
        self.assertIn('Components', html)
        self.assertIn('Sidebar', html)

    def test_sidebar_user_macro_renders(self):
        """Test user profile macro rendering"""
        template_string = """
        {% import 'macros/sidebar_macros.html' as sb %}
        {% set user = {'name': 'John Doe', 'email': 'john@example.com'} %}
        {{ sb.sidebar_user(user) }}
        """
        template = self.app.jinja_env.from_string(template_string)
        html = template.render()

        self.assertIn('John Doe', html)
        self.assertIn('john@example.com', html)


if __name__ == '__main__':
    unittest.main()
