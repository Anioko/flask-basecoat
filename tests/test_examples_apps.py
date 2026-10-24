"""The app screens ported from the shadcn-examples collection render, carry their upstream headings and use only
component macros for controls."""
import re
import unittest

from flask import render_template

from flask_basecoat.testing import make_app
from flask_basecoat.examples import examples_bp

SCREENS = {
    'mail-app': ['Inbox', 'Alicia Koch', 'Drafts', 'Promotions', 'William Smith', 'Meeting Tomorrow', 'No message selected',
                 'Snooze until', 'Mark as unread', 'Mute this thread'],
    'chat-app': ['Chat', 'Personal', 'Groups', 'Shannon Baker', 'last seen recently', 'New chat', 'Will do. Appreciate it!'],
    'ai-chat': ['New Chat', 'Recent Chats', 'Welcome, John Doe', 'May I be of assistance today?', 'Help &amp; Support',
                'Do you have emotions?'],
    'video-call-chat': ['Coming Soon', 'This example is currently under development'],
    'music-app': ['Maise', 'Vladimir Raksha', 'Browse', 'My Playlists', 'More Like Lady Gaga', 'Shallow', 'Lady Gaga'],
    'podcast-app': ['Coming Soon', 'This example is currently under development'],
    'social-media': ['Your Communities', 'Create Post', 'Who to follow', 'Trending Topics', 'Moyo Shiro', '#SpaceExploration'],
    'event-calendar': ['Today', 'New event', 'Create Event', 'Start Date', 'End Time', 'All day', 'Etiquette', 'Agenda'],
    'kanban-board': ['Backlog', 'In Progress', 'Done', 'Add authentication', 'Initial commit', 'Frank White'],
    'sortable-cards': ['Hero Image', 'Feature Highlight', 'Background Music', '15.7 MB'],
}
SLOTS = {
    'mail-app': {'resizable-panel': 3, 'resizable-handle': 2, 'tabs-trigger': 2, 'tooltip-content': 7, 'select-item': 3,
                 'dropdown-menu-item': 4, 'switch': 1, 'textarea': 1, 'calendar': 1, 'badge': 21},
    'chat-app': {'avatar': 9, 'input': 1, 'button': 4},
    'ai-chat': {'scroll-area': 2, 'input': 2, 'avatar': 3},
    'video-call-chat': {'empty': 1, 'empty-icon': 1},
    'music-app': {'card': 12, 'scroll-area': 1, 'separator': 1},
    'podcast-app': {'empty': 1},
    'social-media': {'card': 2, 'card-title': 2, 'avatar': 6, 'input': 1},
    'event-calendar': {'dialog-content': 1, 'dropdown-menu-item': 4, 'dropdown-menu-shortcut': 4, 'select-trigger': 2,
                       'calendar': 2, 'checkbox': 1, 'radio-group-item': 6, 'label': 8, 'textarea': 1},
    'kanban-board': {'kanban-column': 3, 'kanban-item': 7, 'badge': 10},
    'sortable-cards': {'sortable-item': 9, 'sortable-item-handle': 9, 'badge': 9},
}
CONTROL = re.compile(r'<(button|input|select|textarea)\b[^>]*>', re.I)


class ExamplesAppsTest(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        if 'basecoat_examples' not in self.app.blueprints:
            self.app.register_blueprint(examples_bp, url_prefix='/examples')
        self.client = self.app.test_client()

    def render(self, slug):
        """Render through the /examples/<slug> route; an older screen owns /examples/ai-chat, so that one renders directly."""
        r = self.client.get(f'/examples/{slug}')
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        if 'examples/ported' not in html and slug == 'ai-chat':
            with self.app.test_request_context(f'/examples/{slug}'):
                html = render_template(f'examples/ported/{slug}.html')
        return html

    def test_screens_render_with_upstream_text(self):
        for slug, headings in SCREENS.items():
            with self.subTest(slug=slug):
                html = self.render(slug)
                self.assertIn('class="style-vega', html)
                for text in headings:
                    self.assertIn(text, html)

    def test_component_inventory(self):
        for slug, slots in SLOTS.items():
            with self.subTest(slug=slug):
                html = self.render(slug)
                for slot, minimum in slots.items():
                    self.assertGreaterEqual(html.count(f'data-slot="{slot}"'), minimum, slot)

    def test_no_raw_controls(self):
        for slug in SCREENS:
            with self.subTest(slug=slug):
                html = self.render(slug)
                for tag in CONTROL.finditer(html):
                    if 'type="hidden"' in tag.group(0):
                        continue
                    self.assertIn('data-slot=', tag.group(0), tag.group(0)[:120])

    def test_no_raw_palette_colours(self):
        palette = re.compile(r'\b(?:bg|text|border|from|to|via)-(?:slate|gray|zinc|blue|red|green|sky|amber|rose|pink|teal|orange|indigo|violet|emerald|lime|yellow)-\d{2,3}\b')
        for slug in SCREENS:
            with self.subTest(slug=slug):
                self.assertIsNone(palette.search(self.render(slug)))

    def test_screens_are_listed(self):
        html = self.client.get('/examples/').get_data(as_text=True)
        for title in ['Mail App', 'Chat App', 'Music App', 'Social Media', 'Event Calendar', 'Kanban Board', 'Sortable Cards']:
            self.assertIn(title, html)


if __name__ == '__main__':
    unittest.main()
