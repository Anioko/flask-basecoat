"""sidebar-07 collapses to a 3rem icon rail (upstream collapsible="icon"): icons stay, labels hide, tooltips name the buttons."""
import unittest

from .live_server import TEST_SERVER_BASE_URL

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

URL = f'{TEST_SERVER_BASE_URL}/basecoat/blocks/sidebar-07'
LABELS = ('Playground', 'Models', 'Documentation', 'Settings')


@unittest.skipIf(sync_playwright is None, 'playwright is not installed')
class SidebarIconRailBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch()
        except Exception as e:
            cls.pw.stop()
            raise unittest.SkipTest(f'Chromium not available: {e}')

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1440, 'height': 900})
        self.page.goto(URL)
        self.page.wait_for_selector('[data-slot="sidebar"][data-state]')

    def tearDown(self):
        self.page.close()

    def rail_width(self):
        return self.page.evaluate('document.querySelector(\'[data-slot="sidebar-container"]\').getBoundingClientRect().width')

    def settle(self, width):
        self.page.wait_for_function(
            f'Math.abs(document.querySelector(\'[data-slot="sidebar-container"]\').getBoundingClientRect().width - {width}) < 0.5')

    def toggle(self):
        self.page.click('[data-slot="sidebar-trigger"]')

    def test_expanded_is_256px(self):
        self.settle(256)

    def test_collapsed_is_48px_rail_with_icons_and_no_labels(self):
        self.toggle()
        self.settle(48)
        self.assertEqual(self.page.get_attribute('[data-slot="sidebar"]', 'data-collapsible'), 'icon')
        for label in LABELS:
            button = self.page.locator(f'[data-slot="sidebar-content"] button:has(> span:text-is("{label}"))')
            self.assertTrue(button.locator('svg').first.is_visible(), label)
            self.assertLessEqual(button.bounding_box()['width'], 48, label)
            # upstream clips the label with the button's overflow-hidden: it lies wholly outside the button box
            box, text = button.bounding_box(), button.locator(f'span:text-is("{label}")').bounding_box()
            self.assertGreaterEqual(text['x'], box['x'] + box['width'], label)
        self.assertEqual(self.page.evaluate('getComputedStyle(document.querySelector(\'[data-slot="sidebar-group-label"]\')).opacity'), '0')
        # team switcher and user menu shrink to their avatar and icon box
        for selector in ('[data-slot="sidebar-header"] [data-sidebar="menu-button"]', '[data-slot="sidebar-footer"] [data-sidebar="menu-button"]'):
            self.assertLessEqual(self.page.locator(selector).bounding_box()['width'], 48, selector)

    def test_collapsed_tooltips_name_each_menu_button(self):
        self.assertEqual(self.page.locator('[data-slot="tooltip-content"][data-sidebar-tooltip]').count(), 4)
        self.toggle()
        self.settle(48)
        for label in LABELS:
            self.page.locator(f'[data-slot="sidebar-content"] button:has(> svg):has(> span:text-is("{label}"))').hover()
            tip = self.page.locator(f'[data-slot="tooltip-content"][data-state="open"]:text-is("{label}")')
            tip.wait_for(state='visible')
            self.page.mouse.move(900, 500)

    def test_tooltip_is_not_shown_when_expanded(self):
        self.page.locator('[data-slot="sidebar-content"] button:has(> span:text-is("Models"))').hover()
        self.page.wait_for_timeout(300)
        self.assertEqual(self.page.locator('[data-slot="tooltip-content"][data-state="open"]').count(), 0)

    def test_trigger_reopens_to_256px(self):
        self.toggle()
        self.settle(48)
        self.toggle()
        self.settle(256)
