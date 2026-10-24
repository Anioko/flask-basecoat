"""Unit tests for the select macro: every variant, size and state renders the Basecoat classes."""
import re

import pytest
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

TEMPLATES_PATH = Path(__file__).parent.parent / "flask_basecoat/templates/basecoat"
SHADCN_SELECT = Path("/tmp/shadcn-fork/components/ui/select.tsx")

env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))

OPTIONS = "[('apple', 'Apple'), ('banana', 'Banana'), {'value': 'cherry', 'label': 'Cherry', 'disabled': True}]"


def render(call, imports="select, select_group, select_item, select_separator, select_label"):
    source = "{% from 'select.html' import " + imports + " %}" + call
    return BeautifulSoup(env.from_string(source).render(), "html.parser")


def trigger_of(soup):
    return soup.find(attrs={"data-slot": "select-trigger"})


def test_wrapper_uses_basecoat_select_structure():
    soup = render("{{ select(name='fruit', id='f', options=" + OPTIONS + ", placeholder='Pick') }}")
    root = soup.find(attrs={"data-slot": "select"})
    assert "select" in root["class"]
    assert [c.name for c in root.find_all(recursive=False)] == ["button", "div", "input"]
    assert trigger_of(soup).parent is root
    popover = root.find(attrs={"data-popover": True})
    assert popover["aria-hidden"] == "true"
    assert popover.find(attrs={"role": "listbox"}) is not None
    assert root.find("input")["type"] == "hidden"
    assert root.find("input")["name"] == "fruit"


@pytest.mark.parametrize("size,height", [("default", "data-[size=default]:h-9"), ("sm", "data-[size=sm]:h-8")])
def test_size_variants(size, height):
    soup = render("{{ select(name='x', id='x', options=" + OPTIONS + ", size='" + size + "') }}")
    trigger = trigger_of(soup)
    assert trigger["data-size"] == size
    assert height in trigger["class"]
    assert "rounded-md" in trigger["class"] and "shadow-xs" in trigger["class"]


def test_trigger_aria_matches_shadcn_combobox():
    soup = render("{{ select(name='x', id='x', options=" + OPTIONS + ", label='Fruit') }}")
    trigger = trigger_of(soup)
    listbox = soup.find(attrs={"role": "listbox"})
    assert trigger["role"] == "combobox"
    assert trigger["aria-haspopup"] == "listbox"
    assert trigger["aria-expanded"] == "false"
    assert trigger["aria-controls"] == listbox["id"]
    assert trigger["aria-label"] == "Fruit"
    assert listbox["aria-labelledby"] == trigger["id"]


def test_placeholder_state():
    soup = render("{{ select(name='x', id='x', options=" + OPTIONS + ", placeholder='Pick a fruit') }}")
    trigger = trigger_of(soup)
    assert trigger.has_attr("data-placeholder")
    assert trigger.find(attrs={"data-slot": "select-value"}).get_text() == "Pick a fruit"
    assert soup.find("input")["value"] == ""
    assert not soup.find_all(attrs={"aria-selected": True})


def test_selected_value_state():
    soup = render("{{ select(name='x', id='x', options=" + OPTIONS + ", value='banana', placeholder='Pick') }}")
    trigger = trigger_of(soup)
    assert not trigger.has_attr("data-placeholder")
    assert trigger.find(attrs={"data-slot": "select-value"}).get_text() == "Banana"
    assert soup.find("input")["value"] == "banana"
    selected = soup.find_all(attrs={"aria-selected": "true"})
    assert [o["data-value"] for o in selected] == ["banana"]


def test_disabled_state():
    soup = render("{{ select(name='x', id='x', options=" + OPTIONS + ", disabled=True) }}")
    assert trigger_of(soup).has_attr("disabled")
    assert "disabled:opacity-50" in trigger_of(soup)["class"]
    assert soup.find("input").has_attr("disabled")


def test_invalid_and_required_states():
    soup = render("{{ select(name='x', id='x', options=" + OPTIONS + ", invalid=True, required=True) }}")
    trigger = trigger_of(soup)
    assert trigger["aria-invalid"] == "true"
    assert trigger["aria-required"] == "true"
    assert "aria-invalid:border-destructive" in trigger["class"]


def test_options_render_as_items_with_disabled_state():
    soup = render("{{ select(name='x', id='x', options=" + OPTIONS + ") }}")
    items = soup.find_all(attrs={"data-slot": "select-item"})
    assert [i["role"] for i in items] == ["option"] * 3
    assert [i["data-value"] for i in items] == ["apple", "banana", "cherry"]
    assert items[2]["aria-disabled"] == "true"
    assert "focus:bg-accent" in items[0]["class"]
    ids = [i["id"] for i in items]
    assert len(set(ids)) == 3


def test_caller_slots_groups_labels_separators():
    soup = render(
        "{% call select(name='tz', id='tz', placeholder='Zone') %}"
        "{% call select_group(label='Americas', id='g1') %}{{ select_item(value='est', content='EST') }}{% endcall %}"
        "{{ select_separator() }}"
        "{% call select_group(label='Europe', id='g2') %}{{ select_item(value='cet', content='CET') }}{% endcall %}"
        "{% endcall %}"
    )
    groups = soup.find_all(attrs={"data-slot": "select-group"})
    assert [g["role"] for g in groups] == ["group", "group"]
    label = groups[0].find(attrs={"data-slot": "select-label"})
    assert groups[0]["aria-labelledby"] == label["id"]
    assert "text-muted-foreground" in label["class"] and "text-xs" in label["class"]
    separator = soup.find(attrs={"data-slot": "select-separator"})
    assert separator["role"] == "separator"
    assert "bg-border" in separator["class"] and "h-px" in separator["class"]
    assert [i["data-value"] for i in soup.find_all(attrs={"role": "option"})] == ["est", "cet"]


def test_extra_class_is_appended_to_trigger():
    soup = render("{{ select(name='x', id='x', options=" + OPTIONS + ", class='w-[180px]') }}")
    assert "w-[180px]" in trigger_of(soup)["class"]


def test_no_raw_colours_or_inline_styles():
    source = (TEMPLATES_PATH / "select.html").read_text()
    assert "macro select(" in source
    assert "style=" not in source
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgb|hsl|oklch)\(|-(?:red|blue|green|gray|slate|zinc)-\d{2,3}", source)
    assert set(re.findall(r"shadow-[\w-]+", source)) <= {"shadow-xs", "shadow-md"}


@pytest.mark.skipif(not SHADCN_SELECT.exists(), reason="shadcn fork not cloned")
def test_item_label_separator_classes_equal_shadcn():
    tsx = SHADCN_SELECT.read_text()

    def shadcn_classes(slot):
        m = re.search(r'data-slot="' + slot + r'"\s*className=\{cn\(\s*"([^"]+)"', tsx)
        assert m, slot
        return sorted(m.group(1).split())

    soup = render(
        "{% call select(name='x', id='x', placeholder='p') %}"
        "{% call select_group(label='L', id='g') %}{{ select_item(value='a', content='A') }}{% endcall %}"
        "{{ select_separator() }}{% endcall %}"
    )
    for slot in ("select-item", "select-label", "select-separator"):
        actual = sorted(soup.find(attrs={"data-slot": slot})["class"])
        assert actual == shadcn_classes(slot), slot
