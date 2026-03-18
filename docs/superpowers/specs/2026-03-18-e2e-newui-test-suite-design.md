# Drop, See, Refine — E2E Test Suite Design

> **Status:** Approved for implementation
> **Date:** 2026-03-18
> **Author:** Atlas (Tech Lead), Team Sentinel

---

## Goal

Build a browser-based end-to-end test suite for the Drop, See, Refine React SPA deployed at `newui.openlabs.club`. The suite simulates real user interactions, verifies the full upload → transcribe → edit workflow, and catches API contract mismatches (the root cause of the deployment bug on 2026-03-18 where `duplicates_found`/`matches` was misread as `duplicates`).

---

## Architecture

### Stack

- **Language:** Python + pytest-playwright (same toolchain as `tests/e2e/`)
- **Location:** `tests/e2e_newui/` — isolated from the existing Lumen E2E suite in `tests/e2e/`
- **Default target:** `https://newui.openlabs.club` (overridable via `E2E_BASE_URL`)
- **Browser:** Chromium (headless)

### Why a separate directory

The existing `tests/e2e/` suite tests the Lumen UI on `openlabs.club`. The two UIs coexist: Lumen on production, Drop, See, Refine on staging. Both suites must run independently without interference. When Drop, See, Refine is promoted to `openlabs.club`, `tests/e2e/` will be retired and `tests/e2e_newui/` becomes the canonical suite.

### Directory layout

```
tests/e2e_newui/
├── conftest.py              # Fixtures: base_url, browser context, pages, task fixtures
├── pytest.ini               # asyncio_mode=auto, marker definitions
├── fixtures/
│   └── sample.wav           # ~50KB silent WAV fixture for live upload tests
├── test_landing.py          # UploadZone UI, ProjectGrid, format hints — no upload
├── test_upload_flow.py      # Live file upload, duplicate dialog, progress, cancel
├── test_editor.py           # Subtitle editing, search, download, session restore
├── test_api_contracts.py    # HTTP-only response shape assertions
└── test_static_pages.py     # Status, About, Security, Contact; nav; footer
```

---

## Fixtures (`conftest.py`)

### Base URL and browser context

```python
@pytest.fixture(scope="session")
def base_url():
    return os.environ.get("E2E_BASE_URL", "https://newui.openlabs.club")

@pytest.fixture(scope="session")
def browser_context(playwright, base_url):
    """Auto-skip entire suite if server is unreachable."""
    try:
        requests.get(base_url, timeout=5, verify=False)
    except Exception:
        pytest.skip(f"Server unreachable: {base_url}")
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(ignore_https_errors=True)
    yield context
    context.close()
    browser.close()
```

### Page fixture — function scope to prevent state bleed

Each test function gets a **fresh page** to prevent navigation state from leaking between tests and test files.

```python
@pytest.fixture(scope="function")
def page(browser_context):
    """Fresh page per test function — prevents URL/state bleed between tests."""
    p = browser_context.new_page()
    yield p
    p.close()
```

### Test audio file fixture

```python
@pytest.fixture(scope="session")
def test_audio_file():
    return Path(__file__).parent / "fixtures" / "sample.wav"
```

`fixtures/sample.wav` is a generated ~50KB silent WAV file committed to the repository. It is created by the implementation task using `scipy.io.wavfile` or an equivalent tool so no external dependency is required.

### Unique audio file fixture (prevents duplicate detection across runs)

Because the duplicate detection endpoint checks by filename and size, reusing the same `sample.wav` across test runs would trigger the duplicate dialog on the very first upload of a new run. Tests that test the **non-duplicate path** must use a file with a unique name per run:

```python
@pytest.fixture(scope="session")
def unique_audio_file(tmp_path_factory, test_audio_file):
    """Copy sample.wav with a unique filename so each test run avoids stale duplicates."""
    import shutil, uuid
    dest = tmp_path_factory.mktemp("audio") / f"sample_{uuid.uuid4().hex[:8]}.wav"
    shutil.copy(test_audio_file, dest)
    return dest
```

