"""The page check passes a shadcn original and catches each kind of departure from shadcn."""
import importlib.util
import pathlib

import pytest
from lxml import html as lxml_html

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_page', ROOT / 'compliance' / 'scripts' / 'check_page.py')
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)
LIMITS = {'regions': 6, 'stat_cards': 4, 'charts': 2, 'tables': 1}


def run(path):
    text, _ = cp.load(path)
    original = lxml_html.fromstring(cp.golden_path('dashboard-01').read_text(encoding='utf8'))
    return cp.check(lxml_html.fromstring(text), original, 'dashboard-01', LIMITS)


def test_the_original_passes_at_100_percent():
    res, score, counts = run('/basecoat/blocks/dashboard-01')
    assert {k: v for k, v in res.items() if v} == {}
    assert score == 100.0


def mutate(tmp_path, old, new):
    text, _ = cp.load('/basecoat/blocks/dashboard-01')
    assert old in text, old
    f = tmp_path / 'page.html'
    f.write_text(text.replace(old, new, 1), encoding='utf8')
    return run(str(f))


CARD = 'data-slot="card" class="'


@pytest.mark.parametrize('old,new,check', [
    (CARD, CARD + 'bg-blue-500 ', 'colours'),                 # palette colour on a component
    (CARD, CARD + 'shadow-2xl ', 'recipes'),                   # styling a component outside its recipe
    (CARD, 'style="color:#ff0000" ' + CARD, 'colours'),        # raw colour in a style
    (CARD, 'style="margin-top:3px" ' + CARD, 'styles'),        # authored inline style
    ('<main', '<button type="button">Raw</button><main', 'components'),  # raw control
    ('data-slot="card-content"', 'data-slot="card-content"><div data-slot="card" class="cn-card group/card flex flex-col"></div', 'structure'),  # card in a card
    ('data-slot="sidebar-header"', 'data-slot="sidebar-headerx"', 'components'),  # unknown part
])
def test_departures_are_caught(tmp_path, old, new, check):
    res, score, _ = mutate(tmp_path, old, new)
    assert res[check], f'{check} did not catch {new!r}'


def test_density_limit(tmp_path):
    text, _ = cp.load('/basecoat/blocks/dashboard-01')
    extra = '<div data-slot="card" class="cn-card group/card flex flex-col"></div>' * 3
    f = tmp_path / 'page.html'
    f.write_text(text.replace('<main', '<main', 1).replace('data-slot="card" class="', 'data-slot="card" class="', 1).replace('</main>', extra + '</main>', 1), encoding='utf8')
    res, _, counts = run(str(f))
    assert counts['regions'] > 6 and res['density']


BLOCKS = sorted(p.stem for p in (ROOT / 'compliance' / 'golden' / 'out' / 'blocks').glob('*.html') if '.' not in p.stem)


@pytest.mark.parametrize('block', BLOCKS)
def test_every_shadcn_block_passes_against_itself(block):
    text, _ = cp.load(f'/basecoat/blocks/{block}')
    original = lxml_html.fromstring(cp.golden_path(block).read_text(encoding='utf8'))
    res, score, _ = cp.check(lxml_html.fromstring(text), original, block, LIMITS)
    assert {k: v[:3] for k, v in res.items() if v} == {}
    assert score == 100.0


def test_reference_portfolio_page_is_shadcn_composed():
    res, score, counts = run('/examples/reference/portfolio')
    assert {k: v[:3] for k, v in res.items() if v} == {}
    assert score == 100.0
    assert counts['regions'] <= 6 and counts['chart_cards'] == 1 and counts['tables'] == 1
