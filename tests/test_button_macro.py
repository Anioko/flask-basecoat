"""Unit tests for the button macro: Basecoat/shadcn classes, ARIA and slots."""
import pytest
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup
from pathlib import Path

TEMPLATES = Path(__file__).parent.parent / "flask_basecoat/templates"

VARIANT_CLASSES = {
    "default": "bg-primary text-primary-foreground hover:bg-primary/90",
    "destructive": "bg-destructive hover:bg-destructive/90 dark:bg-destructive/60",
    "outline": "border bg-background hover:bg-accent dark:bg-input/30",
    "secondary": "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    "ghost": "hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/50",
    "link": "text-primary underline-offset-4 hover:underline",
}
SIZE_CLASSES = {
    "default": "h-9 px-4 py-2",
    "sm": "h-8 gap-1.5 px-3",
    "lg": "h-10 px-6",
    "icon": "size-9",
}


@pytest.fixture(scope="module")
def env():
    return Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=True)


def render(env, source):
    tpl = env.from_string("{% from 'basecoat/button.html' import button %}" + source)
    soup = BeautifulSoup(tpl.render(), "html.parser")
    return soup.find(attrs={"data-slot": "button"})


@pytest.mark.parametrize("variant", VARIANT_CLASSES)
def test_variant_classes(env, variant):
    el = render(env, f"{{{{ button(content='x', variant='{variant}') }}}}")
    classes = set(el["class"])
    assert el.name == "button"
    assert el["type"] == "button"
    for cls in VARIANT_CLASSES[variant].split():
        assert cls in classes, cls
    assert "inline-flex" in classes and "focus-visible:ring-[3px]" in classes


@pytest.mark.parametrize("size", SIZE_CLASSES)
def test_size_classes(env, size):
    el = render(env, f"{{{{ button(content='x', size='{size}') }}}}")
    for cls in SIZE_CLASSES[size].split():
        assert cls in el["class"], cls


def test_caller_slot_renders_children(env):
    el = render(env, "{% call button(variant='outline') %}<svg></svg> Go{% endcall %}")
    assert el.find("svg") is not None
    assert el.get_text(strip=True) == "Go"


def test_disabled_state(env):
    el = render(env, "{{ button(content='x', disabled=true) }}")
    assert el.has_attr("disabled")
    assert not el.has_attr("aria-busy")


def test_loading_state_shows_spinner_and_disables(env):
    el = render(env, "{{ button(content='Please wait', loading=true) }}")
    assert el.has_attr("disabled")
    assert el["aria-busy"] == "true"
    spinner = el.find("svg")
    assert "animate-spin" in spinner["class"]
    assert spinner["aria-hidden"] == "true"


def test_invalid_pressed_expanded_label(env):
    el = render(env, "{{ button(content='x', invalid=true, aria_pressed=false, "
                     "aria_expanded=true, aria_controls='m', aria_label='Menu') }}")
    assert el["aria-invalid"] == "true"
    assert el["aria-pressed"] == "false"
    assert el["aria-expanded"] == "true"
    assert el["aria-controls"] == "m"
    assert el["aria-label"] == "Menu"


def test_href_renders_link_with_same_classes(env):
    link = render(env, "{{ button(content='x', variant='secondary', href='/a') }}")
    btn = render(env, "{{ button(content='x', variant='secondary') }}")
    assert link.name == "a" and link["href"] == "/a"
    assert link["class"] == btn["class"]
    assert not link.has_attr("type")


def test_disabled_link_is_not_focusable_or_navigable(env):
    link = render(env, "{{ button(content='x', href='/a', disabled=true) }}")
    assert not link.has_attr("href")
    assert link["aria-disabled"] == "true"
    assert link["tabindex"] == "-1"


def test_submit_type_and_extra_class(env):
    el = render(env, "{{ button(content='x', type='submit', class='w-full') }}")
    assert el["type"] == "submit"
    assert "w-full" in el["class"]
