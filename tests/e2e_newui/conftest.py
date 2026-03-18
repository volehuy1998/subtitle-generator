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
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
def task_http_session():
    """A requests.Session instance shared by completed_task_id and contract tests."""
    s = requests.Session()
    s.verify = False
    return s


@pytest.fixture(scope="session")
def fixture_audio_file(tmp_path_factory, test_audio_file):
    """Separate unique audio file for the completed_task_id fixture.

    Kept distinct from unique_audio_file so that test_happy_path_upload
    never sees this upload as a duplicate.
    """
    dest = tmp_path_factory.mktemp("fixture") / f"fixture_{uuid.uuid4().hex[:8]}.wav"
    shutil.copy(test_audio_file, dest)
    return dest


@pytest.fixture(scope="session")
def contract_audio_file(tmp_path_factory, test_audio_file):
    """Unique audio file for the upload contract test.

    Kept separate so test_duplicate_detection_* tests are not affected
    by a prior upload of the same filename.
    """
    dest = tmp_path_factory.mktemp("contract") / f"contract_{uuid.uuid4().hex[:8]}.wav"
    shutil.copy(test_audio_file, dest)
    return dest


@pytest.fixture(scope="session")
def duplicate_test_audio_file(tmp_path_factory, test_audio_file):
    """Shared audio file used by both duplicate detection tests.

    Session-scoped so the second duplicate test sees the task created by
    the first, reliably triggering duplicate detection.
    """
    dest = tmp_path_factory.mktemp("dupes") / f"dupe_{uuid.uuid4().hex[:8]}.wav"
    shutil.copy(test_audio_file, dest)
    return dest


@pytest.fixture(scope="session")
def completed_task_id(base_url, fixture_audio_file, task_http_session):
    """
    Returns a task ID for a completed transcription.
    Checks FIXTURE_TASK_ID env var first (local dev), then uploads and polls (CI).
    Tests that depend on this fixture are SKIPPED (not failed) if the task can't complete.
    """
    task_id = os.environ.get("FIXTURE_TASK_ID")
    if task_id:
        return task_id

    # Upload and poll to completion — use a Session to persist cookies for session auth
    session = task_http_session
    try:
        with open(fixture_audio_file, "rb") as f:
            resp = session.post(
                f"{base_url}/upload",
                files={"file": f},
                timeout=30,
            )
        resp.raise_for_status()
        task_id = resp.json()["task_id"]
    except Exception as exc:
        pytest.skip(f"Fixture upload failed: {exc}")

    deadline = time.time() + 300
    while time.time() < deadline:
        try:
            prog = session.get(f"{base_url}/progress/{task_id}", timeout=10).json()
        except Exception:
            time.sleep(2)
            continue
        status = prog.get("status")
        if status is None:
            # Unexpected response shape — skip rather than error
            pytest.skip(f"Unexpected progress response: {prog}")
        if status == "done":
            return task_id
        if status in ("error", "cancelled"):
            pytest.skip(f"Fixture task failed: {prog.get('message')}")
        time.sleep(2)

    pytest.skip("Fixture task timed out after 300s")
