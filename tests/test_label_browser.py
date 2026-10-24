"""Playwright tests for the label gallery: snapshots, axe, keyboard and disabled states."""
import io
from pathlib import Path

import pytest
from PIL import Image, ImageChops
from axe_playwright_python.sync_playwright import Axe

from .live_server import TEST_SERVER_BASE_URL

SNAPSHOTS = Path(__file__).parent / "snapshots"
MAX_DIFF = 0.005
URL = f"{TEST_SERVER_BASE_URL}/basecoat/gallery/label"
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
    path = SNAPSHOTS / f"label-{theme}.png"
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
    page.get_by_role("link", name="Label states").click()
    page.wait_for_url("**/basecoat/gallery/label")
    assert page.locator("[data-gallery=label]").count() == 1


def test_clicking_label_focuses_its_input(page):
    page.goto(URL)
    page.locator("label[for=email]").click()
    assert page.evaluate("document.activeElement.id") == "email"


def test_clicking_label_toggles_checkbox_and_space_keeps_it_in_tab_order(page):
    page.goto(URL)
    page.locator("label[for=terms]").click()
    assert page.is_checked("#terms")
    page.focus("#email")
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "terms"
    page.keyboard.press("Space")
    assert not page.is_checked("#terms")


def test_arrow_keys_and_escape_keep_focus_on_labelled_input(page):
    page.goto(URL)
    page.locator("label[for=email]").click()
    page.keyboard.type("abc")
    page.keyboard.press("ArrowLeft")
    assert page.evaluate("document.activeElement.selectionStart") == 2
    page.keyboard.press("Escape")
    assert page.evaluate("document.activeElement.id") == "email"
    assert page.input_value("#email") == "abc"


def test_label_is_associated_for_assistive_tech(page):
    page.goto(URL)
    assert page.get_by_label("Email", exact=True).get_attribute("id") == "email"


def test_peer_disabled_label_is_dimmed_and_not_clickable_to_focus(page):
    page.goto(URL)
    opacity = page.evaluate("getComputedStyle(document.querySelector('label[for=disabled-input]')).opacity")
    normal = page.evaluate("getComputedStyle(document.querySelector('label[for=email]')).opacity")
    assert float(opacity) == 0.5 and float(normal) == 1.0
    cursor = page.evaluate("getComputedStyle(document.querySelector('label[for=disabled-input]')).cursor")
    assert cursor == "not-allowed"
    page.locator("label[for=disabled-input]").click()
    assert page.evaluate("document.activeElement.id") != "disabled-input"


def test_group_disabled_label_is_dimmed_and_ignores_pointer(page):
    page.goto(URL)
    style = page.evaluate(
        "(() => { const s = getComputedStyle(document.querySelector('[data-gallery=label] [data-disabled=true] label')); "
        "return [s.opacity, s.pointerEvents]; })()"
    )
    assert style == ["0.5", "none"]
