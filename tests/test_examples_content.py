"""The content screens ported from shadcn-examples render, carry their upstream headings and use only component macros."""
import re
import unittest
from html import unescape

from flask_basecoat.testing import make_app
from flask_basecoat.examples import examples_bp

SCREENS = {
    'blog-page': ['Unlocking Business Efficiency with SaaS Solutions', 'Other featured posts', 'Recent Posts', 'All Posts',
                  'Beyond Aesthetics: The Power of Emotional UX Design'],
    'blog-detail-page': ['The Best Way to Write a Recurring Email Newsletter', 'by Esther Howard', 'Share this', 'Comments (',
                         'Post Comment', 'Sarah Johnson', 'Emily Rodriguez'],
    'changelog-page': ["What's new?", 'Version 4.2.92', 'Version 4.2.88', 'Version 4.2.85', 'Bugfixes', 'New Features'],
    'updates-page': ['Updates', 'Last update:', 'July 2, 2025', 'Empty States Pages', 'MyApp First Launch',
                     'Have suggestions for new features?', 'Contact Us'],
    'roadmap': ['Product Roadmap', 'Roadmap', 'Completed', 'In Progress', 'Planned', 'Future', 'Next Generation Features',
                '+3 more features'],
    'timeline': ['Basic', 'Advance', 'Breakfast - 09:00', 'Angelina Gotelli', 'added tags', 'Live Issue'],
    'activity-feed': ['Activity log', 'Show mentioned only', 'SUNDAY, 06 MARCH', 'SATURDAY, 05 MARCH', 'document.csv',
                      'Alvin Moreno'],
    'projects-list': ['Projects Board', 'List of your ongoing projects', 'New Project', 'NFT Marketplace App', '78%',
                      '6 week left'],
    'playground': ['Playground', 'Load a preset...', 'Save preset', 'View code', 'Share preset', 'Content filter preferences',
                   'Are you absolutely sure?', 'Mode', 'Temperature', 'Maximum Length', 'Top P', 'Instructions'],
}

# Minimum number of each component kind the upstream screen uses.
SLOTS = {
    'blog-page': {'badge': 1, 'button': 1, 'avatar': 3},
    'blog-detail-page': {'badge': 1, 'avatar': 4, 'button': 10, 'textarea': 1},
    'changelog-page': {'badge': 5},
    'updates-page': {'card': 9, 'badge': 10, 'button': 10, 'card-action': 9},
    'roadmap': {'card': 6, 'badge': 1},
    'timeline': {'avatar': 3, 'badge': 3, 'card': 1},
    'activity-feed': {'avatar': 6, 'badge': 2, 'switch': 1, 'button': 1},
    'projects-list': {'card': 8, 'badge': 8, 'button': 9},
    'playground': {'tabs': 1, 'tabs-trigger': 3, 'tabs-content': 3, 'dialog-content': 3, 'alert-dialog-content': 1,
                   'popover-content': 3, 'command': 2, 'command-item': 17, 'hover-card-content': 5, 'slider': 3,
                   'dropdown-menu-content': 1, 'switch': 1, 'textarea': 5, 'input': 2, 'separator': 1},
}

# Slugs whose URL is served by an earlier, hand-written screen of the same name.
SHADOWED = {'playground'}

RAW_CONTROL = re.compile(r'<(button|input|select|textarea)\b(?![^>]*data-slot=)', re.I)


class ContentExamplesTest(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        if 'basecoat_examples' not in self.app.blueprints:
            self.app.register_blueprint(examples_bp, url_prefix='/examples')
        self.client = self.app.test_client()

    def html(self, slug):
        r = self.client.get(f'/examples/{slug}')
        self.assertEqual(r.status_code, 200, slug)
        if slug in SHADOWED:
            # An older screen owns this URL, so the ported template is rendered directly.
            from flask import render_template
            with self.app.test_request_context(f'/examples/{slug}'):
                return render_template(f'examples/ported/{slug}.html')
        return r.get_data(as_text=True)

    def test_screens_render_with_upstream_headings(self):
        for slug, headings in SCREENS.items():
            with self.subTest(slug=slug):
                html = unescape(self.html(slug))
                for text in headings:
                    self.assertIn(text, html)

    def test_screens_use_component_macros(self):
        for slug, kinds in SLOTS.items():
            with self.subTest(slug=slug):
                html = self.html(slug)
                for kind, minimum in kinds.items():
                    self.assertGreaterEqual(html.count(f'data-slot="{kind}"'), minimum, kind)

    def test_no_raw_controls(self):
        for slug in SCREENS:
            with self.subTest(slug=slug):
                self.assertEqual(RAW_CONTROL.findall(self.html(slug)), [])

    def test_screens_are_listed(self):
        html = self.client.get('/examples/').get_data(as_text=True)
        for slug in SCREENS:
            self.assertIn(f'/examples/{slug}', html)


if __name__ == '__main__':
    unittest.main()
