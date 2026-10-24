"""Browser tests for the checkbox gallery entry: snapshots in both themes, axe, focus and keyboard."""
import io
from pathlib import Path

import pytest
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

from .live_server import TEST_SERVER_BASE_URL, ensure_server

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
MAX_DIFF_RATIO = 0.005
URL = f"{TEST_SERVER_BASE_URL}/basecoat/gallery/checkbox"


@pytest.fixture(scope="module")
def browser():
    ensure_server()
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(headless=True)
        except Exception as exc:  # pragma: no cover
            pytest.skip(f"Chromium not available: {exc}")
        yield b
        b.close()


@pytest.fixture
def page(browser):
    ctx = browser.new_context(viewport={"width": 900, "height": 1000}, reduced_motion="reduce")
    pg = ctx.new_page()
    pg.goto(URL, wait_until="load")
    pg.wait_for_selector('[data-slot="checkbox"]')
    yield pg
    ctx.close()


def set_theme(page, theme):
    page.evaluate("t => document.documentElement.classList.toggle('dark', t === 'dark')", theme)


def diff_ratio(a_bytes, b_bytes):
    a, b = Image.open(io.BytesIO(a_bytes)).convert("RGB"), Image.open(io.BytesIO(b_bytes)).convert("RGB")
    if a.size != b.size:
        return 1.0
    diff = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 8 else 0)
    return sum(1 for v in diff.getdata() if v) / (a.size[0] * a.size[1])


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_gallery_snapshot(page, theme):
    set_theme(page, theme)
    shot = page.locator('[data-testid="checkbox-states"]').screenshot(animations="disabled")
    path = SNAPSHOT_DIR / f"checkbox-{theme}.png"
    if not path.exists():
        SNAPSHOT_DIR.mkdir(exist_ok=True)
        path.write_bytes(shot)
        return
    ratio = diff_ratio(path.read_bytes(), shot)
    assert ratio <= MAX_DIFF_RATIO, f"{theme} snapshot differs by {ratio:.4%} (limit {MAX_DIFF_RATIO:.1%})"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_gallery_axe_no_serious_findings(page, theme):
    from axe_playwright_python.sync_playwright import Axe

    set_theme(page, theme)
    violations = Axe().run(page).response["violations"]
    serious = [v for v in violations if v["impact"] in ("serious", "critical")]
    assert not serious, [(v["id"], v["impact"], [n["target"] for n in v["nodes"]]) for v in serious]


def box(page, id_):
    return page.locator(f"#{id_}")


def test_gallery_is_linked_from_index(browser):
    ctx = browser.new_context()
    pg = ctx.new_page()
    pg.goto(f"{TEST_SERVER_BASE_URL}/basecoat/gallery")
    pg.get_by_role("link", name="Checkbox").click()
    pg.wait_for_url("**/gallery/checkbox")
    assert pg.get_by_role("heading", name="Checkbox", level=1).is_visible()
    ctx.close()


def test_tab_focuses_first_checkbox_with_ring(page):
    page.get_by_role("link", name="Back to gallery").focus()
    page.keyboard.press("Tab")
    first = box(page, "cb-default")
    assert first.evaluate("el => document.activeElement === el")
    assert first.evaluate("el => getComputedStyle(el).boxShadow") != "none"


def test_space_toggles_and_enter_does_not(page):
    first = box(page, "cb-default")
    first.focus()
    page.keyboard.press("Enter")
    assert first.get_attribute("aria-checked") == "false"
    page.keyboard.press("Space")
    assert first.get_attribute("aria-checked") == "true"
    assert first.get_attribute("data-state") == "checked"
    assert first.locator("svg").count() == 1
    page.keyboard.press("Space")
    assert first.get_attribute("aria-checked") == "false"
    assert first.locator("svg").count() == 0


def test_arrow_keys_and_escape_leave_state_and_focus(page):
    first = box(page, "cb-checked")
    first.focus()
    for key in ("ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight", "Escape"):
        page.keyboard.press(key)
        assert first.get_attribute("aria-checked") == "true", key
        assert first.evaluate("el => document.activeElement === el"), key


def test_tab_order_skips_disabled_and_shift_tab_returns(page):
    box(page, "cb-indeterminate").focus()
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "cb-invalid"
    page.keyboard.press("Shift+Tab")
    assert page.evaluate("document.activeElement.id") == "cb-indeterminate"


def test_indeterminate_becomes_checked_and_disabled_ignores_input(page):
    mixed = box(page, "cb-indeterminate")
    assert mixed.get_attribute("aria-checked") == "mixed"
    mixed.focus()
    page.keyboard.press("Space")
    assert mixed.get_attribute("aria-checked") == "true"
    disabled = box(page, "cb-disabled")
    disabled.click(force=True)
    assert disabled.get_attribute("aria-checked") == "false"


def test_clicking_label_toggles_and_syncs_form_value(page):
    page.get_by_text("Required", exact=True).click()
    assert box(page, "cb-required").get_attribute("aria-checked") == "true"
    assert page.locator('input[name="required"]').evaluate("el => el.checked") is True