`test_upload_flow.py` uses `unique_audio_file` for the happy-path upload and `test_audio_file` for the explicit duplicate-detection test (which intentionally re-uploads the same file after it has been uploaded once).

### Completed task fixture (required by `test_editor.py`)

`test_editor.py` needs a task that has already been transcribed. Two mechanisms are provided; the first available is used:

1. **`FIXTURE_TASK_ID` environment variable** — set to a known completed task ID on the server. Fastest; skips upload entirely. Use this for local development when a completed task already exists.

2. **Auto-upload fixture** — if `FIXTURE_TASK_ID` is not set, the fixture uploads `unique_audio_file` and polls `/progress/{task_id}` every 2 seconds until `status == "done"` (timeout: 300s). This is used in CI.

```python
@pytest.fixture(scope="session")
def completed_task_id(base_url, unique_audio_file):
    task_id = os.environ.get("FIXTURE_TASK_ID")
    if task_id:
        return task_id
    # Upload and poll to completion
    with open(unique_audio_file, "rb") as f:
        resp = requests.post(f"{base_url}/upload",
                             files={"file": f}, verify=False, timeout=30)
    resp.raise_for_status()
    task_id = resp.json()["task_id"]
    deadline = time.time() + 300
    while time.time() < deadline:
        prog = requests.get(f"{base_url}/progress/{task_id}",
                            verify=False, timeout=10).json()
        if prog["status"] == "done":
            return task_id
        if prog["status"] in ("error", "cancelled"):
            pytest.skip(f"Fixture task failed: {prog.get('message')}")
        time.sleep(2)
    pytest.skip("Fixture task timed out after 300s")
```

If the fixture upload or poll fails, tests that depend on it are **skipped** (not failed), so a server-side transcription timeout does not cause false test failures.

---

## `pytest.ini`

```ini
[pytest]
asyncio_mode = auto

markers =
    contract: API response shape assertions — no browser required
    smoke: Critical-path browser tests
    upload: Tests that perform real file uploads (require live server with model loaded)
    editor: Tests that require a completed transcription task
    nav: Navigation and static page tests
```

---

## Test Files

### `test_api_contracts.py` — `@pytest.mark.contract`

HTTP only, no browser. Catches the exact class of bug that motivated this suite. Runs in ~2s.

Each test uses `requests.get` / `requests.post` directly against `base_url`. For endpoints that require a valid `task_id`, the `completed_task_id` session fixture provides one (see above). For endpoints that accept any task-like query parameter (e.g., `/tasks/duplicates`), a known filename and size are passed — a 404 or error response is acceptable as long as the response **still contains the expected keys** (the contract is on the response envelope, not the business logic).

| Endpoint | Required response keys | Types |
|---|---|---|
| `GET /tasks/duplicates?filename=x&file_size=1` | `duplicates_found`, `matches` | `bool`, `list` |
| `POST /upload` (with `sample.wav`) | `task_id`, `model_size`, `language` | `str`, `str`, `str` |
| `GET /progress/{completed_task_id}` | `task_id`, `status`, `percent`, `message` | `str`, `str`, `int/float`, `str` |
| `GET /subtitles/{completed_task_id}` | `task_id`, `segments` | `str`, `list` |
| `GET /search/{completed_task_id}?q=the` | `task_id`, `query`, `matches`, `total_matches` | `str`, `str`, `list`, `int` |
| `GET /translation/languages` | `pairs`, `count` | `list`, `int` |
| `GET /embed/presets` | `presets` | `dict` |
| `GET /health` | `status`, `uptime_sec` | `str`, `float/int` |

**Note:** `/tasks/duplicates` always returns 200 with the contract keys regardless of whether duplicates exist. A test using `filename=doesnotexist.wav&file_size=1` will return `{"duplicates_found": false, "matches": []}` — this is sufficient to assert both keys are present with correct types.

