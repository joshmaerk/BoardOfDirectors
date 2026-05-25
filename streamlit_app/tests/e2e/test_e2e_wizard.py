"""E2E golden-path wizard test."""

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

SCREENSHOTS_DIR = Path(__file__).parents[3] / "docs" / "screenshots"


@pytest.fixture(autouse=True)
def _ensure_screenshot_dir():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def _go_to_wizard(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/Neues_Sparring", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(2000)


def test_wizard_golden_path(page: Page, streamlit_server: str):
    """Full golden-path run through all 6 wizard steps in mock mode."""
    _go_to_wizard(page, streamlit_server)

    # Step 1 – Use Case auswählen
    expect(page.locator("text=Use Case").first).to_be_visible(timeout=8000)
    page.screenshot(path=str(SCREENSHOTS_DIR / "wizard_step1_usecase.png"), full_page=True)
    page.locator("button", has_text="Weiter →").first.click()

    # Step 2 – Kontext eingeben
    page.wait_for_timeout(1500)
    expect(page.locator("text=Kontext").first).to_be_visible(timeout=8000)
    page.screenshot(path=str(SCREENSHOTS_DIR / "wizard_step2_context.png"), full_page=True)
    textarea = page.locator("textarea").first
    textarea.fill("Wie können wir unsere Meetings effektiver gestalten?")
    page.locator("button", has_text="Weiter →").first.click()

    # Step 3 – Sicherheitsprüfung (grün)
    page.wait_for_timeout(1500)
    expect(page.locator("text=Sicherheits").first).to_be_visible(timeout=8000)
    expect(page.locator("text=Grün").first).to_be_visible(timeout=8000)
    page.screenshot(path=str(SCREENSHOTS_DIR / "wizard_step3_safety_green.png"), full_page=True)
    page.locator("button", has_text="Weiter →").first.click()

    # Step 4 – Prompt Review
    page.wait_for_timeout(1500)
    page.screenshot(path=str(SCREENSHOTS_DIR / "wizard_step4_prompt.png"), full_page=True)
    page.locator("button", has_text="Weiter →").first.click()

    # Step 5 – Board & Format auswählen → Sparring starten
    page.wait_for_timeout(1500)
    page.screenshot(path=str(SCREENSHOTS_DIR / "wizard_step5_board.png"), full_page=True)
    page.locator("button", has_text="Sparring starten").first.click()

    # Step 6 – Ergebnis
    page.wait_for_timeout(2000)
    expect(page.locator("text=Synthese").first).to_be_visible(timeout=20000)
    expect(page.locator("text=Ergebnis als Markdown").first).to_be_visible(timeout=8000)
    page.screenshot(path=str(SCREENSHOTS_DIR / "wizard_step6_result.png"), full_page=True)
