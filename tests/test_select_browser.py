"""Playwright tests for the select gallery entry: snapshots in both themes, axe, and keyboard operation."""
import io
from pathlib import Path

import pytest
from PIL import Image, ImageChops

playwright_sync = pytest.importorskip("playwright.sync_api")
from axe_playwright_python.sync_playwright import Axe  # noqa: E402

from .live_server import TEST_SERVER_BASE_URL  # noqa: E402

GALLERY_URL = f"{TEST_SERVER_BASE_URL}/basecoat/gallery/select"
SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
MAX_DIFF_RATIO = 0.005


@pytest.fixture(scope="module")
def browser():
    with playwright_sync.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page(browser):
    ctx = browser.new_context(viewport={"width": 1000, "height": 1300}, reduced_motion="reduce")
    pg = ctx.new_page()
    pg.set_default_timeout(5000)
    yield pg
    ctx.close()


def open_gallery(page, theme="light"):
    page.goto(GALLERY_URL, wait_until="networkidle")
    page.evaluate("theme => document.documentElement.classList.toggle('dark', theme === 'dark')", theme)
    page.wait_for_selector("[data-slot=select-trigger]")
    page.wait_for_timeout(200)


def diff_ratio(a_bytes, b_bytes):
    a = Image.open(io.BytesIO(a_bytes)).convert("RGB")
    b = Image.open(io.BytesIO(b_bytes)).convert("RGB")
    if a.size != b.size:
        return 1.0
    mask = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v else 0)
    return sum(1 for v in mask.getdata() if v) / (a.size[0] * a.size[1])


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_gallery_snapshot(page, theme):
    open_gallery(page, theme)
    shot = page.screenshot(full_page=True)
    stored = SNAPSHOT_DIR / f"select-gallery-{theme}.png"
    if not stored.exists():
        SNAPSHOT_DIR.mkdir(exist_ok=True)
        stored.write_bytes(shot)
        return
    ratio = diff_ratio(shot, stored.read_bytes())
    assert ratio <= MAX_DIFF_RATIO, f"{theme} snapshot differs by {ratio:.4%} (limit {MAX_DIFF_RATIO:.1%})"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_gallery_axe_no_serious_findings(page, theme):
    open_gallery(page, theme)
    results = Axe().run(page)
    serious = [v for v in results.response["violations"] if v["impact"] in ("serious", "critical")]
    assert serious == [], [(v["id"], v["impact"], [n["target"] for n in v["nodes"]]) for v in serious]


def test_gallery_index_links_to_select(page):
    page.goto(f"{TEST_SERVER_BASE_URL}/basecoat/gallery", wait_until="domcontentloaded")
    page.click("[data-slot=gallery-index] a[href$='/gallery/select']")
    page.wait_for_selector("[data-slot=select-trigger]")
    assert page.url.endswith("/basecoat/gallery/select")


def test_keyboard_focus_arrows_enter_and_escape(page):
    open_gallery(page)
    trigger = page.locator("#sel-default-trigger")
    popover = page.locator("#sel-default [data-popover]")

    trigger.focus()
    assert page.evaluate("document.activeElement.id") == "sel-default-trigger"
    assert trigger.get_attribute("aria-expanded") == "false"

    page.keyboard.press("ArrowDown")
    assert trigger.get_attribute("aria-expanded") == "true"
    assert popover.get_attribute("aria-hidden") == "false"

    page.keyboard.press("ArrowDown")
    assert trigger.get_attribute("aria-activedescendant") == "sel-default-opt-1"
    page.keyboard.press("ArrowDown")
    assert trigger.get_attribute("aria-activedescendant") == "sel-default-opt-2"
    page.keyboard.press("ArrowUp")
    assert trigger.get_attribute("aria-activedescendant") == "sel-default-opt-1"
    page.keyboard.press("End")
    assert trigger.get_attribute("aria-activedescendant") == "sel-default-opt-5"
    page.keyboard.press("Home")
    assert trigger.get_attribute("aria-activedescendant") == "sel-default-opt-1"

    page.keyboard.press("Escape")
    assert trigger.get_attribute("aria-expanded") == "false"
    assert popover.get_attribute("aria-hidden") == "true"
    assert page.evaluate("document.activeElement.id") == "sel-default-trigger"
    assert page.input_value("#sel-default input[type=hidden]") == ""

    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    assert trigger.get_attribute("aria-expanded") == "false"
    assert page.input_value("#sel-default input[type=hidden]") == "banana"
    assert trigger.inner_text().strip() == "Banana"
    assert trigger.get_attribute("data-placeholder") is None
    assert page.locator("#sel-default [role=option][aria-selected=true]").get_attribute("data-value") == "banana"


def test_tab_reaches_trigger_and_skips_disabled(page):
    open_gallery(page)
    page.locator("#sel-scroll-trigger").focus()
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "sel-disabled-item-trigger"
    assert page.locator("#sel-disabled-trigger").is_disabled()


def test_disabled_option_is_skipped_by_arrow_keys(page):
    open_gallery(page)
    page.locator("#sel-disabled-item-trigger").focus()
    page.keyboard.press("ArrowDown")
    page.keyboard.press("End")
    assert page.locator("#sel-disabled-item-trigger").get_attribute("aria-activedescendant") == "sel-disabled-item-opt-3"