---

### `test_landing.py` — `@pytest.mark.smoke`

No actual file upload. Verifies entry point renders correctly.

**Text strings to assert must be verified against `frontend/src/components/landing/UploadZone.tsx` before writing tests.** As of 2026-03-18, the strings are:
- `"Drop your file here"` (line 98 of UploadZone.tsx)
- `"or click to browse"` (line 101)
- `"MP4, MKV, MOV, WAV, MP3, OGG, M4A, WEBM, SRT, VTT"` (line 107)
- `"Up to 2GB"` (line 110)

If these strings change, the tests must be updated. Prefer `data-testid` attributes over text matching for resilience — the implementation task should add `data-testid="upload-zone"`, `data-testid="format-hint"`, and `data-testid="size-hint"` to UploadZone.tsx.

```
- page.goto(base_url) → response status 200
- React root element (#root) has children (React mounted)
- "Drop your file here" text visible OR data-testid="upload-zone" present
- Supported formats hint visible
- "Up to 2GB" hint visible
- input[type=file] present in DOM
- ProjectGrid renders (data-testid="project-grid" present)
- Header present (data-testid="app-header" or nav element)
- No JS errors (page.on("pageerror") collects errors; assert empty)
```

---

### `test_upload_flow.py` — `@pytest.mark.upload`

Uses `unique_audio_file` for happy-path tests and `test_audio_file` for the duplicate detection test.

**Happy path (uses `unique_audio_file`):**
```
- page.goto(base_url)
- Set input[type=file] to unique_audio_file path
- UploadProgress component appears (data-testid="upload-progress" OR text contains filename)
- page.wait_for_url("**/editor/**", timeout=60_000)
- URL matches /editor/{uuid}
- Segment list renders (at least 1 segment visible)
```

**Duplicate detection (uses `test_audio_file`, uploads twice):**
```
Run 1: upload test_audio_file via input[type=file], wait for /editor/* URL, navigate back
Run 2: upload test_audio_file again
→ ConfirmDialog appears with text "Duplicate detected"
→ "Cancel" button visible; "Upload anyway" button visible
→ Click Cancel → URL remains at /; UploadZone reappears
Run 3: upload test_audio_file again
→ ConfirmDialog appears
→ Click "Upload anyway" → page.wait_for_url("**/editor/**", timeout=60_000)
→ Upload succeeded
```

**Edge cases:**
```
- Create tmp file with .exe extension → set on input[type=file]
  → Error toast appears (data-testid="toast" OR role="alert" with error text)
  → URL remains at /
- Create tmp file < 1KB with .wav extension → set on input[type=file]
  → Error toast appears with "size" or "range" in message text
  → URL remains at /
- No JS errors during any upload attempt
```

---

### `test_editor.py` — `@pytest.mark.editor`

Requires `completed_task_id` fixture. All tests navigate to `/editor/{completed_task_id}`.

**Session restore:**
```
- page.goto(f"{base_url}/editor/{completed_task_id}")
- Segment list visible (data-testid="segment-list" OR at least one segment row)
- At least one segment has timecode text matching HH:MM:SS format
- At least one segment has non-empty text content
- No JS errors
```

**Inline editing with persistence:**
```
- Click first segment row → textarea[rows="2"] appears
- Fill textarea with unique_text = f"edited_{uuid4().hex[:8]}"
- Click outside textarea (blur event)
- page.reload()  ← navigate away and back to verify server-side persistence
- First segment text contains unique_text
```

**Search:**
```
- Extract first word from first segment text (via page.text_content)
- Type that word into SearchBar input (data-testid="search-bar" or input[placeholder~="Search"])
- Wait for debounce (300ms)
- Assert at least one segment row has class containing "bg-yellow-50"
- Clear input
- Assert no segment rows have "bg-yellow-50"
```

