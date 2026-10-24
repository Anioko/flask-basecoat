"""Unit tests for the slot attribute engine and the tailwind-merge port."""
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

from flask_basecoat import slots as S  # noqa: E402
from flask_basecoat.twmerge import merge  # noqa: E402


def attrs(rendered):
    """Parse the rendered attribute string into a dict."""
    import html, re
    return {k: html.unescape(v) for k, v in re.findall(r' ([\w:-]+)="([^"]*)"', str(rendered.attributes))}


def test_button_default_matches_upstream_recipe():
    r = S.slot('button', {})
    a = attrs(r)
    assert r.tag == 'button'
    assert a['data-slot'] == 'button' and a['data-variant'] == 'default' and a['data-size'] == 'default'
    assert 'cn-button' in a['class'] and 'cn-button-variant-default' in a['class'] and 'cn-button-size-default' in a['class']
    assert 'type' not in a  # React does not add type=button to <Button>


def test_button_variants_and_link():
    a = attrs(S.slot('button', {'variant': 'destructive', 'size': 'icon-sm', 'href': '/x'}))
    assert 'cn-button-variant-destructive' in a['class'] and 'cn-button-size-icon-sm' in a['class']
    assert a['href'] == '/x'
    assert S.slot('button', {'href': '/x'}).tag == 'a'


def test_tailwind_merge_drops_conflicting_recipe_classes():
    a = attrs(S.slot('input', {}, class_='w-fit'))
    assert 'w-fit' in a['class'].split() and 'w-full' not in a['class'].split()
    assert merge(['h-svh', 'h-[calc(100svh-var(--x))]!']) == 'h-svh h-[calc(100svh-var(--x))]!'
    assert merge(['inline-flex shrink-0', 'flex-1']) == 'inline-flex flex-1'
    assert merge(['p-4', 'px-2']) == 'p-4 px-2'
    assert merge(['px-2', 'p-4']) == 'p-4'


def test_open_state_contract():
    closed = attrs(S.slot('dialog-trigger', {}))
    assert closed['data-state'] == 'closed' and closed['aria-expanded'] == 'false' and closed['aria-haspopup'] == 'dialog'
    opened = attrs(S.slot('dialog-trigger', {'open': True}))
    assert opened['data-state'] == 'open' and opened['aria-expanded'] == 'true'
    content = attrs(S.slot('dialog-content', {}))
    assert content['role'] == 'dialog' and content['aria-modal'] == 'true' and content['data-state'] == 'closed'
    acc = attrs(S.slot('accordion-content', {}))
    assert acc['data-state'] == 'closed' and 'hidden' in acc
    tooltip = attrs(S.slot('tooltip-trigger', {}))
    assert tooltip['data-state'] == 'closed' and 'aria-expanded' not in tooltip


def test_checked_and_pressed_contracts():
    cb = attrs(S.slot('checkbox', {'checked': True}))
    assert cb['role'] == 'checkbox' and cb['aria-checked'] == 'true' and cb['data-state'] == 'checked' and cb['value'] == 'on'
    sw = attrs(S.slot('switch', {}))
    assert sw['role'] == 'switch' and sw['aria-checked'] == 'false' and sw['data-state'] == 'unchecked'
    tg = attrs(S.slot('toggle', {'pressed': True}))
    assert tg['aria-pressed'] == 'true' and tg['data-state'] == 'on' and 'data-variant' not in tg
    tgi = attrs(S.slot('toggle-group-item', {'pressed': True}))
    assert tgi['role'] == 'radio' and tgi['aria-checked'] == 'true'
    tgm = attrs(S.slot('toggle-group-item', {'pressed': False, 'multiple': True}))
    assert tgm['aria-pressed'] == 'false' and 'role' not in tgm


def test_tabs_contract():
    t = attrs(S.slot('tabs-trigger', {'active': True}))
    assert t['role'] == 'tab' and t['aria-selected'] == 'true' and t['data-state'] == 'active' and t['data-orientation'] == 'horizontal'
    c = attrs(S.slot('tabs-content', {}))
    assert c['role'] == 'tabpanel' and c['data-state'] == 'inactive' and 'hidden' in c


def test_disabled_and_invalid():
    f = attrs(S.slot('field', {'invalid': True, 'disabled': True}))
    assert f['data-invalid'] == 'true' and f['data-disabled'] == 'true' and 'aria-invalid' not in f
    i = attrs(S.slot('input', {'invalid': True, 'disabled': True}))
    assert i['aria-invalid'] == 'true' and 'disabled' in i and 'data-disabled' not in i


def test_virtual_wrapper_has_no_slot():
    r = S.slot('dropdown-menu', {})
    assert r.virtual and 'data-slot' not in attrs(r) and attrs(r)['data-fb'] == 'dropdown-menu'


def test_svg_part_renders_icon():
    r = S.slot('accordion-trigger-icon', {})
    assert r.tag == 'svg' and 'lucide-chevron-down' in attrs(r)['class'] and '<path' in str(r.inner)


def test_every_recipe_slot_has_a_tag():
    recipes = json.loads((ROOT / 'flask_basecoat/data/recipes.json').read_text(encoding='utf8'))
    for name in recipes:
        assert S.tag_for(name), name


@pytest.mark.parametrize('name', ['button', 'card', 'badge', 'tabs-trigger', 'checkbox', 'select-trigger', 'sidebar-menu-button'])
def test_recipe_classes_are_subset_of_rendered(name):
    rec = S.recipe(name)
    a = attrs(S.slot(name, {}))
    for c in rec.get('base_classes', '').split():
        assert c in a['class'].split(), (name, c)
