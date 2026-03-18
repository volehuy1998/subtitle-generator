"""
API contract tests — HTTP only, no browser.
Asserts response envelope shapes for every endpoint the frontend depends on.
These tests MUST pass in CI before any PR merges.
"""

import pytest
import requests


def _get(base_url, path, session=None, **kwargs):
    """GET helper. Pass session= to reuse an authenticated requests.Session."""
    getter = session.get if session else requests.get
    extra = {} if session else {"verify": False}
    resp = getter(f"{base_url}{path}", timeout=10, **extra, **kwargs)
    resp.raise_for_status()
    return resp.json()


def _post(base_url, path, **kwargs):
    resp = requests.post(f"{base_url}{path}", verify=False, timeout=30, **kwargs)
    resp.raise_for_status()
    return resp.json()


@pytest.mark.contract
def test_duplicates_response_shape(base_url):
    """The root cause of the 2026-03-18 deployment bug — assert correct keys."""
    data = _get(
        base_url,
        "/tasks/duplicates",
        params={"filename": "doesnotexist.wav", "file_size": 1},
    )
    assert "duplicates_found" in data, f"Missing 'duplicates_found' key: {data}"
    assert isinstance(data["duplicates_found"], bool)
    assert "matches" in data, f"Missing 'matches' key: {data}"
    assert isinstance(data["matches"], list)


@pytest.mark.contract
def test_upload_response_shape(base_url, test_audio_file):
    with open(test_audio_file, "rb") as f:
        data = _post(base_url, "/upload", files={"file": f})
    assert "task_id" in data and isinstance(data["task_id"], str)
    assert "model_size" in data and isinstance(data["model_size"], str)
    assert "language" in data and isinstance(data["language"], str)
    assert "word_timestamps" in data and isinstance(data["word_timestamps"], bool)
    assert "diarize" in data and isinstance(data["diarize"], bool)


@pytest.mark.contract
def test_progress_response_shape(base_url, completed_task_id, task_http_session):
    """Uses task_http_session so session cookies are sent (progress endpoint is session-gated)."""
    data = _get(base_url, f"/progress/{completed_task_id}", session=task_http_session)
    # task_id may be null for completed tasks (backend returns None when done)
    assert "task_id" in data, f"Missing 'task_id' key: {data}"
    assert "status" in data and isinstance(data["status"], str)
    assert "percent" in data and isinstance(data["percent"], (int, float))
    assert "message" in data and isinstance(data["message"], str)


@pytest.mark.contract
def test_subtitles_response_shape(base_url, completed_task_id, task_http_session):
    data = _get(base_url, f"/subtitles/{completed_task_id}", session=task_http_session)
    assert "task_id" in data and isinstance(data["task_id"], str)
    assert "segments" in data and isinstance(data["segments"], list)


@pytest.mark.contract
def test_search_response_shape(base_url, completed_task_id, task_http_session):
    """Uses task_http_session so session cookies are sent (search endpoint is session-gated)."""
    data = _get(
        base_url,
        f"/search/{completed_task_id}",
        session=task_http_session,
        params={"q": "the"},
    )
    assert "task_id" in data and isinstance(data["task_id"], str)
    assert "query" in data and isinstance(data["query"], str)
    assert "matches" in data, f"'matches' key missing — got: {list(data.keys())}"
    assert isinstance(data["matches"], list)
    assert "total_matches" in data and isinstance(data["total_matches"], int)


@pytest.mark.contract
def test_translation_languages_response_shape(base_url):
    data = _get(base_url, "/translation/languages")
    assert "pairs" in data and isinstance(data["pairs"], list)
    assert "count" in data and isinstance(data["count"], int)


@pytest.mark.contract
def test_embed_presets_response_shape(base_url):
    data = _get(base_url, "/embed/presets")
    assert "presets" in data
    assert isinstance(data["presets"], dict), f"'presets' must be dict, got {type(data['presets'])}"
    assert "default" in data["presets"], f"'default' preset missing — got: {list(data['presets'].keys())}"
    default = data["presets"]["default"]
    assert "font_name" in default, f"'font_name' missing from default preset: {default}"


@pytest.mark.contract
def test_health_response_shape(base_url):
    data = _get(base_url, "/health")
    assert "status" in data and isinstance(data["status"], str)
    assert "uptime_sec" in data and isinstance(data["uptime_sec"], (int, float))
