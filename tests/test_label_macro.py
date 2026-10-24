"""Unit tests for the label macro: shadcn classes, slot, for/id and call block."""
import re
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

TEMPLATES = Path(__file__).parent.parent / "flask_basecoat/templates"
TSX = Path("/tmp/shadcn-fork/components/ui/label.tsx")

BASE_CLASSES = (
    "flex items-center gap-2 text-sm leading-none font-medium select-none "
    "group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50 "
    "peer-disabled:cursor-not-allowed peer-disabled:opacity-50"
).split()


@pytest.fixture(scope="module")
def env():
    return Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=True)


def render(env, source):
    tpl = env.from_string("{% from 'basecoat/label.html' import label %}" + source)
    return BeautifulSoup(tpl.render(), "html.parser").find(attrs={"data-slot": "label"})


def test_default_has_every_shadcn_class_and_slot(env):
    el = render(env, "{{ label(content='Email') }}")
    assert el.name == "label"
    assert el["data-slot"] == "label"
    assert sorted(el["class"]) == sorted(BASE_CLASSES)
    assert el.text == "Email"
    assert not el.has_attr("for") and not el.has_attr("id")


@pytest.mark.skipif(not TSX.exists(), reason="shadcn fork not cloned")
def test_default_classes_equal_shadcn_source(env):
    cn = re.search(r'className=\{cn\(\s*"([^"]+)"', TSX.read_text())
    assert sorted(render(env, "{{ label() }}")["class"]) == sorted(cn.group(1).split())


def test_for_and_id_are_forwarded(env):
    el = render(env, "{{ label(content='Name', for='name', id='name-label') }}")
    assert el["for"] == "name" and el["id"] == "name-label"


def test_extra_class_is_appended_and_base_kept(env):
    el = render(env, "{{ label(class='text-destructive') }}")
    assert "text-destructive" in el["class"]
    assert set(BASE_CLASSES) <= set(el["class"])


def test_call_block_slot_holds_children(env):
    el = render(env, "{% call label(for='x') %}Accept <b>terms</b>{% endcall %}")
    assert el.find("b").text == "terms"
    assert el.text == "Accept terms"


def test_disabled_state_classes_cover_peer_and_group(env):
    classes = render(env, "{{ label() }}")["class"]
    assert "peer-disabled:opacity-50" in classes
    assert "group-data-[disabled=true]:opacity-50" in classes
