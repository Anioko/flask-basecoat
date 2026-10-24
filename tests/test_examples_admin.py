"""The admin example screens (dashboards, file managers, point of sale, tasks, todo list) render with their upstream content."""
import json
import pathlib
import re
import unittest
from html import unescape

from flask_basecoat.testing import make_app
from flask_basecoat.examples import examples_bp, ported

HEADINGS = {
    'admin-dashboard': ['Acme Inc.', 'Documents', 'Total Revenue', 'New Customers', 'Active Accounts', 'Growth Rate', 'Total Visitors',
                        'Outline', 'Past Performance', 'Key Personnel', 'Focus Documents', 'Customize Columns', 'Cover page', 'Eddie Lake'],
    'payment-admin-dashboard': ['Invoice', 'Total Invoices', 'Paid Invoices', 'Pending Invoices', 'Total Receivables', 'Cash Flow',
                                'All Invoices', 'Robert Baratheon', 'Dianne Russell', 'Darrell Steward'],
    'file-manager-admin-dashboard': ['File Manager', 'All files', 'Recently modified', 'Storage usage', 'Get more space for your files',
                                     'Campaign Analysis - Q3.docx', 'landscape_003.jpg', 'Help Center'],
    'dashboard-layouts': ['Coming Soon', 'This example is currently under development and will be shipped as soon as possible.'],
    'file-manager': ['File Manager', 'Upload Files', 'Rows per page', 'Design', 'Brand Styles Guide', 'File Details'],
    'pos-app': ['CHANNELS', 'Categories', 'Draft #001', 'Duck Salad', 'Sashimi', 'Subtotal', 'Checkout $'],
    'tasks': ['Welcome back!', 'Filter tasks...', 'Status', 'Priority', 'TASK-8782', 'Toggle columns', 'Rows per page', 'Page 1 of 10'],
    'task-detail': ['Workplace Safety Guide 2024', 'Assignee:', 'Attachment', 'Description', 'Phase 1', 'Task - Phase 1',
                    'Include Visuals and Checklists'],
    'todo-list-app': ['Launch Clever dashboard theme', 'New tasks', 'Do today', 'In progress', 'Important', 'New product', 'Delayed'],
}
# Older hand-written screens own these URLs under /examples/, so the port is reached through the `ported` view.
SHADOWED = {'tasks', 'task-detail', 'file-manager'}
RAW_CONTROL = re.compile(r'<(button|input|select|textarea)\b[^>]*>', re.I)


class AdminExamplesTest(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        if 'basecoat_examples' not in self.app.blueprints:
            self.app.register_blueprint(examples_bp, url_prefix='/examples')
        if 'ported_direct' not in self.app.view_functions:
            self.app.add_url_rule('/ported/<slug>', 'ported_direct', ported)
        self.client = self.app.test_client()

    def get(self, slug, query=''):
        r = self.client.get(f'/ported/{slug}{query}')
        self.assertEqual(r.status_code, 200, slug)
        return r.get_data(as_text=True)

    def test_every_screen_renders_with_its_headings(self):
        for slug, headings in HEADINGS.items():
            with self.subTest(slug=slug):
                html = unescape(self.get(slug))
                text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html))
                for h in headings:
                    self.assertTrue(h in text or f'"{h}"' in html, f'{slug}: {h!r} missing')

    def test_unshadowed_screens_are_served_under_examples(self):
        for slug in set(HEADINGS) - SHADOWED:
            with self.subTest(slug=slug):
                self.assertEqual(self.client.get(f'/examples/{slug}').status_code, 200)

    def test_no_raw_controls(self):
        for slug in HEADINGS:
            with self.subTest(slug=slug):
                html = re.sub(r'<script.*?</script>', '', self.get(slug), flags=re.S)
                raw = [m.group(0)[:80] for m in RAW_CONTROL.finditer(html) if 'data-slot=' not in m.group(0)]
                self.assertEqual(raw, [], slug)

    def test_screens_are_listed_with_metadata(self):
        html = self.client.get('/examples/').get_data(as_text=True)
        folder = pathlib.Path(examples_bp.root_path) / 'templates' / 'examples' / 'ported'
        for slug in HEADINGS:
            meta = json.loads((folder / f'{slug}.json').read_text(encoding='utf8'))
            self.assertEqual(meta['id'], slug)
            self.assertTrue(meta['title'] and meta['description'] and meta['tags'])
            self.assertIn(f'/examples/{slug}', html)

    def test_admin_table_carries_every_upstream_row(self):
        html = self.get('admin-dashboard')
        self.assertEqual(len(re.findall(r'<button[^>]*data-fb-open="section-viewer"', html)), 68)
        self.assertIn('Page 1 of 7', html)

    def test_tasks_table_carries_every_task(self):
        html = self.get('tasks')
        self.assertEqual(len(re.findall(r'<tr[^>]*data-row="TASK-', html)), 100)

    def test_file_manager_opens_folders_from_the_query(self):
        html = self.get('file-manager', '?path=Design')
        self.assertIn('UI Components', html)
        self.assertIn('Mockups', html)
        self.assertIn('data-slot="breadcrumb"', html)
        self.assertIn('This folder is empty.', self.get('file-manager', '?path=Design/UI%20Components'))

    def test_pos_totals_are_computed(self):
        html = self.get('pos-app')
        self.assertIn('111.00$', html)
        self.assertIn('11.10$', html)
        self.assertIn('122.10$', html)


if __name__ == '__main__':
    unittest.main()
