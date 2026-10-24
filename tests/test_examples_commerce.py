"""The commerce screens ported from shadcn-examples render, carry their upstream headings and use only macro controls."""
import re
import unittest

from flask import render_template

from flask_basecoat.testing import make_app
from flask_basecoat.examples import examples_bp, ported_examples

HEADINGS = {
    'cart': ['Shopping Cart', 'Coupon Code', 'Order Summary', 'Payment Method', 'Apply Your Coupon', 'Check Out',
             'Samsung Galaxy S23 Ultra S918B/DS 256GB', '$2929.92'],
    'checkout-page': ['Payment Method', 'Order Details', 'Credit/Debit Card', 'Mandiri Virtual Account', 'Mastering Illustration',
                      'GWENCHANA', 'Yeay, you got $10 discount!', 'Checkout Now', '$289'],
    'product-list': ['Related categories', 'Brands', 'Colors', 'Delivery date', 'Price', 'Filters', 'Search products...',
                     'iPhone 14 Pro Max 256GB Space Black', 'Apple Watch Series 9 GPS 45mm', 'No products found matching your filters.'],
    'product-detail-page': ['Stonewind Trekker', 'Jacket', '$99.29', '$102.97', '498 products sold out', 'Color (Ocean Blue)',
                            'Size Guide', 'Composition', 'Quantity', 'Add to Cart', 'Buy Now'],
    'add-product-form': ['General', 'Media', 'Variation', 'Pricing', 'Thumbnail', 'Status', 'Product Details', 'Product Template',
                         'Add another variation', 'Create New Category', 'Save changes'],
    'multi-step-form': ['Let&#39;s personalize your experience', 'What best describes your role?', 'What do you want to automate first?',
                        'Role &amp; Use Case', 'Invite Team', 'Continue', 'Step 1 of 5'],
    'settings-page': ['Personal information', 'Address information', 'Password', '2-Step verification', 'Notification', 'Billing',
                      'Transaction history', 'Integration', 'Google Drive', 'Gitlab'],
    'profile-page': ['John Doe', 'Pro Member', 'Personal Information', 'Account Settings', 'Danger Zone', 'Security Settings',
                     'Notification Preferences', 'Security Alerts'],
    'onboarding-flow': ['Account Type', 'Account Info', 'Business Details', 'Billing Details', 'Completed', 'Choose Account Type',
                        'Corporate Account', 'Select Account Plan', 'Save Card for further billing?', 'Your Are Done!'],
    'authentication': ['Create an account', 'Enter your email below to create your account', 'Sign In with Email', 'Or continue with',
                       'GitHub', 'Acme Inc', 'Terms of Service', 'Privacy Policy'],
}
# Static routes registered before the ported catch-all answer these URLs, so these screens are rendered directly.
SHADOWED = {'authentication', 'product-list'}
RAW_CONTROL = re.compile(r'<(button|input|select|textarea)\b(?![^>]*data-slot=)(?![^>]*type="hidden")', re.I)


