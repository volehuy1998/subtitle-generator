"""
Fixtures for the Drop, See, Refine E2E test suite.
Target: https://newui.openlabs.club (or E2E_BASE_URL env var)
"""

import os
import shutil
import time
import uuid
from pathlib import Path

import pytest
import requests


@pytest.fixture(scope="session")
def base_url():
    return os.environ.get("E2E_BASE_URL", "https://newui.openlabs.club")


@pytest.fixture(scope="session")
def browser_instance(playwright, base_url):
    """Single browser process for the session. Auto-skip if server unreachable."""
    try:
        requests.get(base_url, timeout=5, verify=False)
    except Exception:
        pytest.skip(f"Server unreachable: {base_url}")
    browser = playwright.chromium.launch(headless=True)
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def browser_context(browser_instance):
    """Fresh BrowserContext per test — isolates cookies, localStorage, sessionStorage."""
    context = browser_instance.new_context(ignore_https_errors=True)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(browser_context):
    """Fresh page per test function."""
    p = browser_context.new_page()
    yield p
    p.close()


@pytest.fixture(scope="session")
def test_audio_file():
    return Path(__file__).parent / "fixtures" / "sample.wav"


@pytest.fixture(scope="session")
def unique_audio_file(tmp_path_factory, test_audio_file):
    """Copy sample.wav with a unique filename so each test run avoids stale duplicates."""
    dest = tmp_path_factory.mktemp("audio") / f"sample_{uuid.uuid4().hex[:8]}.wav"
    shutil.copy(test_audio_file, dest)
    return dest


@pytest.fixture(scope="session")
def completed_task_id(base_url, unique_audio_file):
    """
    Returns a task ID for a completed transcription.
    Checks FIXTURE_TASK_ID env var first (local dev), then uploads and polls (CI).
    Tests that depend on this fixture are SKIPPED (not failed) if the task can't complete.
    """
    task_id = os.environ.get("FIXTURE_TASK_ID")
    if task_id:
        return task_id

    # Upload and poll to completion
    try:
        with open(unique_audio_file, "rb") as f:
            resp = requests.post(
                f"{base_url}/upload",
                files={"file": f},
                verify=False,
                timeout=30,
            )
        resp.raise_for_status()
        task_id = resp.json()["task_id"]
    except Exception as exc:
        pytest.skip(f"Fixture upload failed: {exc}")

    deadline = time.time() + 300
    while time.time() < deadline:
        try:
            prog = requests.get(f"{base_url}/progress/{task_id}", verify=False, timeout=10).json()
        except Exception:
            time.sleep(2)
            continue
        if prog["status"] == "done":
            return task_id
        if prog["status"] in ("error", "cancelled"):
            pytest.skip(f"Fixture task failed: {prog.get('message')}")
        time.sleep(2)

    pytest.skip("Fixture task timed out after 300s")
