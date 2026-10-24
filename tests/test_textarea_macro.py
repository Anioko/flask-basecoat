"""Unit tests for the textarea macro: shadcn classes, ARIA and slot."""
import re
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

TEMPLATES = Path(__file__).parent.parent / "flask_basecoat/templates"
TSX = Path("/tmp/shadcn-fork/components/ui/textarea.tsx")

BASE_CLASSES = (
    "border-input placeholder:text-muted-foreground focus-visible:border-ring "
    "focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 "
    "dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive "
    "dark:bg-input/30 flex field-sizing-content min-h-16 w-full rounded-md border "
    "bg-transparent px-3 py-2 text-base shadow-xs transition-[color,box-shadow] "
    "outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed "
    "disabled:opacity-50 md:text-sm"
).split()


@pytest.fixture(scope="module")
def env():
    return Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=True)


def render(env, source):
    tpl = env.from_string("{% from 'basecoat/textarea.html' import textarea %}" + source)
    soup = BeautifulSoup(tpl.render(), "html.parser")
    return soup.find(attrs={"data-slot": "textarea"})


def test_default_has_every_shadcn_class_and_slot(env):
    el = render(env, "{{ textarea() }}")
    assert el.name == "textarea"
    assert el["data-slot"] == "textarea"
    assert sorted(el["class"]) == sorted(BASE_CLASSES)
    for attr in ("disabled", "readonly", "required", "aria-invalid", "rows"):
        assert not el.has_attr(attr)


@pytest.mark.skipif(not TSX.exists(), reason="shadcn fork not cloned")
def test_default_classes_equal_shadcn_source(env):
    cn = re.search(r'className=\{cn\(\s*"([^"]+)"', TSX.read_text())
    assert sorted(render(env, "{{ textarea() }}")["class"]) == sorted(cn.group(1).split())


def test_extra_class_is_appended_and_base_kept(env):
    el = render(env, "{{ textarea(class='font-mono') }}")
    assert "font-mono" in el["class"]
    assert set(BASE_CLASSES) <= set(el["class"])


@pytest.mark.parametrize("rows", [2, 6])
def test_rows_sets_height(env, rows):
    assert render(env, f"{{{{ textarea(rows={rows}) }}}}")["rows"] == str(rows)


def test_disabled_and_readonly(env):
    assert render(env, "{{ textarea(disabled=true) }}").has_attr("disabled")
    assert render(env, "{{ textarea(readonly=true) }}").has_attr("readonly")


def test_required_sets_aria_required(env):
    el = render(env, "{{ textarea(required=true) }}")
    assert el.has_attr("required") and el["aria-required"] == "true"


def test_invalid_sets_aria_invalid_which_drives_destructive_classes(env):
    el = render(env, "{{ textarea(invalid=true) }}")
    assert el["aria-invalid"] == "true"
    assert "aria-invalid:border-destructive" in el["class"]


def test_aria_attributes_and_identity(env):
    el = render(env, "{{ textarea(id='m', name='msg', placeholder='Hi', maxlength=50,"
                     " aria_label='Message', aria_describedby='help') }}")
    assert (el["id"], el["name"], el["placeholder"], el["maxlength"]) == ("m", "msg", "Hi", "50")
    assert el["aria-label"] == "Message" and el["aria-describedby"] == "help"


def test_content_value_and_call_slot(env):
    assert render(env, "{{ textarea(content='a') }}").text == "a"
    assert render(env, "{{ textarea(value='b') }}").text == "b"
    assert render(env, "{% call textarea() %}from slot{% endcall %}").text == "from slot"


def test_content_is_escaped(env):
    el = render(env, "{{ textarea(content='</textarea><b>x</b>') }}")
    assert el.find("b") is None
    assert el.text == "</textarea><b>x</b>"
