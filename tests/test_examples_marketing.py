"""The marketing screens ported from the shadcn-examples collection render with their upstream content."""
import re

import pytest

from flask_basecoat.examples import examples_bp
from flask_basecoat.testing import make_app


@pytest.fixture(scope='module')
def client():
    app = make_app()
    if 'basecoat_examples' not in app.blueprints:
        app.register_blueprint(examples_bp, url_prefix='/examples')
    return app.test_client()


PLACEHOLDER = ['Coming Soon', 'This example is currently under development and will be shipped as soon as possible.']

SCREENS = {
    'coming-soon-page': ['Coming Soon', 'Stay Connected, Stay Updated!', 'Get Updates!', 'Send Now', 'Email Address',
                         'About', 'Feedback', 'days', 'seconds', 'aria-label="LinkedIn"'],
    'contact-page': ['Let&#39;s Talk About', 'Your Energy Goals', 'First Name', 'Last Name', 'Phone No', 'Your message',
                     'privacy policy', 'Send Your Message'],
    'course-detail': ['The Ultimate Guide to Usability Testing and UX Law', 'Course Curriculum', 'Enroll Now',
                      'Add to Favorites', 'Instructor', 'David Travis', '4.5 rating', 'Usability Testing:', 'UX Law:',
                      'Creating a UX Law Compliance Plan', '8:21', '0:23 / 45:32', 'All Videos', '24 Classes'],
    'help-center': ['How can we help you today?', 'Enter a question, topic or keyword', 'Go to FAQs', 'Check guides',
                    'Contact us', 'Most frequently asked questions', 'Is there a 14-days trial?',
                    'What kind of support do you offer?', 'Our average response time is under 2 hours.'],
    'pricing-tables': ['Pricing', 'Monthly', 'Yearly', 'Most Popular', 'Free', 'Tiny', 'Solo', 'Pro', '44% off',
                       'Billed at $372 /yr', 'Billed monthly', '7-day money-back guarantee', 'Additional Features:',
                       'Add more team members', 'Compare plans'],
    'cv-template': PLACEHOLDER,
    'hero-sections': PLACEHOLDER,
    'saas-landing-page': PLACEHOLDER,
}

SLOTS = {
    'coming-soon-page': {'input': 1, 'button': 1},
    'contact-page': {'input': 4, 'textarea': 1, 'checkbox': 1, 'button': 1},
    'course-detail': {'card': 5, 'badge': 3, 'avatar': 1, 'button': 22},
    'help-center': {'card': 3, 'input': 1, 'accordion': 1, 'accordion-item': 4},
    'pricing-tables': {'button': 10},
    'cv-template': {'empty': 1, 'empty-title': 1},
    'hero-sections': {'empty': 1, 'empty-title': 1},
    'saas-landing-page': {'empty': 1, 'empty-title': 1},
}

RAW_CONTROL = re.compile(r'<(button|input|select|textarea)\b(?![^>]*data-slot=)', re.I)


@pytest.mark.parametrize('slug', sorted(SCREENS))
def test_screen_renders_upstream_content(client, slug):
    resp = client.get(f'/examples/{slug}')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    for text in SCREENS[slug]:
        assert text in html, f'{slug}: missing {text!r}'


@pytest.mark.parametrize('slug', sorted(SCREENS))
def test_screen_uses_component_macros(client, slug):
    html = client.get(f'/examples/{slug}').get_data(as_text=True)
    assert not RAW_CONTROL.findall(html), f'{slug}: raw control outside the macros'
    for name, count in SLOTS[slug].items():
        assert html.count(f'data-slot="{name}"') >= count, f'{slug}: expected {count} {name}'


def test_screens_are_listed(client):
    html = client.get('/examples/').get_data(as_text=True)
    for slug in SCREENS:
        assert f'/examples/{slug}' in html
