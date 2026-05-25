"""E2E safety classification tests (red and yellow)."""
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

SCREENSHOTS_DIR = Path(__file__).parents[3] / "docs" / "screenshots"

_IBAN = "DE89 3704 0044 0532 0130 00"


@pytest.fixture(autouse=True)
def _ensure_screenshot_dir():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def _reach_step3(page: Page, base_url: str, context_text: str) -> None:
    page.goto(f"{base_url}/Neues_Sparring", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(2000)

    # Step 1 → Step 2
    page.locator("button", has_text="Weiter →").first.click()
    page.wait_for_timeout(1500)

    # Step 2: fill context → Step 3
    page.locator("textarea").first.fill(context_text)
    page.locator("button", has_text="Weiter →").first.click()
    page.wait_for_timeout(1500)


def test_red_safety_blocks_progress(page: Page, streamlit_server: str):
    """IBAN in context triggers red safety – only Zurück is shown."""
    _reach_step3(page, streamlit_server, f"Bitte prüfe Konto {_IBAN}")

    expect(page.locator("text=Rot").first).to_be_visible(timeout=8000)
    page.screenshot(path=str(SCREENSHOTS_DIR / "wizard_step3_safety_red.png"), full_page=True)

    # Weiter button must not be present
    expect(page.locator("button", has_text="Weiter →")).not_to_be_visible(timeout=5000)
    # Zurück button must be present
    expect(page.locator("button", has_text="← Zurück").first).to_be_visible(timeout=5000)


def test_yellow_safety_shows_checkbox(page: Page, streamlit_server: str):
    """Strategy keyword triggers yellow safety – confirmation checkbox appears."""
    _reach_step3(page, streamlit_server, "Unsere Strategie für das nächste Budget-Jahr")

    expect(page.locator("text=Gelb").first).to_be_visible(timeout=8000)
    page.screenshot(
        path=str(SCREENSHOTS_DIR / "wizard_step3_safety_yellow.png"), full_page=True
    )
    expect(page.locator("[data-testid='stCheckbox']").first).to_be_visible(timeout=8000)