**Download links:**
```
- Click DownloadMenu button (data-testid="download-menu" or button containing "Download")
- Assert link href containing f"/download/{completed_task_id}?format=srt" is visible
- Assert link href containing f"/download/{completed_task_id}?format=vtt" is visible
```

**No JS errors throughout**

---

### `test_static_pages.py` — `@pytest.mark.nav`

```
For each route in ["/status", "/about", "/security", "/contact"]:
  - page.goto(f"{base_url}{route}")
  - Response status 200
  - React root has children
  - Header present with nav links
  - Footer present (contentinfo landmark or data-testid="footer")
  - No JS errors

Navigation:
  - page.goto(base_url) → click About link → URL is /about
  - page.goto(base_url) → click Status link → URL is /status
  - page.go_back() → URL is /
  - page.go_forward() → URL is /status

Footer links from homepage:
  - For each footer link [About, Status, Security, Contact]:
    - click link → URL matches expected route
```

---

## Running the Suite

```bash
# Full suite — hits newui.openlabs.club
pytest tests/e2e_newui/ -v

# Against localhost
E2E_BASE_URL=http://localhost:8001 pytest tests/e2e_newui/ -v

# Contract tests only (no browser, CI-friendly)
pytest tests/e2e_newui/test_api_contracts.py -v -m contract

# Skip upload tests (no model preloaded)
pytest tests/e2e_newui/ -v -m "not upload"

# Use pre-existing completed task (skip transcription wait)
FIXTURE_TASK_ID=abc-123 pytest tests/e2e_newui/test_editor.py -v

# All E2E suites (old Lumen + new Drop, See, Refine)
pytest tests/e2e/ tests/e2e_newui/ -v
```

---

## CI Integration

### Contract tests (required status check)

`test_api_contracts.py` runs in every CI pipeline against a Docker service. The image is **built in the same job** before starting the service — it does not rely on a pre-published image.

```yaml
e2e-contracts:
  name: E2E Contract Tests
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Build app image
      run: docker build -t subtitle-generator-test:ci .

    - name: Start app service
      run: |
        docker run -d --name app -p 8001:8000 \
          -e ENVIRONMENT=dev subtitle-generator-test:ci
        # Wait for healthy
        for i in $(seq 1 30); do
          curl -sf http://localhost:8001/health && break || sleep 2
        done

    - name: Run contract tests
      run: |
        pip install pytest pytest-playwright requests
        E2E_BASE_URL=http://localhost:8001 \
          pytest tests/e2e_newui/test_api_contracts.py -v -m contract

    - name: Stop service
      if: always()
      run: docker stop app && docker rm app
```

This job becomes a **required status check** alongside `Lint` and `Test`. A merge cannot proceed if any contract assertion fails.

### Browser tests (manual dispatch / `run-e2e` label)

The full browser suite runs on manual dispatch or when the `run-e2e` label is applied to a PR. Not a required check for merge — browser tests depend on live server timing and model preload state.

---

## What This Would Have Caught

The 2026-03-18 deployment bug:
- Frontend called `dupeResult.duplicates.length` but backend returned `{ duplicates_found, matches }`
- `test_api_contracts.py::test_duplicates_response_shape` asserts:
  ```python
  assert "duplicates_found" in data
  assert isinstance(data["duplicates_found"], bool)
  assert "matches" in data
  assert isinstance(data["matches"], list)
  ```
- This test would have **failed in CI** before the PR merged, blocking the broken build from reaching `newui.openlabs.club`

---

## Out of Scope

- Performance/load testing (separate `Stress` engineer concern)
- Combine flow E2E (requires two files simultaneously; follow-up sprint)
- Local SRT editing flow (client-side only; covered by frontend unit tests)
- Mobile viewport testing (follow-up)
- Multi-language subtitle verification (requires real speech audio fixtures)
- GPU-accelerated model testing (CPU-only in CI)
