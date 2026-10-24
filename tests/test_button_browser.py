"""Playwright tests for the button gallery: snapshots, axe, keyboard."""
import io
from pathlib import Path

import pytest
from PIL import Image, ImageChops
from axe_playwright_python.sync_playwright import Axe

from .live_server import TEST_SERVER_BASE_URL

SNAPSHOTS = Path(__file__).parent / "snapshots"
MAX_DIFF = 0.005
URL = f"{TEST_SERVER_BASE_URL}/basecoat/gallery/button"
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
    path = SNAPSHOTS / f"button-{theme}.png"
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
    page.get_by_role("link", name="Button states").click()
    page.wait_for_url("**/basecoat/gallery/button")
    assert page.locator("[data-gallery=button]").count() == 1


def test_tab_order_skips_disabled_and_shows_focus_ring(page):
    page.goto(URL)
    page.focus("#variant-default")
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "variant-secondary"
    page.focus("#size-icon")
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "with-icon"
    page.focus("#state-invalid")
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "state-pressed"
    page.keyboard.press("Tab")
    # disabled button and disabled link are skipped
    assert page.evaluate("document.activeElement.id") == "as-link"
    ring = page.evaluate(
        "getComputedStyle(document.activeElement).boxShadow")
    assert ring != "none"


@pytest.mark.parametrize("key", ["Enter", "Space"])
def test_enter_and_space_activate_button(page, key):
    page.goto(URL)
    page.evaluate("""() => {
        window.__clicks = 0;
        document.getElementById('kbd-cancel').addEventListener('click', () => window.__clicks++);
    }""")
    page.focus("#kbd-cancel")
    page.keyboard.press(key)
    assert page.evaluate("window.__clicks") == 1


def test_disabled_button_ignores_keyboard_and_focus(page):
    page.goto(URL)
    page.evaluate("""() => {
        window.__clicks = 0;
        document.getElementById('state-disabled').addEventListener('click', () => window.__clicks++);
    }""")
    page.focus("#state-disabled")
    page.keyboard.press("Enter")
    assert page.evaluate("document.activeElement.id") != "state-disabled"
    assert page.evaluate("window.__clicks") == 0


def test_escape_and_arrows_do_not_move_focus_or_activate(page):
    """A button is not a composite widget: arrows and Escape leave it alone."""
    page.goto(URL)
    page.evaluate("""() => {
        window.__clicks = 0;
        document.getElementById('kbd-cancel').addEventListener('click', () => window.__clicks++);
    }""")
    page.focus("#kbd-cancel")
    for key in ("ArrowRight", "ArrowDown", "Escape"):
        page.keyboard.press(key)
    assert page.evaluate("document.activeElement.id") == "kbd-cancel"
    assert page.evaluate("window.__clicks") == 0


def test_link_button_follows_enter(page):
    page.goto(URL)
    page.focus("#as-link")
    page.keyboard.press("Enter")
    assert page.url.endswith("#as-link")
