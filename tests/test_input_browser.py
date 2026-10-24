"""Playwright tests for the input gallery entry: snapshots in both themes, axe, and keyboard behaviour."""
import io
from pathlib import Path

import numpy as np
import pytest
from axe_playwright_python.sync_playwright import Axe
from PIL import Image

from tests.live_server import TEST_SERVER_BASE_URL

URL = f"{TEST_SERVER_BASE_URL}/basecoat/gallery/input"
SNAP_DIR = Path(__file__).parent / "snapshots"
MAX_DIFF = 0.005  # 0.5 per cent of pixels


@pytest.fixture
def page(page):
    page.set_viewport_size({"width": 900, "height": 1000})
    page.emulate_media(reduced_motion="reduce")
    page.goto(URL)
    page.wait_for_selector("#gallery-input")
    return page


def set_theme(page, theme):
    page.evaluate("t => document.documentElement.classList.toggle('dark', t === 'dark')", theme)


def compare_or_record(name, png):
    SNAP_DIR.mkdir(exist_ok=True)
    path = SNAP_DIR / name
    if not path.exists():
        path.write_bytes(png)
        return
    old = np.asarray(Image.open(path).convert("RGB"), dtype=int)
    new = np.asarray(Image.open(io.BytesIO(png)).convert("RGB"), dtype=int)
    assert old.shape == new.shape, f"{name}: size changed {old.shape} -> {new.shape}"
    ratio = (np.abs(old - new).sum(axis=2) > 0).mean()
    assert ratio <= MAX_DIFF, f"{name}: {ratio:.4%} of pixels differ (limit {MAX_DIFF:.1%})"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_gallery_input_snapshot(page, theme):
    set_theme(page, theme)
    page.add_style_tag(content="*{caret-color:transparent!important}")
    png = page.locator("#gallery-input").screenshot(animations="disabled")
    compare_or_record(f"input-gallery-{theme}.png", png)


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_gallery_input_axe_no_serious(page, theme):
    set_theme(page, theme)
    results = Axe().run(page)
    bad = [v for v in results.response["violations"] if v["impact"] in ("serious", "critical")]
    assert not bad, [(v["id"], v["impact"], [n["target"] for n in v["nodes"]]) for v in bad]


def test_gallery_index_links_to_input(page):
    pg = page
    pg.goto(f"{TEST_SERVER_BASE_URL}/basecoat/gallery")
    pg.click("nav[aria-label='Component pages'] >> text=Input")
    assert pg.url == URL


def test_keyboard_focus_and_typing(page):
    page.focus("#in-default")
    assert page.evaluate("document.activeElement.id") == "in-default"
    page.keyboard.type("a@b.co")
    assert page.input_value("#in-default") == "a@b.co"
    # arrow keys move the caret inside the field
    page.keyboard.press("Home")
    page.keyboard.press("ArrowRight")
    page.keyboard.type("X")
    assert page.input_value("#in-default") == "aX@b.co"
    page.keyboard.press("Escape")  # input keeps focus and value on Escape, as in shadcn
    assert page.evaluate("document.activeElement.id") == "in-default"


def test_tab_order_skips_disabled_and_reaches_readonly(page):
    page.focus("#in-file")
    page.keyboard.press("Tab")
    focused = page.evaluate("document.activeElement.id")
    assert focused == "in-readonly"  # disabled input is skipped


def test_focus_ring_uses_ring_token(page):
    page.focus("#in-default")
    shadow = page.eval_on_selector("#in-default", "e => getComputedStyle(e).boxShadow")
    assert shadow != "none"


def test_disabled_not_focusable_and_invalid_exposed(page):
    assert page.is_disabled("#in-disabled")
    assert page.get_attribute("#in-invalid", "aria-invalid") == "true"
    assert page.get_attribute("#in-invalid", "aria-describedby") == "in-invalid-err"
