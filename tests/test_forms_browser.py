"""
Browser-based tests for form styling and functionality
"""
import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class FormBrowserTest(unittest.TestCase):
    """Browser tests for form visual rendering and styling"""

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
            cls.base_url = 'http://localhost:5100'
        except Exception as e:
            raise unittest.SkipTest(f"Chrome driver not available: {e}")

    @classmethod
    def tearDownClass(cls):
        """Close browser"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()

    def test_login_page_loads(self):
        """Test that login page loads successfully"""
        self.driver.get(f'{self.base_url}/account/login')

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'form'))
        )

        # Verify page title
        self.assertIn('Flask-Basecoat', self.driver.title)

    def test_register_page_loads(self):
        """Test that register page loads successfully"""
        self.driver.get(f'{self.base_url}/account/register')

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'form'))
        )

        # Verify page title
        self.assertIn('Flask-Basecoat', self.driver.title)

    def test_login_button_properly_styled(self):
        """Test that login button has proper styling"""
        self.driver.get(f'{self.base_url}/account/login')

        # Find submit button
        submit_btn = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="submit"], button[type="submit"]'))
        )

        # Check button classes
        button_classes = submit_btn.get_attribute('class')
        self.assertIn('btn', button_classes, "Submit button should have 'btn' class")

        # Check if button is visible and clickable
        self.assertTrue(submit_btn.is_displayed())
        self.assertTrue(submit_btn.is_enabled())

    def test_register_button_properly_styled(self):
        """Test that register button has proper styling"""
        self.driver.get(f'{self.base_url}/account/register')

        # Find submit button
        submit_btn = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="submit"], button[type="submit"]'))
        )

        # Check button classes
        button_classes = submit_btn.get_attribute('class')
        self.assertIn('btn', button_classes, "Submit button should have 'btn' class")

        # Check if button is visible
        self.assertTrue(submit_btn.is_displayed())

    def test_login_inputs_properly_styled(self):
        """Test that login form inputs have proper styling"""
        self.driver.get(f'{self.base_url}/account/login')

        # Find all input fields
        inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="email"], input[type="password"]')

        self.assertGreater(len(inputs), 0, "Should have at least one input field")

        # Check first input has proper class
        first_input = inputs[0]
        input_classes = first_input.get_attribute('class')
        self.assertIn('input', input_classes, "Input field should have 'input' class")

    def test_register_inputs_properly_styled(self):
        """Test that register form inputs have proper styling"""
        self.driver.get(f'{self.base_url}/account/register')

        # Find all text input fields
        inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"], input[type="email"], input[type="password"]')

        self.assertGreater(len(inputs), 0, "Should have input fields")

        # Check all inputs have proper class
        for input_field in inputs:
            input_classes = input_field.get_attribute('class')
            self.assertIn('input', input_classes, f"Input {input_field.get_attribute('name')} should have 'input' class")

    def test_login_form_structure(self):
        """Test that login form has proper structure"""
        self.driver.get(f'{self.base_url}/account/login')

        # Check for email field
        email_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="email"]')
        self.assertTrue(email_input.is_displayed())

        # Check for password field
        password_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
        self.assertTrue(password_input.is_displayed())

        # Check for submit button
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"], button[type="submit"]')
        self.assertTrue(submit_btn.is_displayed())

    def test_register_form_structure(self):
        """Test that register form has proper structure"""
        self.driver.get(f'{self.base_url}/account/register')

        # Check for first name field
        first_name = self.driver.find_element(By.ID, 'first_name')
        self.assertTrue(first_name.is_displayed())

        # Check for last name field
        last_name = self.driver.find_element(By.ID, 'last_name')
        self.assertTrue(last_name.is_displayed())

        # Check for email field
        email_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="email"]')
        self.assertTrue(email_input.is_displayed())

        # Check for password fields
        password_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
        self.assertEqual(len(password_inputs), 2, "Should have 2 password fields (password + confirm)")

    def test_no_javascript_errors_login(self):
        """Test that login page loads without JavaScript errors"""
        self.driver.get(f'{self.base_url}/account/login')

        # Wait for page to fully load
        time.sleep(2)

        # Get browser console logs
        logs = self.driver.get_log('browser')

        # Filter out only errors (not warnings or info)
        errors = [log for log in logs if log['level'] == 'SEVERE']

        # We expect no severe errors
        critical_errors = [e for e in errors if 'share-modal' not in e['message']]

        self.assertEqual(len(critical_errors), 0,
                        f"JavaScript errors found: {critical_errors}")

    def test_no_javascript_errors_register(self):
        """Test that register page loads without JavaScript errors"""
        self.driver.get(f'{self.base_url}/account/register')

        # Wait for page to fully load
        time.sleep(2)

        # Get browser console logs
        logs = self.driver.get_log('browser')

        # Filter out only errors (not warnings or info)
        errors = [log for log in logs if log['level'] == 'SEVERE']

        # We expect no severe errors
        critical_errors = [e for e in errors if 'share-modal' not in e['message']]

        self.assertEqual(len(critical_errors), 0,
                        f"JavaScript errors found: {critical_errors}")

    def test_login_has_card_wrapper(self):
        """Test that login form has card wrapper styling"""
        self.driver.get(f'{self.base_url}/account/login')

        # Find card element
        card = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'card'))
        )

        self.assertTrue(card.is_displayed())

        # Check for card header
        card_header = self.driver.find_element(By.CLASS_NAME, 'card-header')
        self.assertTrue(card_header.is_displayed())

        # Check for card content
        card_content = self.driver.find_element(By.CLASS_NAME, 'card-content')
        self.assertTrue(card_content.is_displayed())

    def test_register_has_card_wrapper(self):
        """Test that register form has card wrapper styling"""
        self.driver.get(f'{self.base_url}/account/register')

        # Find card element
        card = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'card'))
        )

        self.assertTrue(card.is_displayed())

        # Check for card header
        card_header = self.driver.find_element(By.CLASS_NAME, 'card-header')
        self.assertTrue(card_header.is_displayed())

        # Check for card content
        card_content = self.driver.find_element(By.CLASS_NAME, 'card-content')
        self.assertTrue(card_content.is_displayed())


if __name__ == '__main__':
    unittest.main()
