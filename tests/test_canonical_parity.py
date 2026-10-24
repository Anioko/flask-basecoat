"""
Test that the registry-based gallery produces identical rendered output
to the canonical branch's explicit per-component routes.
"""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


def normalize_whitespace(html):
    """Normalize whitespace for comparison, preserving structure."""
    # Remove comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    # Normalize whitespace (collapse multiple spaces/newlines to single space)
    html = re.sub(r'\s+', ' ', html)
    # Remove leading/trailing whitespace
    html = html.strip()
    return html


def render_page(checkout_dir, path, venv_python):
    """Render a page from a specific checkout using a separate Python process."""
    script = f'''
import sys
sys.path.insert(0, "{checkout_dir}")
from app import create_app, db
app = create_app("testing")
with app.app_context():
    db.create_all()
    client = app.test_client()
    response = client.get("{path}")
    if response.status_code != 200:
        print(f"ERROR: Status {{response.status_code}}", file=sys.stderr)
        sys.exit(1)
    print(response.get_data(as_text=True))
'''
    result = subprocess.run(
        [str(venv_python), '-c', script],
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f'Failed to render {path} from {checkout_dir}:\n{result.stderr}')
    return result.stdout


class CanonicalParityTestCase(unittest.TestCase):
    """Compare rendered output from registry branch vs canonical branch."""

    @classmethod
    def setUpClass(cls):
        """Set up temporary worktree for canonical branch."""
        cls.repo_root = Path(__file__).parent.parent

        # Find the actual repo root and venv (handle worktrees)
        result = subprocess.run(['git', 'rev-parse', '--git-common-dir'],
                              cwd=cls.repo_root, capture_output=True, text=True, check=True)
        git_dir = Path(result.stdout.strip())
        cls.actual_repo_root = git_dir.parent if git_dir.name == '.git' else git_dir.parent.parent
        cls.venv_python = cls.actual_repo_root / 'venv' / 'bin' / 'python'

        if not cls.venv_python.exists():
            raise RuntimeError(f'venv Python not found at {cls.venv_python}')

        # Create temporary worktree for canonical branch
        cls.tmpdir = tempfile.mkdtemp(prefix='canonical-wt-')
        cls.canonical_path = Path(cls.tmpdir) / 'canonical'

        subprocess.run(
            ['git', 'worktree', 'add', str(cls.canonical_path), 'origin/feat/basecoat-shadcn-canonical'],
            cwd=cls.repo_root,
            check=True,
            capture_output=True
        )

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary worktree."""
        if hasattr(cls, 'canonical_path'):
            subprocess.run(
                ['git', 'worktree', 'remove', '--force', str(cls.canonical_path)],
                cwd=cls.repo_root,
                capture_output=True
            )

    def compare_pages(self, path, component_name=''):
        """Compare a page rendered from both checkouts."""
        registry_html = normalize_whitespace(
            render_page(self.repo_root, path, self.venv_python)
        )
        canonical_html = normalize_whitespace(
            render_page(self.canonical_path, path, self.venv_python)
        )

        if registry_html != canonical_html:
            # Find first difference for debugging
            for i, (r, c) in enumerate(zip(registry_html, canonical_html)):
                if r != c:
                    start = max(0, i - 100)
                    end = min(len(registry_html), i + 100)
                    context = component_name + ' ' if component_name else ''
                    self.fail(f'{context}HTML differs at position {i}.\n'
                             f'Registry: ...{registry_html[start:end]}...\n'
                             f'Canonical: ...{canonical_html[start:end]}...')

        self.assertEqual(registry_html, canonical_html,
                        f'{component_name} HTML differs between registry and canonical')

    def test_gallery_index_identical(self):
        """Gallery index page renders identically."""
        self.compare_pages('/basecoat/gallery', 'Gallery index')

    def test_component_gallery_pages_identical(self):
        """All component gallery pages render identically."""
        # All components that have gallery pages in canonical
        components = ['button', 'textarea', 'label', 'input', 'select']

        for component in components:
            with self.subTest(component=component):
                self.compare_pages(f'/basecoat/gallery/{component}', f'Gallery {component}')

    def test_component_docs_pages_identical(self):
        """All component docs pages render identically."""
        # All components that have docs pages
        components = ['button', 'badge', 'card', 'alert', 'avatar', 'input', 'textarea', 'label', 'select']

        for component in components:
            with self.subTest(component=component):
                self.compare_pages(f'/docs/components/{component}', f'Docs {component}')


if __name__ == '__main__':
    unittest.main()
