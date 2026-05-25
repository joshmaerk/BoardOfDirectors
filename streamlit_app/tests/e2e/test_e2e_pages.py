"""E2E tests for Board-Bibliothek and Hilfe pages."""

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

SCREENSHOTS_DIR = Path(__file__).parents[3] / "docs" / "screenshots"


@pytest.fixture(autouse=True)
def _ensure_screenshot_dir():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def test_board_library_loads(page: Page, streamlit_server: str):
    page.goto(f"{streamlit_server}/Board_Bibliothek", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(2000)
    expect(page.locator("text=Board Bibliothek").first).to_be_visible(timeout=8000)
    page.screenshot(path=str(SCREENSHOTS_DIR / "board_library.png"), full_page=True)


def test_board_library_shows_boards(page: Page, streamlit_server: str):
    page.goto(f"{streamlit_server}/Board_Bibliothek", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(2000)
    for board_fragment in ["Management", "Banking", "Communications"]:
        expect(page.locator(f"text={board_fragment}").first).to_be_visible(timeout=8000)


def test_help_page_loads(page: Page, streamlit_server: str):
    page.goto(f"{streamlit_server}/Hilfe_Leitplanken", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(2000)
    expect(page.locator("text=Hilfe").first).to_be_visible(timeout=8000)
    page.screenshot(path=str(SCREENSHOTS_DIR / "help_page.png"), full_page=True)


def test_help_page_shows_safety_levels(page: Page, streamlit_server: str):
    page.goto(f"{streamlit_server}/Hilfe_Leitplanken", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(2000)
    for level in ["Grün", "Gelb", "Rot"]:
        expect(page.locator(f"text={level}").first).to_be_visible(timeout=8000)
