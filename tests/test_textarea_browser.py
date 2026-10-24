"""Playwright tests for the textarea gallery: snapshots, axe, keyboard."""
import io
from pathlib import Path

import pytest
from PIL import Image, ImageChops
from axe_playwright_python.sync_playwright import Axe

from .live_server import TEST_SERVER_BASE_URL

SNAPSHOTS = Path(__file__).parent / "snapshots"
MAX_DIFF = 0.005
URL = f"{TEST_SERVER_BASE_URL}/basecoat/gallery/textarea"
THEMES = {"light": URL, "dark": URL + "?theme=dark"}


@pytest.fixture
def page(page):
    page.set_viewport_size({"width": 900, "height": 1000})
    return page


def diff_ratio(a, b):
    if a.size != b.size:
        return 1.0
    diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB")).convert("L")
    changed = diff.point(lambda v: 255 if v else 0).histogram()[255]
    return changed / (a.size[0] * a.size[1])


@pytest.mark.parametrize("theme", THEMES)
def test_gallery_snapshot(page, theme):
    response = page.goto(THEMES[theme])
    assert response.status == 200
    page.wait_for_load_state("networkidle")
    assert page.evaluate("document.documentElement.classList.contains('dark')") == (theme == "dark")
    shot = Image.open(io.BytesIO(page.screenshot(full_page=True, animations="disabled")))
    path = SNAPSHOTS / f"textarea-{theme}.png"
    if not path.exists():
        SNAPSHOTS.mkdir(exist_ok=True)
        shot.save(path)
        return
    ratio = diff_ratio(shot, Image.open(path))
    assert ratio <= MAX_DIFF, f"{theme} snapshot differs by {ratio:.4%}"


@pytest.mark.parametrize("theme", THEMES)
def test_gallery_axe_no_serious_findings(page, theme):
    assert page.goto(THEMES[theme]).status == 200
    page.wait_for_load_state("networkidle")
    violations = Axe().run(page).response["violations"]
    serious = [v for v in violations if v["impact"] in ("serious", "critical")]
    assert serious == [], [(v["id"], v["impact"]) for v in serious]


def test_gallery_reachable_from_index(page):
    page.goto(f"{TEST_SERVER_BASE_URL}/basecoat/gallery")
    page.get_by_role("link", name="Textarea states").click()
    page.wait_for_url("**/basecoat/gallery/textarea")
    assert page.locator("[data-gallery=textarea]").count() == 1


def test_tab_order_skips_disabled_and_shows_focus_ring(page):
    page.goto(URL)
    page.focus("#size-large")
    page.keyboard.press("Tab")
    # the disabled textarea is skipped
    assert page.evaluate("document.activeElement.id") == "state-readonly"
    ring = page.evaluate("getComputedStyle(document.activeElement).boxShadow")
    assert ring != "none"


def test_typing_enter_and_arrow_keys_move_the_caret(page):
    page.goto(URL)
    page.focus("#state-default")
    page.keyboard.type("ab")
    page.keyboard.press("Enter")
    page.keyboard.type("cd")
    assert page.input_value("#state-default") == "ab\ncd"
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowLeft")
    assert page.evaluate("document.activeElement.selectionStart") == 2
    page.keyboard.press("ArrowUp")
    assert page.evaluate("document.activeElement.selectionStart") <= 2
    page.keyboard.press("ArrowDown")
    page.keyboard.press("End")
    assert page.evaluate("document.activeElement.selectionStart") == 5
    assert page.evaluate("document.activeElement.id") == "state-default"


def test_escape_keeps_focus_and_text(page):
    page.goto(URL)
    page.focus("#state-default")
    page.keyboard.type("keep")
    page.keyboard.press("Escape")
    assert page.evaluate("document.activeElement.id") == "state-default"
    assert page.input_value("#state-default") == "keep"


def test_readonly_is_focusable_but_not_editable_and_disabled_is_not_focusable(page):
    page.goto(URL)
    page.focus("#state-readonly")
    page.keyboard.type("zzz")
    assert page.input_value("#state-readonly") == "Read only"
    page.focus("#state-disabled")
    assert page.evaluate("document.activeElement.id") != "state-disabled"


def test_label_click_focuses_textarea(page):
    page.goto(URL)
    page.get_by_text("Your message", exact=True).click()
    assert page.evaluate("document.activeElement.id") == "message"


def test_invalid_state_exposes_aria_and_destructive_border(page):
    page.goto(URL)
    assert page.get_attribute("#state-invalid", "aria-invalid") == "true"
    assert page.get_attribute("#state-default", "aria-invalid") is None
    invalid = page.evaluate("getComputedStyle(document.getElementById('state-invalid')).borderTopColor")
    normal = page.evaluate("getComputedStyle(document.getElementById('state-default')).borderTopColor")
    assert invalid != normal
