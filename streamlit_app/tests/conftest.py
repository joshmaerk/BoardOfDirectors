import os
import sys
import time
from pathlib import Path

import pytest

# Ensure streamlit_app/ is on sys.path for all test imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture()
def mock_st_session(monkeypatch):
    """Replace st.session_state with a plain dict for unit tests."""
    import streamlit as st

    state: dict = {}
    monkeypatch.setattr(st, "session_state", state)
    yield state


@pytest.fixture(scope="session")
def streamlit_server():
    """Start Streamlit in mock mode and yield base URL. Used by e2e tests."""
    import subprocess

    import requests

    env = {**os.environ, "BOARD_API_BASE_URL": ""}
    proc = subprocess.Popen(
        [
            "streamlit",
            "run",
            "app.py",
            "--server.port=8502",
            "--server.headless=true",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false",
        ],
        cwd=Path(__file__).parent.parent,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = "http://localhost:8502"
    for _ in range(30):
        try:
            if requests.get(f"{base_url}/_stcore/health", timeout=1).ok:
                break
        except Exception:
            pass
        time.sleep(1)
    yield base_url
    proc.terminate()
    proc.wait()