class CommerceExamplesTest(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        if 'basecoat_examples' not in self.app.blueprints:
            self.app.register_blueprint(examples_bp, url_prefix='/examples')
        self.client = self.app.test_client()

    def render(self, slug, method='GET', data=None):
        if slug in SHADOWED:
            with self.app.test_request_context(f'/examples/{slug}', method=method, data=data):
                return 200, render_template(f'examples/ported/{slug}.html')
        r = self.client.open(f'/examples/{slug}', method=method, data=data)
        return r.status_code, r.get_data(as_text=True)

    def test_screens_render_with_their_headings(self):
        for slug, headings in HEADINGS.items():
            with self.subTest(slug=slug):
                status, html = self.render(slug)
                self.assertEqual(status, 200)
                self.assertIn('class="style-vega', html)
                for h in headings:
                    self.assertIn(h, html)

    def test_no_raw_controls(self):
        for slug in HEADINGS:
            with self.subTest(slug=slug):
                _, html = self.render(slug)
                body = html.split('<body', 1)[1]
                self.assertEqual(RAW_CONTROL.findall(body), [])

    def test_screens_are_listed(self):
        ids = {m['id'] for m in ported_examples()}
        self.assertTrue(set(HEADINGS) <= ids)

    def test_component_inventory(self):
        minimum = {
            'cart': {'button': 16, 'input': 1},
            'checkout-page': {'card': 8, 'input': 4, 'checkbox': 1, 'badge': 1, 'separator': 1, 'label': 5},
            'product-list': {'card': 12, 'badge': 17, 'radio-group-item': 26, 'checkbox': 36, 'slider': 2, 'toggle-group': 2, 'sheet-content': 1, 'scroll-area': 1, 'separator': 8},
            'product-detail-page': {'radio-group': 2, 'radio-group-item': 7, 'button': 11, 'separator': 1, 'label': 11},
            'add-product-form': {'card': 8, 'input': 5, 'textarea': 1, 'select-trigger': 3, 'radio-group-item': 3, 'badge': 1, 'separator': 1},
            'multi-step-form': {'button': 13},
            'settings-page': {'card': 16, 'avatar': 1, 'switch': 11, 'checkbox': 4, 'radio-group-item': 3, 'select-trigger': 2, 'badge': 7, 'separator': 3},
            'profile-page': {'card': 6, 'tabs-trigger': 4, 'tabs-content': 4, 'switch': 7, 'textarea': 1, 'badge': 3, 'avatar': 1, 'separator': 10},
            'onboarding-flow': {'card': 3, 'radio-group-item': 3, 'select-trigger': 3, 'switch': 1, 'alert': 1, 'input': 6},
            'authentication': {'button': 3, 'input': 1, 'label': 1},
        }
        for slug, counts in minimum.items():
            _, html = self.render(slug)
            for slot, n in counts.items():
                with self.subTest(slug=slug, slot=slot):
                    self.assertGreaterEqual(html.count(f'data-slot="{slot}"'), n)

    def test_add_product_validation(self):
        status, html = self.render('add-product-form', 'POST', {'name': '', 'basePrice': '', 'vatAmount': '', 'categories': 'Headphones'})
        self.assertEqual(status, 200)
        for msg in ['Product name is required', 'Base price is required', 'VAT amount is required']:
            self.assertIn(msg, html)
        self.assertEqual(html.count('data-slot="field-error"'), 3)
        self.assertEqual(html.count('aria-invalid="true"'), 3)
        _, ok = self.render('add-product-form', 'POST', {'name': 'Desk', 'basePrice': '10', 'vatAmount': '20', 'status': 'draft'})
        self.assertNotIn('data-slot="field-error"', ok)
        self.assertIn('value="Desk"', ok)

    def test_forms_post_back_to_themselves(self):
        for slug in ['cart', 'checkout-page', 'product-detail-page', 'add-product-form', 'multi-step-form', 'settings-page', 'onboarding-flow', 'authentication']:
            with self.subTest(slug=slug):
                _, html = self.render(slug)
                self.assertRegex(html, rf'<form method="post" action="/examples/{slug}"')
                status, _ = self.render(slug, 'POST', {})
                self.assertEqual(status, 200)

    def test_posted_values_are_kept(self):
        _, html = self.render('authentication', 'POST', {'email': 'ada@example.com'})
        self.assertIn('value="ada@example.com"', html)
        _, html = self.render('settings-page', 'POST', {'section': 'security', 'currentPassword': 'x'})
        self.assertRegex(html, r'data-section="security">')
        _, html = self.render('multi-step-form', 'POST', {'step': '0', 'role': 'designer', 'automation': 'emails'})
        self.assertIn('Step 2 of 5', html)
        _, html = self.render('onboarding-flow', 'POST', {'accountType': 'personal', 'nameOnCard': 'Max Doe'})
        self.assertIn('var step = 5;', html)


if __name__ == '__main__':
    unittest.main()
