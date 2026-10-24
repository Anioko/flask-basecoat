"""Every shadcn/ui registry component and block is covered, renders, matches the upstream DOM and carries its recipe.

These tests drive the same checks as compliance/scripts and are parametrised over the pinned registry index,
so a missing page, macro or regression in any component fails the suite by name.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'compliance' / 'scripts'))

import check_dom  # noqa: E402
import check_recipes  # noqa: E402

REGISTRY = json.loads((ROOT / 'compliance/upstream/shadcn/registry/index.json').read_text(encoding='utf8'))
COMPONENTS = sorted(i['name'] for i in REGISTRY if i.get('type') == 'registry:ui')
BLOCKS = sorted(p.name for p in (ROOT / 'compliance/upstream/shadcn/radix/blocks').iterdir()
                if p.is_dir() and p.name.split('-')[0] in ('dashboard', 'login', 'signup', 'sidebar'))
TEMPLATES = ROOT / 'flask_basecoat/templates/basecoat'


@pytest.fixture(scope='module')
def client():
    from flask_basecoat.testing import make_app
    app = make_app()
    with app.test_client() as c:
        yield c


def test_registry_is_fully_covered():
    missing_macros = [n for n in COMPONENTS if not (TEMPLATES / f'{n}.html').exists()]
    missing_pages = [n for n in COMPONENTS if not (TEMPLATES / 'pages' / 'components' / f'{n}.html').exists()]
    missing_blocks = [n for n in BLOCKS if not (TEMPLATES / 'pages' / 'blocks' / f'{n}.html').exists()]
    assert len(COMPONENTS) == 65
    assert len(BLOCKS) == 27
    assert not missing_macros, missing_macros
    assert not missing_pages, missing_pages
    assert not missing_blocks, missing_blocks


def test_barrel_exports_every_macro():
    barrel = (TEMPLATES / 'index.html').read_text(encoding='utf8')
    recipes = json.loads((ROOT / 'flask_basecoat/data/recipes.json').read_text(encoding='utf8'))
    missing = [s for s in recipes if f"set {s.replace('-', '_')} =" not in barrel]
    assert not missing, missing


@pytest.mark.parametrize('name', COMPONENTS)
def test_component_page_renders(client, name):
    r = client.get(f'/basecoat/components/{name}')
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert 'class="style-vega' in body
    assert 'data-slot=' in body


@pytest.mark.parametrize('name', BLOCKS)
def test_block_page_renders(client, name):
    r = client.get(f'/basecoat/blocks/{name}')
    assert r.status_code == 200


@pytest.mark.parametrize('name', COMPONENTS)
def test_component_dom_matches_upstream(name):
    result = check_dom.check('components', name)
    assert result['status'] == 'pass', result.get('problems', result)[:10]


@pytest.mark.parametrize('name', BLOCKS)
def test_block_dom_matches_upstream(name):
    result = check_dom.check('blocks', name)
    assert result['status'] == 'pass', result.get('problems', result)[:10]


@pytest.mark.parametrize('name', COMPONENTS)
def test_component_classes_follow_recipes(name):
    recipes = check_recipes
    result = recipes.check_page('components', name)
    assert result['status'] == 'pass', result.get('problems', result)[:10]


@pytest.mark.parametrize('name', BLOCKS)
def test_block_classes_follow_recipes(name):
    result = check_recipes.check_page('blocks', name)
    assert result['status'] == 'pass', result.get('problems', result)[:10]


def test_gallery_index_lists_everything(client):
    r = client.get('/basecoat/')
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    for n in COMPONENTS + BLOCKS:
        assert f'>{n}<' in body, n
