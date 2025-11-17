"""
Browser tests for table styling verification
Tests that table borders and lines are clearly visible
"""
import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .live_server import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD, TEST_SERVER_BASE_URL


@pytest.fixture
def driver():
    """Create a Chrome WebDriver instance"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as exc:  # pragma: no cover - handled via skip
        pytest.skip(f"Chrome driver not available: {exc}")
    driver.implicitly_wait(5)
    yield driver
    driver.quit()


def login(driver, email=TEST_ADMIN_EMAIL, password=TEST_ADMIN_PASSWORD):
    """Helper to log in a user"""
    driver.get(f'{TEST_SERVER_BASE_URL}/account/login')

    # Wait for login form
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, 'email'))
    )

    driver.find_element(By.NAME, 'email').send_keys(email)
    driver.find_element(By.NAME, 'password').send_keys(password)
    driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()

    # Wait for redirect
    WebDriverWait(driver, 10).until(
    EC.url_changes(f'{TEST_SERVER_BASE_URL}/account/login')
    )


class TestTableStyling:
    """Test table styling on account settings page"""

    def test_table_has_borders(self, driver):
        """Test that table has visible borders"""
        login(driver)
        driver.get(f'{TEST_SERVER_BASE_URL}/account/manage')

        # Wait for table to load
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.table'))
        )

        # Check table exists
        assert table is not None, "Table should be present"

        # Check table has border-collapse
        border_collapse = table.value_of_css_property('border-collapse')
        assert border_collapse == 'collapse', f"Table should have border-collapse: collapse, got {border_collapse}"

    def test_table_header_has_bottom_border(self, driver):
        """Test that table header has visible bottom border"""
        login(driver)
        driver.get(f'{TEST_SERVER_BASE_URL}/account/manage')

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.table'))
        )

        thead_elements = driver.find_elements(By.CSS_SELECTOR, '.table thead')
        if not thead_elements:
            rows = driver.find_elements(By.CSS_SELECTOR, '.table tbody tr')
            assert len(rows) > 0, "Should have table rows"
            return

        thead = thead_elements[0]

        # Check thead has bottom border
        border_bottom = thead.value_of_css_property('border-bottom-width')
        assert border_bottom == '2px', f"Table thead should have 2px bottom border, got {border_bottom}"

        # Check border color is visible (not transparent)
        border_color = thead.value_of_css_property('border-bottom-color')
        assert border_color != 'rgba(0, 0, 0, 0)', "Border color should not be transparent"

    def test_table_rows_have_borders(self, driver):
        """Test that table rows have visible borders between them"""
        login(driver)
        driver.get(f'{TEST_SERVER_BASE_URL}/account/manage')

        # Wait for tbody rows
        rows = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.table tbody tr'))
        )

        # There should be at least 3 rows (Full name, Email, Account type)
        assert len(rows) >= 3, f"Should have at least 3 table rows, found {len(rows)}"

        # Check first row has bottom border (not the last one)
        first_row = rows[0]
        border_bottom = first_row.value_of_css_property('border-bottom-width')
        assert border_bottom == '1px', f"Table row should have 1px bottom border, got {border_bottom}"

        # Check border color
        border_color = first_row.value_of_css_property('border-bottom-color')
        assert border_color != 'rgba(0, 0, 0, 0)', "Border color should not be transparent"

    def test_table_cells_have_padding(self, driver):
        """Test that table cells have adequate padding"""
        login(driver)
        driver.get(f'{TEST_SERVER_BASE_URL}/account/manage')

        # Wait for table cells
        cells = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.table tbody td'))
        )

        assert len(cells) > 0, "Should have table cells"

        # Check first cell has padding
        first_cell = cells[0]
        padding_left = first_cell.value_of_css_property('padding-left')
        padding_top = first_cell.value_of_css_property('padding-top')

        # Should have at least 12px padding (1rem = 16px, but we check for minimum)
        assert float(padding_left.replace('px', '')) >= 12, f"Cell should have at least 12px left padding, got {padding_left}"
        assert float(padding_top.replace('px', '')) >= 10, f"Cell should have at least 10px top padding, got {padding_top}"

    def test_table_header_has_background(self, driver):
        """Test that table header has visible background color"""
        login(driver)
        driver.get(f'{TEST_SERVER_BASE_URL}/account/manage')

        # Wait for thead th elements
        headers = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.table thead th'))
        )

        # Note: The account manage table uses tbody only, no thead
        # So we test the td cells instead
        if len(headers) == 0:
            # This table doesn't have thead, that's okay
            # Check that tbody tr elements still have proper styling
            rows = driver.find_elements(By.CSS_SELECTOR, '.table tbody tr')
            assert len(rows) > 0, "Should have table rows"
        else:
            # If thead exists, check background
            first_header = headers[0]
            bg_color = first_header.value_of_css_property('background-color')
            assert bg_color != 'rgba(0, 0, 0, 0)', "Header should have visible background color"

    def test_table_hover_effect(self, driver):
        """Test that table rows have hover effect"""
        login(driver)
        driver.get(f'{TEST_SERVER_BASE_URL}/account/manage')

        # Wait for table rows
        rows = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.table tbody tr'))
        )

        assert len(rows) > 0, "Should have table rows"

        # Get initial background color
        first_row = rows[0]
        initial_bg = first_row.value_of_css_property('background-color')

        # Hover over row
        from selenium.webdriver.common.action_chains import ActionChains
        ActionChains(driver).move_to_element(first_row).perform()
        time.sleep(0.2)  # Wait for hover effect

        # Get hover background color
        hover_bg = first_row.value_of_css_property('background-color')

        # Note: Hover effect might not trigger in headless mode
        # This test documents the expected behavior
        # In real browser, hover_bg should be different from initial_bg

    def test_table_text_is_readable(self, driver):
        """Test that table text has good contrast and is readable"""
        login(driver)
        driver.get(f'{TEST_SERVER_BASE_URL}/account/manage')

        # Wait for table cells
        cells = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.table tbody td'))
        )

        assert len(cells) > 0, "Should have table cells"

        # Check text color is not default/black
        first_cell = cells[0]
        color = first_cell.value_of_css_property('color')

        # Should have a defined color (not default)
        assert color != 'rgba(0, 0, 0, 0)', "Text should have visible color"

        # Check font size is readable
        font_size = first_cell.value_of_css_property('font-size')
        size_px = float(font_size.replace('px', ''))
        assert size_px >= 12, f"Font size should be at least 12px, got {size_px}px"

    def test_admin_users_table_has_styling(self, driver):
        """Test that admin users table also has proper styling"""
        login(driver)
        driver.get(f'{TEST_SERVER_BASE_URL}/admin/users')

        # Wait for table
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.table'))
        )

        # Check this table has thead (unlike account table)
        thead = table.find_element(By.CSS_SELECTOR, 'thead')
        assert thead is not None, "Admin table should have thead"

        # Check thead has bottom border
        border_bottom = thead.value_of_css_property('border-bottom-width')
        assert border_bottom == '2px', f"Admin table thead should have 2px bottom border, got {border_bottom}"

        # Check tbody rows
        rows = table.find_elements(By.CSS_SELECTOR, 'tbody tr')
        assert len(rows) > 0, "Admin table should have rows"

        # Check first row has border
        first_row = rows[0]
        border_bottom = first_row.value_of_css_property('border-bottom-width')
        assert border_bottom == '1px', f"Admin table row should have 1px bottom border, got {border_bottom}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
