"""
Browser-based tests for flash message rendering
"""
import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from .live_server import TEST_SERVER_BASE_URL


class FlashMessageBrowserTest(unittest.TestCase):
    """Browser tests for flash message rendering"""

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
            cls.driver.implicitly_wait(10)
            cls.base_url = TEST_SERVER_BASE_URL
        except Exception as e:
            raise unittest.SkipTest(f"Chrome driver not available: {e}")

    @classmethod
    def tearDownClass(cls):
        """Close browser"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()

    def setUp(self):
        """Clear cookies and session before each test"""
        self.driver.delete_all_cookies()

    def test_login_flash_message_appears_once(self):
        """Test that 'Please log in' flash message only appears once, not 4 times"""
        # Navigate to a protected page that requires login
        self.driver.get(f'{self.base_url}/account/manage/info')

        # Should redirect to login page with flash message
        WebDriverWait(self.driver, 10).until(
            EC.url_contains('/account/login')
        )

        # Wait for flash messages to load
        time.sleep(2)

        # Debug: Check page source for flash messages
        page_source = self.driver.page_source
        flash_count = page_source.count('Please log in to access this page')

        # Should appear exactly once in HTML, not 4 times
        self.assertEqual(flash_count, 1,
                        f"Expected 1 'Please log in' message in HTML, found {flash_count}")

    def test_flash_message_has_close_button(self):
        """Test that flash messages have close buttons"""
        self.driver.get(f'{self.base_url}/account/manage/info')

        WebDriverWait(self.driver, 10).until(
            EC.url_contains('/account/login')
        )

        # Find flash message
        flash_message = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'flash-message'))
        )

        # Check for close button
        close_button = flash_message.find_element(By.CLASS_NAME, 'close')
        self.assertIsNotNone(close_button)
        self.assertTrue(close_button.is_displayed())

    def test_flash_message_dismissable(self):
        """Test that flash messages can be dismissed"""
        self.driver.get(f'{self.base_url}/account/manage/info')

        WebDriverWait(self.driver, 10).until(
            EC.url_contains('/account/login')
        )

        # Find and click close button
        close_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.flash-message .close'))
        )
        close_button.click()

        # Wait for message to be hidden
        time.sleep(0.5)

        # Message should be hidden (display: none)
        flash_message = self.driver.find_element(By.CLASS_NAME, 'flash-message')
        self.assertFalse(flash_message.is_displayed(),
                        "Flash message should be hidden after clicking close")


if __name__ == '__main__':
    unittest.main()
