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
├── conftest.py              # Fixtures: base_url, browser context, test audio file
├── pytest.ini               # asyncio_mode=auto, test markers
├── fixtures/
│   └── sample.wav           # ~50KB audio fixture for live upload tests
├── test_landing.py          # UploadZone UI, ProjectGrid, format hints — no upload
├── test_upload_flow.py      # Live file upload, duplicate dialog, progress, cancel
├── test_editor.py           # Subtitle editing, search, download, session restore
├── test_api_contracts.py    # HTTP-only response shape assertions
└── test_static_pages.py     # Status, About, Security, Contact; nav; footer
```

---

## Fixtures (`conftest.py`)

```python
@pytest.fixture(scope="session")
def base_url():
    return os.environ.get("E2E_BASE_URL", "https://newui.openlabs.club")

@pytest.fixture(scope="session")
def browser_context(playwright, base_url):
    # Auto-skip entire suite if server is unreachable
    try:
        requests.get(base_url, timeout=5, verify=False)
    except Exception:
        pytest.skip(f"Server unreachable: {base_url}")
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(ignore_https_errors=True)
    yield context
    context.close()
    browser.close()

@pytest.fixture(scope="session")
def page(browser_context):
    p = browser_context.new_page()
    yield p
    p.close()

@pytest.fixture(scope="session")
def test_audio_file():
    return Path(__file__).parent / "fixtures" / "sample.wav"
```

The `sample.wav` fixture is a generated ~50KB silent WAV file that ships with the repository. No external files required.

---

## Test Files

### `test_api_contracts.py` — HTTP only, no browser

The dedicated contract layer. Catches API shape mismatches before the browser layer runs. Fast (~2s total).

| Endpoint | Required fields |
|---|---|
| `GET /tasks/duplicates` | `duplicates_found` (bool), `matches` (list) |
| `POST /upload` | `task_id` (str), `model_size` (str), `language` (str) |
| `GET /progress/{id}` | `task_id`, `status`, `percent`, `message` |
| `GET /subtitles/{id}` | `task_id`, `segments` (list of `{start, end, text}`) |
| `GET /search/{id}` | `task_id`, `query`, `results` (list of `{index, ...}`) |
| `GET /translation/languages` | `pairs` (list), `count` (int) |
| `GET /embed/presets` | `presets` (list of `{name, label, description}`) |
| `GET /health` | `status`, `uptime_sec` |

Each test issues a real HTTP request and asserts the response JSON has the required keys with the correct types. No mocking. A failure here means the frontend will break — fix the endpoint or fix the client before shipping.

---

### `test_landing.py` — page load and upload zone UI

No actual file upload. Verifies the entry point renders correctly.

```
- Page loads with HTTP 200, React mounts (root element has children)
- "Drop your file here" text visible
- "or click to browse" text visible
- Supported formats hint: MP4, MKV, MOV, WAV, MP3, OGG, M4A, WEBM, SRT, VTT
- Size limit hint: "Up to 2GB"
- Clicking the UploadZone opens file picker (input[type=file] is present)
- ProjectGrid renders (empty state message OR project cards visible)
- Header present with SubForge branding
- Health indicator present in header
- ConnectionBanner absent when server is healthy
- No JS errors on page load
```

---

### `test_upload_flow.py` — live file upload with `sample.wav`

Uses the `test_audio_file` fixture for live uploads against the server.

**Happy path:**
```
- Drop sample.wav → UploadProgress component appears with filename visible
- Progress bar advances (percent > 0 within 5s)
- Pipeline steps update during processing
- On completion → URL changes to /editor/{task_id}
- Editor page renders with segment list
```

**Duplicate detection (the bug we fixed):**
```
- Upload same file twice
- Second upload → ConfirmDialog appears: "Duplicate detected"
- Dialog has "Upload anyway" and "Cancel" buttons
- Click Cancel → UploadZone reappears (upload aborted)
- Upload again → click "Upload anyway" → upload proceeds to /editor/{task_id}
```

**Edge cases:**
```
- Drop file with unsupported extension (.exe) → error toast appears, no upload
- Drop file smaller than 1KB → error toast "File size out of range"
- Start upload → click Cancel button → UploadZone reappears
- No JS errors during any upload attempt
```

---

### `test_editor.py` — subtitle editing, search, download

Depends on a known completed `task_id` stored in a session fixture (populated by `test_upload_flow.py` or a pre-seeded fixture task).

**Session restore:**
```
- Navigate to /editor/{task_id} directly
- Segment list renders with timecodes and text
- At least one segment visible
- No JS errors on load
```

**Inline editing:**
```
- Click a segment row → textarea appears (editing mode)
- Type new text in textarea
- Click outside (blur) → text persists on re-render
- Segment text updated in the list
```

**Search:**
```
- Type a word present in subtitles into SearchBar
- Matching segments highlighted (bg-yellow-50 class present)
- Match count badge shows > 0
- Clear search input → highlights removed
```

**Download:**
```
- DownloadMenu button visible in EditorToolbar
- Click Download → SRT option visible
- Click Download → VTT option visible
- SRT download link is a valid /download/{id}?format=srt URL
```

**No JS errors throughout**

---

### `test_static_pages.py` — static pages, navigation, footer

```
/status   → loads, shows component statuses (Transcription Engine, etc.), no JS errors
/about    → loads, page content visible, no JS errors
/security → loads, page content visible, no JS errors
/contact  → loads, page content visible, no JS errors

