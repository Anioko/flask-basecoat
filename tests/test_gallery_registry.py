import re
import sys
import textwrap
import unittest
from pathlib import Path

from app import create_app, db
from flask_basecoat import gallery_registry
from flask_basecoat.gallery_registry import _build, get_entry, load_entries

GOLDEN = Path(__file__).parent / 'golden' / 'registry'
# Components that existed before the registry; their pages were captured before the migration.
LEGACY_DOCS = ['button', 'badge', 'card', 'alert', 'avatar', 'input', 'textarea', 'label', 'accordion']
LEGACY_GALLERY_PAGES = ('button', 'textarea', 'label', 'input')


def only_legacy_links(html):
    """Drop gallery index links to components added after the migration so later entries do not break the golden."""
    def keep(line):
        m = re.search(r'/basecoat/gallery/([\w-]+)', line)
        return not m or m.group(1) in LEGACY_GALLERY_PAGES
    return '\n'.join(line for line in html.split('\n') if keep(line))


class RenderedPagesUnchangedTestCase(unittest.TestCase):
    """The gallery index and component docs pages render exactly as they did before the registry."""

    def setUp(self):
        self.app = create_app('testing')
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def get(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        return response.get_data(as_text=True)

    def test_gallery_index_identical(self):
        golden = (GOLDEN / 'gallery.html').read_bytes().decode()
        self.assertEqual(only_legacy_links(self.get('/basecoat/gallery')), only_legacy_links(golden))

    def test_docs_pages_identical(self):
        for name in LEGACY_DOCS:
            with self.subTest(component=name):
                golden = (GOLDEN / f'docs-{name}.html').read_bytes().decode()
                self.assertEqual(self.get(f'/docs/components/{name}'), golden)

    def test_gallery_pages_still_routed(self):
        for name in LEGACY_GALLERY_PAGES:
            with self.subTest(component=name):
                self.get(f'/basecoat/gallery/{name}')


class RegistryTestCase(unittest.TestCase):
    def test_existing_components_registered(self):
        names = [e.name for e in gallery_registry.get_entries()]
        for name in LEGACY_DOCS[:-1]:
            self.assertIn(name, names)
        self.assertEqual(get_entry('label').endpoint, 'gallery_label')
        self.assertIsNone(get_entry('accordion'))

    def test_index_order(self):
        header = [e.name for e in gallery_registry.gallery_entries('header')]
        self.assertEqual(header[:3], ['button', 'textarea', 'label'])
        self.assertIn('input', [e.name for e in gallery_registry.gallery_entries('nav')])

    def test_validation(self):
        with self.assertRaisesRegex(ValueError, 'unknown keys'):
            _build('x', {'name': 'x', 'colour': 1})
        with self.assertRaisesRegex(ValueError, 'does not match'):
            _build('x', {'name': 'y'})
        with self.assertRaisesRegex(ValueError, 'needs index_label'):
            _build('x', {'name': 'x', 'gallery_template': 'basecoat/gallery_x.html'})
        with self.assertRaisesRegex(ValueError, 'index_slot'):
            _build('x', {'name': 'x', 'index_slot': 'footer'})
        self.assertEqual(_build('radio_group', {'name': 'radio-group'}).endpoint, 'gallery_radio_group')

    def test_discovers_dropped_in_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / 'regpkg_probe'
            pkg.mkdir()
            (pkg / '__init__.py').write_text('')
            (pkg / 'zeta.py').write_text(textwrap.dedent("""
                ENTRY = {'name': 'zeta', 'gallery_template': 'basecoat/gallery_zeta.html', 'index_label': 'Zeta'}
            """))
            sys.path.insert(0, tmp)
            try:
                entries = load_entries('regpkg_probe')
            finally:
                sys.path.remove(tmp)
                sys.modules.pop('regpkg_probe', None)
                sys.modules.pop('regpkg_probe.zeta', None)
        self.assertEqual([e.name for e in entries], ['zeta'])
