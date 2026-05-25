"""E2E tests for the Start page."""
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

SCREENSHOTS_DIR = Path(__file__).parents[3] / "docs" / "screenshots"


@pytest.fixture(autouse=True)
def _ensure_screenshot_dir():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def _go_to_start(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/Start", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(2000)


def test_start_page_loads(page: Page, streamlit_server: str):
    _go_to_start(page, streamlit_server)
    expect(page.locator("text=Board of Directors").first).to_be_visible(timeout=8000)
    page.screenshot(
        path=str(SCREENSHOTS_DIR / "start_page.png"),
        full_page=True,
    )


def test_start_page_shows_value_proposition(page: Page, streamlit_server: str):
    _go_to_start(page, streamlit_server)
    expect(page.locator("text=KI-gestütztes Sparring-System")).to_be_visible(timeout=8000)


def test_start_page_shows_safety_hints(page: Page, streamlit_server: str):
    _go_to_start(page, streamlit_server)
    expect(page.locator("text=Sicherheitshinweise")).to_be_visible(timeout=8000)
    expect(page.locator("text=keine personenbezogenen")).to_be_visible(timeout=8000)


def test_start_page_shows_use_case_buttons(page: Page, streamlit_server: str):
    _go_to_start(page, streamlit_server)
    for use_case in [
        "Entscheidungsvorlage",
        "Kommunikationsreview",
        "Strategie-Sparring",
    ]:
        expect(page.locator(f"text={use_case}").first).to_be_visible(timeout=8000)


def test_start_page_shows_mock_indicator(page: Page, streamlit_server: str):
    _go_to_start(page, streamlit_server)
    expect(page.locator("text=Mock-Modus aktiv").first).to_be_visible(timeout=8000)


def test_navigation_sidebar_present(page: Page, streamlit_server: str):
    _go_to_start(page, streamlit_server)
    for nav_item in ["Neues Sparring", "Meine Runs", "Board Bibliothek"]:
        expect(page.get_by_role("link", name=nav_item)).to_be_visible(timeout=8000)