Navigation:
- All pages have Header with nav links
- Clicking About → navigates to /about
- Clicking Status → navigates to /status
- Browser back → returns to previous page
- Browser forward → re-navigates correctly

Footer:
- Footer visible on every page
- Footer contains links: About, Status, Security, Contact
- Footer links navigate to correct routes
```

---

## Running the Suite

```bash
# Full suite — hits newui.openlabs.club
pytest tests/e2e_newui/ -v

# Against localhost (CI or local dev server)
E2E_BASE_URL=http://localhost:8001 pytest tests/e2e_newui/ -v

# Contract tests only (fastest, no browser, CI-friendly)
pytest tests/e2e_newui/test_api_contracts.py -v

# Specific scenario
pytest tests/e2e_newui/test_upload_flow.py -v -k "duplicate"

# All E2E suites (old + new)
pytest tests/e2e/ tests/e2e_newui/ -v
```

---

## CI Integration

### Contract tests (required check)
`test_api_contracts.py` runs in CI against `http://localhost:8001` using a Docker service spun up from the same image. These are fast (~2s), have no external dependency, and become a **required status check** — a merge cannot proceed if any contract assertion fails.

### Browser tests (optional / manual dispatch)
The full browser suite (`test_landing.py`, `test_upload_flow.py`, `test_editor.py`, `test_static_pages.py`) runs on manual dispatch or when the `run-e2e` label is applied to a PR. Not a required check for merge — they need a live server with model preloaded and depend on network timing.

### New CI job (added to `ci.yml`)
```yaml
e2e-contracts:
  name: E2E Contract Tests
  runs-on: ubuntu-latest
  services:
    app:
      image: subtitle-generator:latest
      ports: ["8001:8000"]
  steps:
    - run: E2E_BASE_URL=http://localhost:8001 pytest tests/e2e_newui/test_api_contracts.py -v
```

---

## What This Would Have Caught

The 2026-03-18 deployment bug:
- Frontend called `dupeResult.duplicates.length` but backend returned `duplicates_found` / `matches`
- `test_api_contracts.py::test_duplicates_response_shape` would assert `assert "duplicates_found" in data` and `assert "matches" in data`
- This test would have **failed in CI** before the PR merged, blocking the broken build from reaching `newui.openlabs.club`

---

## Out of Scope

- Performance/load testing (separate `Stress` engineer concern)
- Combine flow E2E (requires two files; added in a follow-up)
- Local SRT editing flow (client-side only; covered by frontend unit tests)
- Mobile viewport testing (follow-up)
- Multi-language subtitle verification (requires real audio fixtures with speech)
