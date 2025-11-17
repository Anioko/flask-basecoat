"""
Browser-based integration tests for sidebar using Selenium
"""
import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

from .live_server import TEST_SERVER_BASE_URL


class SidebarBrowserTest(unittest.TestCase):
    """Browser tests for sidebar visual rendering and interactions"""

    @classmethod
    def setUpClass(cls):
        """Set up Chrome driver with headless mode"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            raise unittest.SkipTest(f"Chrome driver not available: {e}")
        cls.driver.implicitly_wait(10)
        cls.base_url = TEST_SERVER_BASE_URL

    @classmethod
    def tearDownClass(cls):
        """Close browser"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()

    def test_sidebar_page_loads(self):
        """Test that sidebar demo page loads successfully"""
        self.driver.get(f'{self.base_url}/sidebar-demo-new')

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'main-sidebar'))
        )

        # Verify page title
        self.assertIn('Flask-Basecoat', self.driver.title)

    def test_sidebar_element_exists(self):
        """Test that sidebar element is present in DOM"""
        self.driver.get(f'{self.base_url}/sidebar-demo-new')

        sidebar = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'main-sidebar'))
        )

        self.assertIsNotNone(sidebar)
        self.assertTrue(sidebar.is_displayed())

    def test_sidebar_icons_proper_size(self):
        """Test that sidebar icons are properly sized (not huge)"""
        self.driver.get(f'{self.base_url}/sidebar-demo-new')

        # Wait for sidebar to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'sidebar-icon'))
        )

        # Get all icon containers
        icon_containers = self.driver.find_elements(By.CLASS_NAME, 'sidebar-icon')

        self.assertGreater(len(icon_containers), 0, "No sidebar icons found")

        # Check first icon size
        first_icon = icon_containers[0]
        icon_width = first_icon.size['width']
        icon_height = first_icon.size['height']

        # Icons should be around 20px (w-5 = 1.25rem = 20px)
        # Allow some tolerance for browser rendering
        self.assertLess(icon_width, 30, f"Icon width {icon_width}px is too large (expected ~20px)")
        self.assertLess(icon_height, 30, f"Icon height {icon_height}px is too large (expected ~20px)")
        self.assertGreater(icon_width, 15, f"Icon width {icon_width}px is too small")
        self.assertGreater(icon_height, 15, f"Icon height {icon_height}px is too small")

    def test_sidebar_svg_elements_sized(self):
        """Test that SVG elements inside icons are properly constrained"""
        self.driver.get(f'{self.base_url}/sidebar-demo-new')

        # Wait for sidebar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'sidebar-icon'))
        )

        # Find SVG within icon container
        svg_elements = self.driver.find_elements(By.CSS_SELECTOR, '.sidebar-icon svg')

        self.assertGreater(len(svg_elements), 0, "No SVG elements found in sidebar icons")

        # Check SVG dimensions
        first_svg = svg_elements[0]
        svg_width = first_svg.size['width']
        svg_height = first_svg.size['height']

        # SVGs should be constrained to ~20px
        self.assertLess(svg_width, 30, f"SVG width {svg_width}px is too large (expected ~20px)")
        self.assertLess(svg_height, 30, f"SVG height {svg_height}px is too large (expected ~20px)")

    def test_sidebar_toggle_button_exists(self):
        """Test that sidebar toggle button is present"""
        self.driver.get(f'{self.base_url}/sidebar-demo-new')

        toggle_btn = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'sidebar-toggle'))
        )

        self.assertTrue(toggle_btn.is_displayed())
        self.assertTrue(toggle_btn.is_enabled())

    def test_sidebar_toggle_functionality(self):
        """Test that sidebar can be toggled between expanded and collapsed"""
        self.driver.get(f'{self.base_url}/sidebar-demo-new')

        sidebar = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'main-sidebar'))
        )

        # Get initial width
        initial_width = sidebar.size['width']

        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'sidebar-toggle'))
        )
        toggle_btn = self.driver.find_element(By.CLASS_NAME, 'sidebar-toggle')
        self.driver.execute_script("arguments[0].click();", toggle_btn)

        # Wait for animation to complete
        time.sleep(0.5)

        # Get new width
        collapsed_width = sidebar.size['width']

        # Sidebar should be narrower when collapsed
        self.assertLess(collapsed_width, initial_width,
                       f"Sidebar didn't collapse (was {initial_width}px, now {collapsed_width}px)")

        # Click again to expand
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'sidebar-toggle'))
        )
        self.driver.execute_script("arguments[0].click();", toggle_btn)
        time.sleep(0.5)

        expanded_width = sidebar.size['width']
        self.assertGreater(expanded_width, collapsed_width,
                          f"Sidebar didn't expand back")

    def test_navigation_items_present(self):
        """Test that navigation items are visible"""
        self.driver.get(f'{self.base_url}/sidebar-demo-new')

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'main-sidebar'))
        )

        # Check for specific nav items
        page_source = self.driver.page_source

        self.assertIn('Dashboard', page_source)
        self.assertIn('Projects', page_source)
        self.assertIn('Tasks', page_source)
        self.assertIn('Settings', page_source)

    def test_collapsible_groups_exist(self):
        """Test that collapsible navigation groups are present"""
        self.driver.get(f'{self.base_url}/sidebar-demo-new')

        groups = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'sidebar-group'))
        )

        self.assertGreater(len(groups), 0, "No collapsible groups found")

    def test_user_profile_section_present(self):
        """Test that user profile section is visible in sidebar footer"""
        self.driver.get(f'{self.base_url}/sidebar-demo-new')

        page_source = self.driver.page_source

        # Check for guest user info
        self.assertIn('Guest User', page_source)
        self.assertIn('guest@example.com', page_source)

    def test_no_javascript_errors(self):
        """Test that page loads without JavaScript errors"""
        self.driver.get(f'{self.base_url}/sidebar-demo-new')

        # Wait for page to fully load
        time.sleep(2)

        # Get browser console logs
        logs = self.driver.get_log('browser')

        # Filter out only errors (not warnings or info)
        errors = [log for log in logs if log['level'] == 'SEVERE']

        # We expect no severe errors (excluding the share-modal.js error which is unrelated)
        critical_errors = [e for e in errors if 'share-modal' not in e['message']]

        self.assertEqual(len(critical_errors), 0,
                        f"JavaScript errors found: {critical_errors}")


if __name__ == '__main__':
    unittest.main()
