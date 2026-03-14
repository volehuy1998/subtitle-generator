# SubForge Frontend Architecture Review, Bug Report & Test Plan

Date: 2026-03-14

---

## 1. Frontend Architecture Review

### 1.1 Technology Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 19 (StrictMode) |
| Language | TypeScript |
| Build tool | Vite |
| State management | Zustand (2 stores) |
| Styling | Tailwind CSS + CSS custom properties (design tokens) |
| Real-time | Server-Sent Events (EventSource API) |
| File upload | XHR (XMLHttpRequest) for progress tracking |
| Drag & drop | react-dropzone |
| Testing | Vitest (unit), Playwright (e2e) |
| Mocking | MSW (Mock Service Worker) for dev mode |

### 1.2 Complete Component Tree

```
<StrictMode>
  <Router>                              # main.tsx -- custom SPA router
    |
    +-- useHealthStream()               # Global SSE connection to /health/stream
    |
    +-- <MainApp />                     # pages/App.tsx (path: /)
    |   +-- <ConnectionBanner />        # system/ -- offline/reconnecting/db-down/model-loading banners
    |   +-- <AppHeader />               # layout/ -- sticky header with logo, nav links, GPU badge, health indicator
    |   |   +-- <HealthDot />           # inline -- colored status dot
    |   |   +-- <LoadBar />             # inline -- CPU load mini progress bar
    |   +-- <HealthPanel />             # system/ -- dropdown panel (CPU, RAM, disk, GPU VRAM, DB status, alerts)
    |   |   +-- <StatBar />            # inline -- resource utilization bar
    |   +-- <main>
    |   |   +-- [Left column]
    |   |   |   +-- Tab header (Transcribe | Embed Subtitles)
    |   |   |   +-- <TranscribeForm />      # transcribe/ -- model table, language, translate, format, dropzone
    |   |   |   |   +-- <Skeleton />        # inline -- loading placeholder
    |   |   |   |   +-- useDropzone()       # react-dropzone hook
    |   |   |   +-- <ProgressView />        # progress/ -- active task monitoring
    |   |   |   |   +-- useSSE(taskId)      # hooks/ -- SSE event processing
    |   |   |   |   +-- <PipelineSteps />   # progress/ -- step indicator (Upload > Extract > Transcribe > [Translate] > Done)
    |   |   |   |   +-- Progress bar
    |   |   |   |   +-- Live segments preview (scrollable list)
    |   |   |   |   +-- Pause/Resume/Cancel controls
    |   |   |   +-- <EmbedTab />            # embed/ -- standalone video+subtitle embedding
    |   |   |       +-- <FilePicker />      # inline -- file input with button UI
    |   |   |       +-- <ModeSelector />    # embed/ -- soft mux vs hard burn radio buttons
    |   |   |       +-- <StyleOptions />    # embed/ -- color picker + font size slider + preview strip
    |   |   +-- [Right column]
    |   |       +-- <OutputPanel />         # output/ -- results sidebar (sticky on desktop)
    |   |           +-- <EmptyState />      # inline -- telescope illustration
    |   |           +-- <DownloadButtons /> # output/ -- SRT/VTT download links
    |   |           +-- <EmbedPanel />      # embed/ -- quick embed for completed video tasks
    |   |           +-- <TimingBreakdown /> # output/ -- collapsible timing table
    |   +-- <TaskQueuePanel />          # system/ -- fixed bottom-left collapsible task list
    |   |   +-- useTaskQueue(open)      # hooks/ -- polling /tasks every 2s when open
    |   +-- <footer>
    |
    +-- <StatusPage />                  # pages/ (path: /status)
    +-- <SecurityPage />                # pages/ (path: /security)
    +-- <AboutPage />                   # pages/ (path: /about)
    +-- <ContactPage />                 # pages/ (path: /contact)
        (all static pages use <StaticPageLayout> wrapper)
```

### 1.3 State Management

#### taskStore (Zustand)

File: `frontend/src/store/taskStore.ts`

Manages all state for the currently active transcription/embed task. Single-task model (one task at a time in the UI).

**State shape (26 fields):**

| Field | Type | Purpose |
|-------|------|---------|
| `taskId` | `string \| null` | Current task identifier; `'uploading'` during upload phase |
| `filename` | `string \| null` | Original filename |
| `fileSize` | `number \| null` | File size in bytes |
| `status` | `TaskStatus \| null` | Pipeline status (14 possible values) |
| `percent` | `number` | Progress 0-100 |
| `message` | `string` | Current status message |
| `isPaused` | `boolean` | Task paused flag |
| `isPauseRequesting` | `boolean` | Optimistic UI for pause request |
| `isCancelRequesting` | `boolean` | Optimistic UI for cancel request |
| `isComplete` | `boolean` | Task finished successfully |
| `error` | `string \| null` | Error message |
| `activeStep` | `number` | Pipeline step index (-1 = none) |
| `stepTimings` | `StepTimings` | Per-step timing data |
| `language` | `string \| null` | Detected/selected language |
| `segments` | `number` | Segment count |
| `totalTimeSec` | `number \| null` | Total processing time |
| `audioDuration` | `number \| null` | Audio length in seconds |
| `isVideo` | `boolean` | Whether the input is video (enables embed panel) |
| `speedFactor` | `number \| null` | Processing speed multiplier |
| `liveSegments` | `LiveSegment[]` | Real-time subtitle preview |
| `translatedTo` | `string \| null` | Translation target language |
| `isUploading` | `boolean` | Upload in progress |
| `uploadPercent` | `number` | Upload progress 0-100 |
| `downloadReady` | `boolean` | Downloads available |
| `embedDownloadUrl` | `string \| null` | Embedded video download path |
| `warning` | `string \| null` | Non-fatal warning message |

**Actions (16 methods):**
`setTaskId`, `setUploading`, `setUploadPercent`, `applyProgressData`, `addSegment`, `setLiveSegments`, `setStep`, `setComplete`, `setCancelled`, `setError`, `setPaused`, `setResumed`, `setPauseRequesting`, `setCancelRequesting`, `setWarning`, `setEmbedDownload`, `reset`

**Key design decisions:**
- `applyProgressData` uses shallow merge (`{ ...s, ...data }`) for flexible partial updates from SSE
- `setComplete` forces `status='done'`, `percent=100`, `isComplete=true`, `downloadReady=true` regardless of input
- `reset()` clears `localStorage('sg_currentTaskId')` and restores all fields to initial values
- `addSegment` appends to array (no deduplication) -- potential issue with SSE reconnection

#### uiStore (Zustand)

File: `frontend/src/store/uiStore.ts`

Manages UI chrome state shared across components.

**State shape (8 fields):**

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `appMode` | `'transcribe' \| 'embed'` | `'transcribe'` | Active tab |
| `embedMode` | `'soft' \| 'hard'` | `'soft'` | Embed mode selection |
| `healthPanelOpen` | `boolean` | `false` | Health dropdown visibility |
| `taskQueueOpen` | `boolean` | `false` | Task queue drawer |
| `sseConnected` | `boolean` | `false` | Health SSE connection status |
| `reconnecting` | `boolean` | `false` | Reconnection in progress |
| `dbOk` | `boolean` | `true` | Database connectivity |
| `health` | `HealthStatus \| null` | `null` | Latest health snapshot |

### 1.4 Hooks

#### `useSSE(taskId: string | null)`

File: `frontend/src/hooks/useSSE.ts`

Core real-time communication hook for task progress. Opens an EventSource to `/events/{taskId}`.

**Features:**
- Handles 13 SSE event types: `state`, `progress`, `step_change`, `segment`, `warning`, `done`, `paused`, `resumed`, `embed_progress`, `embed_done`, `embed_error`, `cancelled`, `critical_abort`, `heartbeat`
- Exponential backoff retry: 1s min, 30s max, doubles on each failure
- Watchdog timer: forces reconnect if no event received for 45 seconds (checks every 5s)
- On error: checks task status via `api.progress()` before retrying (handles done/cancelled/error)
- `translatedReset` flag: clears live segments once when first translated segment arrives
- Auto-closes on terminal events (`done`, `embed_done`, `embed_error`, `cancelled`, `critical_abort`)
- Skips connection when `taskId` is null or `'uploading'`

#### `useHealthStream(): HealthStatus | null`

File: `frontend/src/hooks/useHealthStream.ts`

Persistent SSE connection to `/health/stream` mounted once at the Router level.

**Features:**
- Grace period (2.5s) before showing offline banner -- absorbs brief disconnections
- Updates uiStore: `health`, `sseConnected`, `reconnecting`, `dbOk`
- Reconnects every 5s on error
- Has try/catch around JSON.parse (unlike useSSE)

#### `useTaskQueue(open: boolean): TaskListItem[]`

File: `frontend/src/hooks/useTaskQueue.ts`

Polls `/tasks` every 2s when the task queue panel is open.

**Features:**
- Only polls when `open === true`
- Cleans up interval on close/unmount
- Silently swallows errors (`.catch(() => {})`)

### 1.5 API Client

File: `frontend/src/api/client.ts`

Typed HTTP client wrapping `fetch` and `XMLHttpRequest`.

**Endpoints (16 methods):**

| Method | HTTP | Endpoint | Returns |
|--------|------|----------|---------|
| `systemInfo()` | GET | `/system-info` | `SystemInfo` |
| `languages()` | GET | `/languages` | `LanguagesResponse` |
| `upload(fd)` | POST | `/upload` | `UploadResponse` |
| `uploadWithProgress(fd, onProgress)` | POST (XHR) | `/upload` | `{ promise, abort }` |
| `progress(taskId)` | GET | `/progress/{taskId}` | `TaskProgress` |
| `tasks()` | GET | `/tasks` | `TasksResponse` |
| `cancel(taskId)` | POST | `/cancel/{taskId}` | `{ message }` |
| `pause(taskId)` | POST | `/pause/{taskId}` | `{ message }` |
| `resume(taskId)` | POST | `/resume/{taskId}` | `{ message }` |
| `health()` | GET | `/api/status` | `HealthStatus` |
| `embedQuick(taskId, fd)` | POST | `/embed/{taskId}/quick` | `EmbedResult` |
| `combineStart(fd)` | POST | `/combine` | `{ task_id, message }` |
| `combineStatus(taskId)` | GET | `/combine/status/{taskId}` | `CombineStatus` |
| `subtitles(taskId)` | GET | `/subtitles/{taskId}` | `SubtitlesResponse` |
| `translationLanguages()` | GET | `/translation/languages` | `TranslationLanguagesResponse` |
| `modelStatus()` | GET | `/api/model-status` | `ModelPreloadStatus` |

**URL generators (no fetch):** `downloadUrl(taskId, format)`, `embedDownloadUrl(taskId)`, `combineDownloadUrl(taskId)`

**Error handling:** The `json<T>()` helper checks `res.ok`, tries to parse error body for `detail` field, and throws an `Error`. The XHR variant in `uploadWithProgress` has separate handlers for load/error/abort.

### 1.6 Data Flow: Upload-to-Download

```
1. User drops file on TranscribeForm dropzone
2. App.handleUpload():
   a. store.reset() -- clear previous state
   b. store.setTaskId('uploading') -- sentinel value
   c. api.uploadWithProgress() -- XHR POST /upload
   d. XHR onprogress -> store.setUploadPercent()
   e. On success: store.setTaskId(result.task_id), save to localStorage
3. useSSE(taskId) activates (taskId changes from 'uploading' to real ID)
   a. Opens EventSource to /events/{taskId}
   b. progress/state events -> store.applyProgressData()
   c. step_change events -> store.setStep()
   d. segment events -> store.addSegment()
   e. done event -> store.setComplete(), save to localStorage, close SSE
4. OutputPanel renders:
   a. DownloadButtons with SRT/VTT links
   b. EmbedPanel (if isVideo) for subtitle embedding
   c. TimingBreakdown with per-step timings
5. User clicks "Process Another File" -> store.reset()
```

### 1.7 Real-Time SSE Architecture

**Two independent SSE connections:**

1. **Health stream** (`/health/stream`): Mounted once at Router level via `useHealthStream()`. Runs for the entire app lifetime. Feeds uiStore with system health data. Has a 2.5s grace period before showing offline banner.

2. **Task stream** (`/events/{taskId}`): Mounted per-task via `useSSE()` inside `ProgressView`. Opened when a real taskId is set, closed on terminal events. Has exponential backoff retry and 45s watchdog.

**SSE event type mapping:**

| SSE Event | Store Action | Effect |
|-----------|-------------|--------|
| `state` | `applyProgressData` + `setComplete` (if done) | Bulk state update |
| `progress` | `applyProgressData` + `setStep` | Progress/step update |
| `step_change` | `applyProgressData` + `setStep` | Pipeline step transition |
| `segment` | `setLiveSegments([])` (first translated) + `addSegment` | Live preview |
| `warning` | `setWarning` | Non-fatal warning banner |
| `done` | `setComplete` + localStorage save + close | Terminal |
| `paused` | `setPaused` | Pause confirmed |
| `resumed` | `setResumed` | Resume confirmed |
| `embed_progress` | `applyProgressData({message})` | Embed status |
| `embed_done` | `setEmbedDownload` + close | Terminal |
| `embed_error` | `setError` + close | Terminal |
| `cancelled` | `setCancelled` + localStorage remove + close | Terminal |
| `critical_abort` | `setError` + close | Terminal |
| `heartbeat` | (timestamp update only) | Keep-alive |

### 1.8 Routing

Custom SPA router in `main.tsx` using `history.pushState` + custom `'spa-navigate'` events.

**Route table:**

| Path | Component |
|------|-----------|
| `/` | `MainApp` (pages/App.tsx) |
| `/status` | `StatusPage` |
| `/security` | `SecurityPage` |
| `/about` | `AboutPage` |
| `/contact` | `ContactPage` |

Navigation is handled by preventing default link behavior and dispatching `spa-navigate` events. The Router listens to both `popstate` (browser back/forward) and `spa-navigate` events.

### 1.9 Styling Architecture

- **CSS custom properties** (design tokens) for all colors, shadows, fonts -- defined in `index.css`
- **Tailwind CSS** utility classes for layout, spacing, responsive design
- **Inline `style` attributes** for dynamic/token-based styling (colors, borders, backgrounds)
- **Responsive breakpoints**: Mobile-first, `sm:` (640px), `lg:` (1024px)
- **Animations**: Tailwind's `animate-pulse` (loading states), `animate-spin` (spinners), CSS `transition-all` for interactive elements
- Hover effects handled via `onMouseEnter`/`onMouseLeave` inline handlers (no CSS hover states)

### 1.10 Error Handling

- **API errors**: `json<T>()` wrapper throws `Error` with `detail` from response body
- **Upload errors**: Caught in `App.handleUpload()`, displayed via `store.setError()`
- **SSE parse errors in useHealthStream**: Wrapped in try/catch (errors silently ignored)
- **SSE parse errors in useSSE**: NOT wrapped in try/catch (see bugs section)
- **Network errors**: SSE reconnects with backoff; API calls generally swallow errors (`.catch(() => {})`)
- **Session restore errors**: Remove stale localStorage key on failure

---

## 2. Known Bugs & Issues

### BUG-1: Upload Cancellation Not Implemented (Severity: Medium)

**Location:** `frontend/src/pages/App.tsx` lines 94-116, `frontend/src/api/client.ts` lines 28-57

**Description:** The `uploadWithProgress` method returns an `abort` function, but `App.handleUpload()` never captures or uses it. The returned `{ promise, abort }` is destructured to only take `promise`. During the upload phase, there is no UI to cancel the upload, and even if there were, the XHR `abort()` is never called.

**Additional issue in abort implementation:** The `abort` function in `client.ts` (line 56) only calls `rejectFn(new Error('Upload cancelled'))` -- it rejects the promise but never calls `xhr.abort()`, so the actual network request continues in the background even if the promise is rejected.

```typescript
// client.ts line 56 -- abort() rejects promise but does NOT abort XHR
return { promise, abort: () => rejectFn?.(new Error('Upload cancelled')) }
```

**Fix required:**
1. Store a reference to the XHR object and call `xhr.abort()` in the abort function
2. Expose the abort handle in `handleUpload` and wire it to a cancel button during the upload phase

### BUG-2: SSE JSON Payload Validation Missing (Severity: High)

**Location:** `frontend/src/hooks/useSSE.ts` lines 39-121

**Description:** Every `JSON.parse()` call in the useSSE hook is unprotected. If the server sends malformed JSON (e.g., during a partial write, network truncation, or server error), the parse will throw and crash the event handler, potentially leaving the UI in an inconsistent state.

**Affected handlers (12 instances):**
- Line 41: `state` event
- Line 48: `progress` event
- Line 55: `step_change` event
- Line 63: `segment` event
- Line 74: `warning` event
- Line 80: `done` event
- Line 92: `embed_progress` event
- Line 97: `embed_done` event
- Line 104: `embed_error` event
- Line 118: `critical_abort` event

**Contrast:** `useHealthStream` (line 29) correctly wraps `JSON.parse` in try/catch.

**Fix required:** Wrap each `JSON.parse()` in a try/catch block, or extract a safe parse helper.

### BUG-3: Session Restore Race Condition (Severity: Medium)

**Location:** `frontend/src/pages/App.tsx` lines 21-68

**Description:** During session restore for in-progress tasks (lines 51-63), `store.setTaskId(savedTaskId)` is called which triggers `useSSE` to open an EventSource connection. Then `store.applyProgressData()` is called on the next line. There is a brief window where `useSSE` fires before the progress data is applied, meaning the UI briefly shows default state (0%, empty message) before the restored data appears.

For completed tasks (lines 27-50), `store.setTaskId()` triggers `useSSE` to open a connection to a finished task. The server may send a `done` event that redundantly re-triggers `setComplete()`, and then the component also calls `store.setComplete()` directly, causing a double-complete.

**Fix required:** Use `useTaskStore.setState()` to batch the taskId and progress data in a single update, preventing the intermediate state from being rendered.

### BUG-4: Embed Download Fallback Timing Too Aggressive (Severity: Low)

**Location:** `frontend/src/components/embed/EmbedPanel.tsx` lines 72-93

**Description:** When the SSE connection for embed tracking errors out, the code falls back to a HEAD request after a fixed 2-second delay (line 92). For large videos or slow servers, 2 seconds is insufficient. If the HEAD check fails, the user sees "Embedding may have failed" even though the operation is still in progress.

**Fix required:** Implement polling with progressive backoff instead of a single 2s check. Try HEAD at 2s, 5s, 10s, 20s before giving up.

### BUG-5: `translatedReset` Flag Lost on SSE Reconnection (Severity: Medium)

**Location:** `frontend/src/hooks/useSSE.ts` lines 60-69

**Description:** The `translatedReset` variable is declared inside the `connect()` function scope (line 60). When the SSE connection drops and reconnects, a new `connect()` call creates a fresh `translatedReset = false`. If translated segments were already being received before the reconnection, the reconnection will clear `liveSegments` again when the next translated segment arrives, losing any segments accumulated before the reconnect.

**Fix required:** Move `translatedReset` to a `useRef` so it persists across reconnections.

### BUG-6: Missing ARIA Attributes on Model Selector Table (Severity: Medium - Accessibility)

**Location:** `frontend/src/components/transcribe/TranscribeForm.tsx` lines 183-282

**Description:** The model selector table uses `<button>` elements styled as table rows but lacks:
- `role="radiogroup"` on the container
- `role="radio"` and `aria-checked` on each button
- `aria-label` describing the model characteristics
- Keyboard navigation (arrow keys to move between options)

The visual table header (`MODEL | SPEED / ACCURACY | PROS & CONS | VRAM`) uses plain `<span>` elements instead of semantic table markup or appropriate ARIA roles.

**Additional accessibility issues elsewhere:**
- Device selector buttons (lines 126-168): Missing `role="radiogroup"` / `aria-pressed`
- Format selector buttons (lines 360-376): Same issue
- Health panel close mechanism: Only responds to mouse clicks, no keyboard escape handler
- Nav links in AppHeader: `isActive` computed only on initial render (line 109), does not update on SPA navigation without full re-render of the component
- Progress bar: Missing `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- Live segments panel: Missing `aria-live="polite"` for screen reader updates

### BUG-7: `store` in useSSE Dependency Array Causes Latent Re-render Issue (Severity: Low)

**Location:** `frontend/src/hooks/useSSE.ts` line 154

**Description:** The `connect` callback includes `store` in its dependency array. Since `useTaskStore()` returns a new object reference on every render (Zustand selector pattern), `connect` is recreated on every render. The `useEffect` on line 156 has `[taskId]` as deps with an eslint-disable comment, which masks this issue. If the eslint-disable were removed and `connect` added to deps, it would cause infinite reconnection loops.

This is not currently causing visible bugs due to the eslint-disable, but it is a latent issue that could surface during refactoring.

---

## 3. Test Plan

### 3.1 Current Test Coverage Inventory

| Category | Count | Location |
|----------|-------|----------|
| Backend (pytest) | 1,326 tests | `tests/test_sprint*.py`, `tests/test_*.py` |
| Frontend store (Vitest) | 2 test files (26 test cases) | `frontend/src/store/__tests__/` |
| End-to-end (Playwright) | 7 test files | `tests/e2e/` |

**Backend tests:** Comprehensive coverage of all API routes, pipeline steps, services, middleware, database operations, security, rate limiting, and more. Organized by sprint (sprint1-sprint30) plus domain files.

**Frontend store tests:**
- `taskStore.test.ts` (14 test cases): Initial state, setTaskId, applyProgressData, addSegment, setStep, setComplete, setCancelled, setError, setPaused/setResumed, setWarning, setEmbedDownload, reset, state isolation
- `uiStore.test.ts` (8 test cases): Initial state, setAppMode, setEmbedMode, setHealthPanelOpen, setTaskQueueOpen, SSE connection sequence, field independence, state isolation

**E2E tests (Playwright):**
- `test_homepage.py`: Basic page load and element visibility
- `test_api.py`: API endpoint accessibility
- `test_health_panel.py`: Health panel toggle and content
- `test_status_page.py`: Status page navigation and content
- `test_control_buttons.py`: Pause/resume/cancel button visibility
- `test_translation_ui.py`: Translation dropdown presence
- `conftest.py`: Playwright fixtures and server setup

### 3.2 What Is NOT Tested

**React components (0% coverage):**
- TranscribeForm (model table, dropzone, selectors, loading skeletons, db-down state)
- ProgressView (progress bar, status text, controls, live segments, auto-scroll)
- PipelineSteps (step transitions, timing display, upload phase)
- OutputPanel (empty state, result display, metadata badges)
- EmbedTab (file pickers, mode selector, polling, progress, download)
- EmbedPanel (SSE embed tracking, HEAD fallback, translation select)
- ConnectionBanner (4 banner states: model loading, db down, reconnecting, offline)
- HealthPanel (resource bars, GPU info, alerts, outside-click dismiss)
- TaskQueuePanel (expand/collapse, task list rendering)
- AppHeader (nav links, GPU badge, health indicator, SPA navigation)
- DownloadButtons (link generation, hover effects)
- TimingBreakdown (collapsible, timing formatting)
- ModeSelector (radio behavior)
- StyleOptions (color picker, range slider, preview)

**Hooks (0% coverage):**
- useSSE: Event processing, reconnection logic, watchdog, error handling
- useHealthStream: Grace period timing, reconnection, health data parsing
- useTaskQueue: Polling lifecycle, interval cleanup

**API client (0% coverage):**
- `json<T>()` error extraction
- `uploadWithProgress` XHR behavior, progress callbacks, abort
- All fetch-based endpoint methods
- Error scenarios (network failure, 4xx, 5xx)

**Integration flows (0% coverage):**
- Full upload -> SSE -> completion flow
- Session restore from localStorage
- Tab switching during active task
- Embed flow (transcribe -> embed -> download)

**Accessibility (0% coverage):**
- Keyboard navigation through model table
- Screen reader announcements for progress updates
- Focus management on tab/panel transitions
- Color contrast validation

**Upload progress XHR (0% coverage):**
- XHR progress event firing
- XHR abort behavior
- XHR error scenarios
- Large file upload handling

### 3.3 Detailed Plan for New Tests

#### 3.3.a Component Rendering Tests

Framework: Vitest + React Testing Library (`@testing-library/react`)

**TranscribeForm:**
```
- renders loading skeletons while API calls are in flight
- renders device selector with GPU button when cuda_available=true
- renders device selector without GPU button when cuda_available=false
- renders all 5 model rows with correct labels (Tiny, Base, Small, Medium, Large)
- highlights selected model row with primary color border
- shows GPU fit indicator (Fits/X) for each model when GPU available
- renders language dropdown with auto-detect default
- populates language dropdown from /languages API response
- renders translation target dropdown from /translation/languages API
- renders format selector (SRT/VTT) with SRT default
- renders dropzone with correct accept types and 500MB limit
- calls onUpload with file and all selected options when file is dropped
- shows database unavailable state when dbOk=false
- disables all interactions when dbOk=false
- auto-selects CUDA device when cuda_available=true on initial load
```

**ProgressView:**
```
- renders filename and formatted file size
- renders "Done" badge when isComplete=true
- renders progress bar with correct width percentage
- applies correct color: primary (active), success (done), danger (error/cancelled), warning (paused)
- shows correct status text for each state (error msg, "Task cancelled.", "Paused", "Pausing after current segment...", message)
- renders live segments with formatted timestamps (M:SS format)
- auto-scrolls segments container when new segments arrive
- shows pause button with correct label (Pause/Pausing.../Resume/Resuming...)
- shows cancel button with confirmation dialog
- disables controls during pause/cancel requesting (opacity + not-allowed cursor)
- hides controls during upload phase (isUploading=true)
- renders "Try Again" button when status=cancelled
- renders "Process Another File" button when isComplete=true
- calls store.reset() and setAppMode('transcribe') on "Try Again" click
- shows warning banner when warning is set
```

**PipelineSteps:**
```
- renders 4 base steps (Upload, Extract, Transcribe, Done)
- renders 5 steps when stepTimings.translate is present
- highlights active step with primary color
- shows green checkmark for completed steps
- shows step number for pending steps
- displays formatted timing for completed steps (e.g., "1.5s", "2m 30s")
- shows upload percent during upload phase instead of timing
- applies warning color to active step when isPaused=true
- renders green connector lines between completed steps
```

**OutputPanel:**
```
- renders empty state with telescope illustration when no task complete
- renders filename and metadata badges (segments count, language, duration)
- renders SRT and VTT download buttons with correct hrefs
- renders "Process Next File" button that calls store.reset()
- renders EmbedPanel when isVideo=true
- hides EmbedPanel when isVideo=false
- renders TimingBreakdown with step timings
- shows translatedTo in metadata if present
```

**EmbedTab:**
```
- renders video and subtitle file pickers
- renders mode selector (soft/hard)
- shows style options only when hard mode selected
- renders translate dropdown with deduped targets
- enables embed button only when both files selected
- shows progress bar with percent during processing
- shows task ID snippet during processing
- shows success banner and download link on completion
- shows error message on failure
- shows "Start over" button after completion
- polls combine status during embedding at 1s intervals
- shows database unavailable when dbOk=false
```

**ConnectionBanner:**
```
- returns null when sseConnected=true, reconnecting=false, dbOk=true, no model loading
- shows model loading banner with model name, count, and progress bar
- shows database unavailable banner with role="alert" and aria-live="assertive"
- shows reconnecting banner (yellow) with role="status" and aria-live="polite"
- shows offline banner (red) with role="status"
- prioritizes model loading banner over connection issue banners
- prioritizes database down over reconnecting/offline
```

**HealthPanel:**
```
- renders "All systems operational" badge when status=ok/healthy
- renders "Performance degraded" badge when status=degraded/warning
- renders "System error" badge when status=error/critical
- renders "Connecting..." when health=null
- renders uptime in human-readable format (Xs, Xm Xs, Xh Xm)
- renders CPU, RAM, disk StatBars
- colors bars green (<65%), yellow (65-85%), red (>85%)
- shows disk free GB and "low" warning when disk_ok=false
- renders GPU name and VRAM bar when gpu_available=true
- shows "No GPU detected" warning with explanation when gpu_available=false
- renders database Connected/Error status
- renders alerts list when alerts present
- shows loading skeletons when health=null
- closes on outside click via mousedown handler
- does not close when clicking element with data-health-toggle
```

#### 3.3.b Hook Tests

Framework: Vitest + `@testing-library/react` renderHook + `vitest.useFakeTimers()`

**useSSE:**
```
- does not connect when taskId is null
- does not connect when taskId is 'uploading'
- opens EventSource to /events/{taskId} when valid taskId provided
- processes 'state' event and calls applyProgressData
- processes 'state' event with status=done and calls setComplete
- processes 'progress' event and calls applyProgressData
- processes 'progress' event with step field and calls setStep
- processes 'step_change' event and calls both applyProgressData and setStep
- processes 'segment' event and calls addSegment
- clears liveSegments on first translated segment (translatedReset behavior)
- does not clear liveSegments on subsequent translated segments
- processes 'done' event: calls setComplete with isVideo mapping, saves to localStorage, closes connection
- processes 'cancelled' event: calls setCancelled, removes localStorage, closes connection
- processes 'critical_abort' event: calls setError with message, closes connection
- processes 'warning' event: calls setWarning with message or warning field
- processes 'embed_progress' event: calls applyProgressData with message
- processes 'embed_done' event: calls setEmbedDownload with download_url, closes connection
- processes 'embed_error' event: calls setError with message, closes connection
- processes 'paused' event: calls setPaused
- processes 'resumed' event: calls setResumed
- processes 'heartbeat' event: updates lastEventTime without store changes
- on EventSource error: fetches task progress before retrying
- on error with done status from progress check: calls setComplete and closes
- on error with cancelled status: calls setCancelled and closes
- on error with error status: calls setError and closes
- on error with active status: retries with exponential backoff
- retry delay sequence: 1s, 2s, 4s, 8s, 16s, 30s, 30s (capped)
- resets retry delay to 1s on successful data receipt
- watchdog forces reconnect after 45s of silence
- watchdog checks every 5 seconds
- cleans up EventSource, retry timer, and watchdog on unmount
- cleans up and reconnects on taskId change
- close() prevents further reconnection attempts
```

**useHealthStream:**
```
- opens EventSource to /health/stream on mount
- parses health JSON data and calls setHealth on uiStore
- sets sseConnected=true on first message receipt
- sets dbOk from health.db_ok field
- clears offline timer on successful message receipt
- does not set reconnecting during grace period (first 2.5s after error)
- sets sseConnected=false and reconnecting=true after 2.5s grace period
- reconnects every 5s after error
- silently ignores JSON parse errors (try/catch)
- cleans up EventSource and offline timer on unmount
- does not leak timers on rapid mount/unmount
```

**useTaskQueue:**
```
- returns empty array initially
- does not make API calls when open=false
- starts polling /tasks every 2s when open=true
- updates returned tasks array with API response data
- stops polling when open changes from true to false
- cleans up interval on unmount
- silently handles API errors (no thrown exceptions)
- resumes polling when open changes back to true
```

#### 3.3.c API Client Tests

Framework: Vitest + MSW (Mock Service Worker)

```
json() helper:
- returns parsed JSON body on 2xx response
- throws Error with detail field from error body on 4xx response
- throws Error with statusText when error body JSON parse fails
- throws Error with statusText on 5xx response with no body

Endpoint methods:
- systemInfo(): sends GET to /system-info, returns typed SystemInfo
- languages(): sends GET to /languages, returns LanguagesResponse
- upload(fd): sends POST to /upload with FormData body, returns UploadResponse
- progress(taskId): sends GET to /progress/{taskId}, returns TaskProgress
- tasks(): sends GET to /tasks, returns TasksResponse
- cancel(taskId): sends POST to /cancel/{taskId}, returns { message }
- pause(taskId): sends POST to /pause/{taskId}, returns { message }
- resume(taskId): sends POST to /resume/{taskId}, returns { message }
- health(): sends GET to /api/status, returns HealthStatus
- embedQuick(taskId, fd): sends POST to /embed/{taskId}/quick with FormData, returns EmbedResult
- combineStart(fd): sends POST to /combine with FormData, returns { task_id, message }
- combineStatus(taskId): sends GET to /combine/status/{taskId}, returns CombineStatus
- subtitles(taskId): sends GET to /subtitles/{taskId}, returns SubtitlesResponse
- translationLanguages(): sends GET to /translation/languages, returns TranslationLanguagesResponse
- modelStatus(): sends GET to /api/model-status, returns ModelPreloadStatus

URL generators:
- downloadUrl(taskId, 'srt'): returns '/download/{taskId}?format=srt'
- downloadUrl(taskId, 'vtt'): returns '/download/{taskId}?format=vtt'
- downloadUrl(taskId, 'json'): returns '/download/{taskId}?format=json'
- embedDownloadUrl(taskId): returns '/embed/download/{taskId}'
- combineDownloadUrl(taskId): returns '/combine/download/{taskId}'

uploadWithProgress:
- sends POST to /upload via XMLHttpRequest
- reports upload progress percentage via onProgress callback
- resolves promise with parsed response on success (2xx)
- rejects with Error containing detail on server error (4xx/5xx)
- rejects with 'Network error' on XHR onerror
- rejects with 'Upload cancelled' on XHR onabort
- abort() function is returned and can be called
```

#### 3.3.d Integration Tests

Framework: Vitest + React Testing Library + MSW

```
Upload Flow End-to-End:
- complete flow: select model -> drop file -> see upload progress -> SSE events fire -> completion screen -> download links visible
- upload failure shows error state with message
- upload with translation sends translate_to parameter in FormData
- can start new task after completion (reset clears all state and returns to form)
- error during SSE shows error state with retry option

SSE -> Store -> UI Integration:
- progress events update progress bar width in DOM
- step_change events advance pipeline step indicator
- segment events appear as new items in live preview list
- done event transitions to completion state with download buttons
- error event shows error message and hides progress controls
- cancelled event shows "Try Again" button and hides progress bar
- paused event changes pause button to "Resume"
- warning event shows yellow warning banner below progress bar

Session Restore:
- restores completed task from localStorage on page load (shows output panel with downloads)
- restores in-progress task from localStorage (reconnects SSE and shows progress)
- clears stale localStorage entry when task not found on server (404)
- does not restore cancelled tasks (stays on form)
- does not restore errored tasks (stays on form)
- fetches and restores subtitle segments for completed tasks

Embed Flow:
- transcribe video -> completion -> click "Embed & Download" in output panel -> SSE embed events -> download embedded video
- embed panel shows translation dropdown when not already translated
- embed panel hides translation dropdown when alreadyTranslated=true
- embed SSE error falls back to HEAD check
- standalone embed tab: upload video + subtitle -> embed -> poll -> download
```

#### 3.3.e Performance Tests

Framework: Vitest + React Testing Library + custom timing utilities

```
Concurrent State Updates:
- multiple rapid applyProgressData calls do not cause store corruption
- rapid addSegment calls (100 in 100ms) all appear in liveSegments
- reset during active SSE processing clears state cleanly

SSE Under Load:
- handles rapid burst of segment events (100+ in 1 second) without dropped events
- handles reconnection with accumulated segments (no data loss)
- watchdog does not fire false positives during heavy event processing (events arriving < 45s apart)
- back-to-back error/reconnect cycles do not leak EventSource instances

Segment Rendering:
- renders 100 segments within 100ms
- renders 500 segments within 500ms
- renders 1000+ segments (document actual rendering time)
- auto-scroll performance with 1000+ segments (no layout thrashing)
- memory usage stays bounded with 5000+ segments (no unbounded growth)

Component Re-render Efficiency:
- model table rows do not re-render when language/format/translateTo changes (requires React.memo)
- segment list items do not re-render when progress percent changes
- OutputPanel does not re-render when live segments update during transcription
- health panel updates do not trigger re-render of TranscribeForm/ProgressView
```

#### 3.3.f Accessibility Tests

Framework: Vitest + React Testing Library + `jest-axe` (aXe-core integration)

```
Keyboard Navigation:
- Tab moves focus through all interactive elements in TranscribeForm in logical order
- Arrow keys navigate between model rows (requires radiogroup implementation)
- Enter/Space activates buttons and selects options
- Escape closes HealthPanel dropdown
- Escape closes TaskQueuePanel
- Tab order follows visual layout (device -> model -> language -> translate -> format -> dropzone)
- Focus visible indicator on all interactive elements

ARIA Attributes:
- model selector container has role="radiogroup" with aria-label="Select model"
- model row buttons have role="radio" with aria-checked matching selection state
- device selector buttons have aria-pressed matching selection state
- format selector buttons have aria-pressed matching selection state
- progress bar div has role="progressbar" with aria-valuenow, aria-valuemin=0, aria-valuemax=100
- live segments container has aria-live="polite" for screen reader updates
- connection banners have correct role (alert for errors, status for info)
- health panel has aria-label="System health"
- dropzone has aria-label describing accepted file types
- all SVG icons have aria-hidden="true" (already present in most cases)

Screen Reader Compatibility:
- progress updates announced via aria-live region when percent changes
- task completion announced (status change to "done")
- error messages announced immediately (aria-live="assertive")
- warning messages announced
- model selection change announced
- connection status changes announced via banner role attributes

aXe Automated Checks:
- no critical accessibility violations on TranscribeForm
- no critical accessibility violations on ProgressView
- no critical accessibility violations on OutputPanel
- no critical accessibility violations on EmbedTab
- no critical accessibility violations on HealthPanel
- color contrast passes WCAG AA for all text elements
```

### 3.4 Bug Fix Priorities

| Priority | Bug | Effort | Impact |
|----------|-----|--------|--------|
| **P0** | BUG-2: SSE JSON parse unprotected | Low (add try/catch wrapper) | Crashes UI on malformed server data |
| **P1** | BUG-1: Upload abort not implemented | Medium (fix XHR abort + add cancel UI) | Users cannot cancel large uploads |
| **P1** | BUG-5: translatedReset lost on reconnect | Low (move to useRef) | Duplicate segment clearing on reconnect |
| **P2** | BUG-3: Session restore race condition | Low (use setState batch) | Brief inconsistent state on reload |
| **P2** | BUG-6: Missing ARIA on model table | Medium (add roles + keyboard nav) | Accessibility compliance failure |
| **P3** | BUG-4: Embed HEAD fallback timing | Low (add retry loop) | False failure on slow embeds |
| **P3** | BUG-7: store in useSSE deps | Low (use selector or getState) | Latent issue, no current symptoms |

---

## 4. Optimization Methods

### 4.1 React.memo for Heavy Components

**Problem:** Model table rows in TranscribeForm re-render on every parent state change (device, language, format, translateTo). Each row computes GPU fit, builds complex JSX with SVGs.

**Solution:** Extract model rows into a memoized component:

```typescript
const ModelRow = React.memo(function ModelRow({
  model, info, isActive, gpuFit, onClick
}: ModelRowProps) {
  // ... existing row JSX
})
```

**Also apply to:**
- `LiveSegment` items in ProgressView (re-render only when segment data changes)
- `TaskQueuePanel` task items (re-render only on individual task changes)
- `StatBar` in HealthPanel (re-render only when value changes)

**Expected impact:** Reduce unnecessary re-renders during progress updates. Most impactful when 100+ live segments are displayed.

### 4.2 Debounce Segment Auto-Scroll

**Problem:** `ProgressView` calls `scrollIntoView({ behavior: 'smooth' })` on every `liveSegments.length` change (line 44-46). During transcription, segments arrive rapidly (every 1-5 seconds), causing continuous smooth-scroll animations that can jank the UI and overlap.

**Solution:**

```typescript
const scrollDebounce = useRef<ReturnType<typeof setTimeout> | null>(null)

useEffect(() => {
  if (scrollDebounce.current) clearTimeout(scrollDebounce.current)
  scrollDebounce.current = setTimeout(() => {
    segmentsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, 200)
}, [liveSegments.length])
```

**Expected impact:** Reduces scroll calls from every segment to at most 5/second. Eliminates overlapping smooth-scroll animations.

### 4.3 Batch SSE State Updates

**Problem:** Several SSE event handlers make multiple store calls per event. For example, the `progress` handler (useSSE line 47-50) calls both `applyProgressData` and `setStep`, triggering two React re-renders. SSE events fire outside React's event system, so React 18's automatic batching does not apply.

**Solution option A -- combined store actions:**

```typescript
// In taskStore:
applyProgressWithStep: (data: Partial<TaskState>, step?: number) => set((s) => ({
  ...s, ...data,
  ...(step !== undefined ? { activeStep: step } : {}),
}))
```

**Solution option B -- explicit batching:**

```typescript
import { unstable_batchedUpdates } from 'react-dom'

es.addEventListener('progress', (e) => {
  onData()
  const data = JSON.parse((e as MessageEvent).data)
  unstable_batchedUpdates(() => {
    store.applyProgressData(data)
    if (data.step !== undefined) store.setStep(data.step)
  })
})
```

**Expected impact:** Reduces re-renders by approximately 40% during active transcription. Each SSE event triggers one render instead of two.

### 4.4 Virtualize Long Segment Lists

**Problem:** The live preview in ProgressView renders ALL segments in the DOM. For a 2-hour recording with 2000+ segments, this creates 2000+ DOM nodes inside a 200px scrollable container. Only ~8-10 segments are visible at any time.

**Solution:** Use `@tanstack/react-virtual` to virtualize the segment list:

```typescript
import { useVirtualizer } from '@tanstack/react-virtual'

const parentRef = useRef<HTMLDivElement>(null)
const rowVirtualizer = useVirtualizer({
  count: liveSegments.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 24,
  overscan: 10,
})

// Render only visible rows
{rowVirtualizer.getVirtualItems().map((virtualRow) => {
  const seg = liveSegments[virtualRow.index]
  return (
    <div key={virtualRow.index} style={{
      position: 'absolute',
      top: virtualRow.start,
      height: virtualRow.size,
    }}>
      <span>{formatTimestamp(seg.start)}</span>
      <span>{seg.text}</span>
    </div>
  )
})}
```

**Expected impact:** Reduces DOM nodes from O(n) to O(visible + overscan), approximately 30 nodes regardless of total segment count. Critical for recordings longer than 30 minutes.

### 4.5 Add try/catch Around All JSON.parse in SSE Handlers

**Problem:** See BUG-2. All 12 JSON.parse calls in useSSE are unprotected.

**Solution:** Create a safe parse helper:

```typescript
function safeParse<T = Record<string, unknown>>(data: string): T | null {
  try {
    return JSON.parse(data) as T
  } catch {
    console.warn('[SSE] Failed to parse event data:', data.slice(0, 100))
    return null
  }
}

// Usage in each handler:
es.addEventListener('state', (e) => {
  onData()
  const data = safeParse((e as MessageEvent).data)
  if (!data) return
  store.applyProgressData(data)
  if (data.status === 'done') store.setComplete(data)
})
```

**Expected impact:** Prevents UI crashes from malformed SSE data. Zero performance cost. Should be applied to all 12 event handlers.

### 4.6 Implement Proper Upload abort()

**Problem:** See BUG-1. The abort function rejects the promise but does not abort the underlying XHR.

**Solution:**

```typescript
uploadWithProgress: (fd: FormData, onProgress: (percent: number) => void) => {
  const xhr = new XMLHttpRequest()
  const promise = new Promise<UploadResponse>((resolve, reject) => {
    xhr.open('POST', '/upload')
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100))
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText))
      } else {
        try {
          const err = JSON.parse(xhr.responseText)
          reject(new Error(err.detail ?? xhr.statusText))
        } catch {
          reject(new Error(xhr.statusText))
        }
      }
    }
    xhr.onerror = () => reject(new Error('Network error'))
    xhr.onabort = () => reject(new Error('Upload cancelled'))
    xhr.send(fd)
  })
  return { promise, abort: () => xhr.abort() }  // Actually abort the XHR
}
```

Then in `App.handleUpload`, store the abort handle and expose a cancel button during the upload phase:

```typescript
const abortRef = useRef<(() => void) | null>(null)

// In handleUpload:
const { promise, abort } = api.uploadWithProgress(fd, onProgress)
abortRef.current = abort

// Render cancel button when isUploading:
{isUploading && (
  <button onClick={() => { abortRef.current?.(); store.reset() }}>
    Cancel Upload
  </button>
)}
```

**Expected impact:** Users can cancel uploads of large files (up to 500MB), immediately freeing bandwidth and server resources.

### 4.7 Fix Session Restore Ordering

**Problem:** See BUG-3. Setting taskId and progress data in separate calls creates a race condition with useSSE.

**Solution:** Use Zustand's `setState` to apply all restoration data atomically:

```typescript
// For in-progress tasks:
useTaskStore.setState({
  taskId: savedTaskId,
  filename: data.filename ?? null,
  fileSize: data.file_size ?? null,
  status: data.status,
  percent: data.percent,
  message: data.message,
})

// For completed tasks, set a flag to prevent useSSE from connecting:
useTaskStore.setState({
  taskId: savedTaskId,
  filename: data.filename ?? null,
  // ... all completion data
  status: 'done',
  percent: 100,
  isComplete: true,
  downloadReady: true,
})
```

For completed tasks, useSSE should check `isComplete` and skip connecting:

```typescript
// In useSSE:
if (!taskId || taskId === 'uploading' || closed.current) return
const currentState = useTaskStore.getState()
if (currentState.isComplete) return  // Don't connect for completed tasks
```

**Expected impact:** Eliminates flash of empty state on page reload. Prevents unnecessary SSE connections for completed tasks.

---

## Summary of Recommendations

### Immediate (This Sprint)

1. **BUG-2 fix**: Add try/catch around JSON.parse in useSSE -- prevents crashes from malformed SSE data
2. **BUG-1 fix**: Fix upload abort to actually call xhr.abort() -- functional gap affecting all users
3. **BUG-5 fix**: Move translatedReset to useRef -- one-line fix preventing duplicate segment clearing

### Short Term (Next 2 Sprints)

4. Add component rendering tests for TranscribeForm and ProgressView -- highest-value coverage gap
5. Add hook tests for useSSE -- most complex untested code path
6. **BUG-6 fix**: Add ARIA attributes to model selector and other interactive elements
7. Implement segment list virtualization for long recordings
8. Debounce auto-scroll in ProgressView
9. Batch SSE state updates to reduce re-renders

### Medium Term (Next Quarter)

10. Complete component test coverage for all 14 components
11. Add API client tests with MSW
12. Add integration tests for full upload and embed flows
13. Performance benchmarks for large segment counts (1000+)
14. Accessibility audit with aXe-core
15. **BUG-3 fix**: Batch session restore state updates
16. **BUG-4 fix**: Add retry loop for embed HEAD fallback

### Infrastructure

17. Set up Vitest coverage reporting in CI with minimum threshold (e.g., 60% for new code)
18. Add MSW handlers for all API endpoints to support component testing
19. Consider replacing custom SPA router with a lightweight router (e.g., wouter) for proper route params, lazy loading, and 404 handling

---

## 5. Git Workflow & Project Standards

### 5.1 Current State (Before)

| Aspect | Status |
|--------|--------|
| Commit format | Informal imperative ("Add...", "Fix..."), no structured convention |
| Branching | Single `main` branch, all work direct to main |
| Hooks | 1 custom post-commit (security assertions tracking) |
| Linting | ruff (Python), eslint (TS) — no commit lint |
| PR templates | None |
| Contributing guide | None |
| Versioning | None (no tags, no semver) |

### 5.2 Adopted Standards

#### 5.2.1 Commit Convention: Conventional Commits v1.0.0

All commits MUST follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types** (mandatory):

| Type | When to use | Example |
|------|------------|---------|
| `feat` | New feature or user-facing capability | `feat(transcribe): add live segment preview during transcription` |
| `fix` | Bug fix | `fix(sse): prevent reconnection loop when task is already done` |
| `refactor` | Code change that neither fixes a bug nor adds a feature | `refactor(pipeline): extract model loading into separate step` |
| `perf` | Performance improvement | `perf(whisper): reduce beam size for CPU to improve speed` |
| `test` | Adding or updating tests | `test(store): add taskStore upload state tests` |
| `docs` | Documentation only | `docs: update CLAUDE.md with translation architecture` |
| `style` | Formatting, whitespace, no code change | `style(routes): fix import ordering` |
| `ci` | CI/CD changes | `ci: add frontend vitest coverage to pipeline` |
| `build` | Build system or dependency changes | `build(docker): multi-stage build with frontend` |
| `chore` | Maintenance, tooling, config | `chore: update ruff to 0.8.x` |
| `security` | Security fix or hardening | `security(middleware): add rate limit to upload endpoint` |

**Scopes** (optional but recommended):

| Scope | Covers |
|-------|--------|
| `pipeline` | app/services/pipeline.py, transcription flow |
| `transcribe` | Whisper transcription, model loading |
| `translate` | Translation (Whisper + Argos) |
| `embed` | Subtitle embedding (soft/hard) |
| `sse` | Server-sent events, WebSocket, real-time |
| `api` | Route handlers, REST endpoints |
| `db` | Database, migrations, task backend |
| `auth` | Authentication, API keys, sessions |
| `middleware` | All middleware modules |
| `health` | Health checks, monitoring, critical state |
| `ui` | Frontend components, pages |
| `store` | Zustand stores (taskStore, uiStore) |
| `hooks` | React hooks (useSSE, useHealthStream) |
| `docker` | Dockerfile, docker-compose |
| `deploy` | Deployment scripts, infrastructure |
| `config` | Configuration, environment variables |

**Breaking changes**: Add `!` after type/scope and `BREAKING CHANGE:` footer:
```
feat(api)!: change upload response schema

BREAKING CHANGE: upload response now returns `task_id` instead of `id`
```

#### 5.2.2 Branching Strategy: GitHub Flow

```
main (protected, always deployable)
  │
  ├── feat/upload-progress-bar
  ├── fix/sse-reconnection-loop
  ├── refactor/model-preload-background
  └── security/rate-limit-upload
```

**Rules:**
- `main` is always deployable. Never push directly to main (except hotfixes).
- Create a branch from `main` for every change. Branch name: `<type>/<short-description>`.
- Open a Pull Request. CI must pass. At least 1 review (when team > 1).
- Squash merge to main. Delete branch after merge.
- Tag releases with semver: `v2.1.0`, `v2.1.1`.

**Branch naming convention:**
```
feat/model-preload-status
fix/embed-download-fallback
refactor/pipeline-step-timer
test/sse-reconnection
docs/api-swagger-tags
ci/frontend-coverage
security/clamav-scan-timeout
```

#### 5.2.3 Architecture Standards

**Backend (Python 3.12 + FastAPI):**

| Area | Standard |
|------|----------|
| Framework | FastAPI with async lifespan, Pydantic v2 schemas |
| ORM | SQLAlchemy 2.0 async (asyncpg for PostgreSQL, aiosqlite fallback) |
| Migrations | Alembic with auto-generated revisions |
| Validation | Pydantic models for all request/response schemas |
| Logging | Structured logging via `logging_setup.py`, one logger per domain |
| Error handling | HTTPException for client errors, global exception handler for 500s |
| Testing | pytest + httpx.AsyncClient + ASGI transport (no running server) |
| Linting | `ruff check . --select E,F,W --ignore E501` |
| Type hints | Required for all public functions; `Optional[]` for nullable params |
| Module pattern | One router per domain in `app/routes/`, one service per domain in `app/services/` |
| Config | All settings in `app/config.py`, env vars with sensible defaults |
| Security | Input validation at boundaries, sanitize filenames, magic bytes check |
| Concurrency | `asyncio.to_thread()` for blocking I/O, `threading.Semaphore` for task limits |

**Frontend (React 19 + TypeScript + Vite 6):**

| Area | Standard |
|------|----------|
| Framework | React 19 with functional components + hooks |
| Language | TypeScript (strict mode via `tsc -b`) |
| Build | Vite 6, production build via `tsc -b && vite build` |
| State | Zustand (no Redux, no Context for global state) |
| Styling | Tailwind CSS v4 + CSS variables for theming |
| Real-time | EventSource (SSE) with exponential backoff + watchdog |
| API client | Typed fetch wrapper in `api/client.ts` (no axios) |
| Testing | Vitest + Testing Library + MSW for API mocking |
| Components | One component per file, co-located in feature folders |
| Types | All API responses typed in `api/types.ts` |
| Routing | Custom SPA router via `pushState` + custom events |

**Infrastructure:**

| Area | Standard |
|------|----------|
| Containerization | Docker with multi-stage build (node builder → python runtime) |
| Orchestration | Docker Compose with profiles (cpu/gpu) |
| CI/CD | GitHub Actions: lint → test → build (3 stages) |
| Database | PostgreSQL (production), SQLite (development/fallback) |
| Cache/Queue | Redis (Pub/Sub, Celery broker, rate limiting) |
| Storage | Local filesystem (default), S3/MinIO (multi-server) |
| TLS | Managed externally (certbot/ACME), injected via volume mount |
| Monitoring | Built-in health checks, /api/status SSE stream |

#### 5.2.4 Code Review Checklist

Every PR should be checked against:

- [ ] Follows Conventional Commits for all commit messages
- [ ] No secrets or credentials in code (`.env`, API keys, tokens)
- [ ] New routes registered in `app/routes/__init__.py`
- [ ] New schemas added to `app/schemas.py`
- [ ] Backend tests added/updated for changed endpoints
- [ ] Frontend types updated in `api/types.ts` if API changed
- [ ] No `console.log` left in frontend code
- [ ] `ruff check` passes (backend)
- [ ] `tsc -b && vite build` passes (frontend)
- [ ] `pytest tests/` passes (backend, excluding e2e)
- [ ] No new TypeScript `any` types
- [ ] Middleware order preserved in `app/main.py`
- [ ] SSE events documented if new event types added

#### 5.2.5 Version & Release Strategy

**Semantic Versioning (semver):**
```
MAJOR.MINOR.PATCH
  │      │     └── Bug fixes, patches (no API change)
  │      └──────── New features, backward-compatible
  └─────────────── Breaking changes
```

Current version: `2.0.0` (from `app/main.py` FastAPI version).

**Release process:**
1. Merge all PRs for the release into `main`
2. Update version in `app/main.py` and `frontend/package.json`
3. Create annotated git tag: `git tag -a v2.1.0 -m "feat: upload progress, model preload, transcription details"`
4. Push tag: `git push origin v2.1.0`
5. CI builds and publishes Docker image tagged with version

#### 5.2.6 PR Template

```markdown
## Summary
<!-- 1-3 bullet points describing the change -->

## Type
<!-- Check one -->
- [ ] feat — New feature
- [ ] fix — Bug fix
- [ ] refactor — Code restructure
- [ ] perf — Performance improvement
- [ ] test — Tests only
- [ ] docs — Documentation only
- [ ] ci — CI/CD changes
- [ ] security — Security fix

## Changes
<!-- List specific files/modules changed and why -->

## Test Plan
<!-- How was this tested? -->
- [ ] Unit tests pass (`pytest tests/`)
- [ ] Frontend tests pass (`npm run test`)
- [ ] Manual testing done
- [ ] E2E tested (if applicable)

## Screenshots
<!-- If UI changes, add before/after screenshots -->
```

### 5.3 Implementation Steps

**Phase 1 — Immediate (this session):**
1. ~~Document standards in class.md~~ (done)
2. Add commitlint config for Conventional Commits enforcement
3. Add PR template to `.github/PULL_REQUEST_TEMPLATE.md`

**Phase 2 — Next session:**
4. Add pre-commit hook: ruff + frontend lint
5. Add commit-msg hook: validate Conventional Commits format
6. Set up branch protection rules on GitHub (require PR, require CI)
7. Create initial semver tag for current state

**Phase 3 — Ongoing:**
8. Retroactively tag past releases based on git history
9. Add CONTRIBUTING.md referencing these standards
10. Set up automated changelog generation from Conventional Commits

---

## 6. Google Software Engineering Standards

This section maps practices from Google's engineering culture to the SubForge project, drawing primarily from *Software Engineering at Google* (Winters, Manshreck, Wright, 2020), the *Google SRE Book* (Beyer et al., 2016), Google's public style guides (https://google.github.io/styleguide/), and the release-please automation tool (https://github.com/googleapis/release-please).

### 6.1 Code Review (Google Engineering Practices)

Google treats code review as the single most important quality gate. Their publicly documented guidelines (https://google.github.io/eng-practices/) define three distinct approval dimensions and strict turnaround expectations.

**Three approval dimensions:**

| Dimension | What the reviewer checks | SubForge mapping |
|-----------|------------------------|------------------|
| **Correctness** | Does the code do what it claims? Are there bugs, race conditions, edge cases? | Any reviewer can approve correctness |
| **Ownership** | Does this change belong in this part of the codebase? Does it fit the module architecture? | Module owners (route owner, service owner) approve ownership |
| **Readability** | Does the code follow style, conventions, and idioms? Is it maintainable? | Readability-approved reviewers (those who know the project conventions) |

**Key practices to adopt:**

- **Small CLs (changelists):** Target < 400 lines per PR. Research shows reviewer effectiveness drops sharply after 400 lines. Large changes should be split into stacked PRs (e.g., refactor first, then feature, then tests).
- **One business day turnaround:** Reviews should be completed within one business day. If you cannot review in time, reassign or acknowledge with an ETA.
- **"Nit:" prefix:** Use `Nit:` for non-blocking style suggestions that the author can choose to address or ignore. This reduces review friction by clearly separating must-fix from nice-to-have.
- **CODEOWNERS file:** GitHub's CODEOWNERS mechanism auto-assigns reviewers based on file paths, implementing Google's concept of per-directory ownership.

**Action items for SubForge:**
- Add a `CODEOWNERS` file mapping module paths to owners:
  ```
  # Backend
  /app/services/pipeline.py    @backend-lead
  /app/services/transcription.py @backend-lead
  /app/routes/                 @backend-lead
  /app/middleware/              @backend-lead
  /app/db/                     @backend-lead

  # Frontend
  /frontend/src/               @frontend-lead

  # Infrastructure
  /docker-compose.yml          @infra-lead
  /.github/                    @infra-lead
  /deploy/                     @infra-lead
  ```
- Enforce PR size warnings: add a CI check or GitHub Action that warns when a PR exceeds 400 lines changed.
- Document the three approval dimensions in the PR template so reviewers know what to look for.

### 6.2 Testing (Google Test Pyramid)

Google's testing philosophy is built around the test pyramid, size-based classification, and pragmatic rules like the Beyonce Rule.

**Test pyramid target ratios:**

| Layer | Target % | SubForge current state | What it covers |
|-------|----------|----------------------|----------------|
| Unit (Small) | ~80% | ~1300 tests in pytest, most are unit-level | Individual functions, classes, pure logic |
| Integration (Medium) | ~15% | Some ASGI transport tests against FastAPI app | Module interactions, API contracts, DB queries |
| E2E (Large) | ~5% | Playwright tests in `tests/e2e/` | Full browser flows, upload-to-download |

**Test size definitions (Google internal classification):**

| Size | Constraints | Time limit | SubForge examples |
|------|------------|------------|-------------------|
| **Small** | No I/O, no network, no disk, no sleep. Single process, single thread. | < 60 seconds | `test_srt.py`, `test_formatting.py`, pure function tests |
| **Medium** | Localhost only (no external services). Can use disk, localhost network. | < 300 seconds | `test_api.py` (ASGI transport), `test_combine.py`, DB tests |
| **Large** | Can access external services, real network, real GPU. | < 900 seconds | `tests/e2e/` (Playwright), full pipeline with real Whisper model |

**The Beyonce Rule:** "If you liked it, then you shoulda put a test on it." If a behavior matters to your system, it must be covered by an automated test. Unwritten expectations are not contracts -- only tested behavior is guaranteed. This is especially relevant for SubForge's SSE event protocol, pipeline step ordering, and error handling paths.

**DAMP over DRY in tests:** Google prefers tests that are "Descriptive and Meaningful Phrases" over "Don't Repeat Yourself." Test code should prioritize clarity over abstraction. Each test should be readable in isolation without jumping to shared helpers. Duplication in tests is acceptable when it makes the test self-documenting.

**Flaky test target:** Google targets a flaky test rate below 0.15%. A flaky test is one that passes and fails without any code change. Flaky tests erode confidence in CI and train developers to ignore red builds. Track flaky tests explicitly and fix or quarantine them within one week.

**Action items for SubForge:**
- Add pytest markers for test sizes:
  ```python
  # conftest.py
  import pytest

  def pytest_configure(config):
      config.addinivalue_line("markers", "small: unit tests, no I/O (< 60s)")
      config.addinivalue_line("markers", "medium: integration tests, localhost only (< 300s)")
      config.addinivalue_line("markers", "large: e2e tests, may use external services (< 900s)")
  ```
- Mark existing tests with `@pytest.mark.small`, `@pytest.mark.medium`, or `@pytest.mark.large`.
- Configure fast presubmit to run only small tests: `pytest -m small`.
- Add flaky test tracking: log test results over time and flag tests that fail intermittently.
- Apply the Beyonce Rule to SSE event contracts, pipeline step ordering, and translation fallback paths.

### 6.3 Documentation (Docs as Code)

Google classifies documentation into five types, each serving a different audience and purpose. Documentation is treated as code: it lives in the repository, is reviewed in PRs, and is tested for freshness.

**Five documentation types:**

| Type | Purpose | SubForge example |
|------|---------|-----------------|
| **Reference** | API docs, function signatures, parameter descriptions | Swagger/OpenAPI auto-generated from FastAPI route docstrings |
| **Design docs** | Explain *why* a system works the way it does, trade-offs considered | Architecture decisions (e.g., why Zustand over Redux, why SSE over WebSocket-only) |
| **Tutorials** | Step-by-step guides for new users | "How to transcribe your first file" walkthrough |
| **Conceptual** | Explain concepts needed to understand the system | Pipeline flow explanation, translation modes comparison |
| **Landing pages** | Navigation hubs that point to other docs | CLAUDE.md serves this role currently |

**Google Python docstring style:**
```python
def transcribe_audio(file_path: str, model_size: str = "base", language: str | None = None) -> list[dict]:
    """Transcribe an audio file using faster-whisper.

    Loads or reuses a cached model, extracts audio to WAV if needed,
    and runs transcription with beam search.

    Args:
        file_path: Absolute path to the input audio or video file.
        model_size: Whisper model size (tiny/base/small/medium/large).
        language: ISO 639-1 language code, or None for auto-detection.

    Returns:
        List of segment dicts with keys: start, end, text, words.

    Raises:
        FileNotFoundError: If file_path does not exist.
        TranscriptionError: If whisper fails to process the audio.
    """
```

**Comments explain WHY, not WHAT:** Code should be self-documenting for *what* it does. Comments are reserved for *why* a particular approach was chosen, non-obvious constraints, or workarounds. Bad: `# increment counter`. Good: `# Retry up to 3 times because the model loader occasionally fails on first load due to a CTranslate2 race condition`.

**Action items for SubForge:**
- Add module-level docstrings to all files in `app/routes/` and `app/services/` explaining the module's responsibility and key behaviors.
- Adopt Google-style docstrings (Args/Returns/Raises) for all public functions.
- Audit existing comments: remove "what" comments, add "why" comments where trade-offs or workarounds exist.
- Treat CLAUDE.md as the landing page; add links to design docs for major subsystems (pipeline, translation, embedding).

### 6.4 Style Guides

Google maintains language-specific style guides that are publicly available. The key principle: 90% of style rules should be auto-enforced by tooling, so code reviews focus on logic rather than formatting.

**Google Python Style Guide key rules (https://google.github.io/styleguide/pyguide.html):**

| Rule | Current SubForge state | Action |
|------|----------------------|--------|
| Import ordering (stdlib, third-party, local) | Not enforced | Enable ruff rule `I` (isort) |
| No wildcard imports (`from x import *`) | Not enforced | Enable ruff rule `F403` (already in `F` selection) |
| Naming: `snake_case` functions/vars, `PascalCase` classes | Followed by convention | No change needed |
| Type hints on all public functions | Partial | Add mypy or pyright to CI |
| Logging with `%s` format, not f-strings | Not followed (f-strings used in logging) | Enable ruff rule `G` (logging-format) |
| No bare `except:` | Not enforced | Enable ruff rule `E722` (already in `E` selection) |
| Avoid mutable default arguments | Not enforced | Enable ruff rule `B006` via `B` (bugbear) |
| Use `collections.abc` for type hints, not `typing` | Not enforced | Enable ruff rule `UP` (pyupgrade) |

**Google TypeScript Style Guide key rules (https://google.github.io/styleguide/tsguide.html):**

| Rule | Current SubForge state | Action |
|------|----------------------|--------|
| Use `interface` over `type` for object shapes | Mixed usage | Add ESLint rule `@typescript-eslint/consistent-type-definitions` |
| `const` by default, `let` only when reassignment needed | Mostly followed | No change needed |
| No `any` type | PR checklist item, not enforced | Make `@typescript-eslint/no-explicit-any` an error |
| Named exports over default exports | Mixed usage | Add ESLint rule `import/no-default-export` |
| Use `readonly` for properties that should not change | Not enforced | Add `@typescript-eslint/prefer-readonly` |

**Tooling enforcement target (90% auto-enforced):**

| Tool | Purpose | Current | Target |
|------|---------|---------|--------|
| `ruff check` | Python linting | `E,F,W` rules only | Add `I,B,UP,SIM,G` rule sets |
| `ruff format` | Python formatting | Not used | Enable, replace manual formatting |
| ESLint | TypeScript linting | Configured but not blocking CI | Make blocking in CI |
| mypy or pyright | Python type checking | Not configured | Add to CI with gradual strictness |
| Prettier | Frontend formatting | Not configured | Add for consistent TS/CSS formatting |

**Action items for SubForge:**
- Expand ruff configuration to include rules `I` (import sorting), `B` (bugbear), `UP` (pyupgrade), `SIM` (simplification), and `G` (logging format).
- Enable `ruff format` for consistent Python formatting.
- Make ESLint a blocking CI check (fail the build on warnings).
- Add mypy or pyright with gradual strictness (start with `--ignore-missing-imports`, tighten over time).

### 6.5 CI/CD (Presubmit/Post-submit)

Google splits CI into two stages: a fast presubmit that runs before merge, and a comprehensive post-submit that runs after merge. The key insight is that presubmit must be fast enough that developers never skip it.

**Presubmit (< 2 minutes):**
- Lint checks (ruff, ESLint, tsc)
- Small (unit) tests only
- Commit message format validation
- Security scanning (no secrets in diff)

**Post-submit (runs on main after merge):**
- Full test suite (small + medium + large)
- Code coverage calculation and threshold enforcement
- Docker build verification
- Dependency vulnerability scanning (pip-audit, npm audit)
- Performance benchmarks (optional, track regressions)

**Hermetic testing:** Tests should be fully self-contained and not depend on external state, network services, or execution order. SubForge already does this well with `sys.modules` patching for torch/whisper mocks and ASGI transport for API tests.

**Configuration as code:** All CI configuration lives in version-controlled files (`.github/workflows/`), never in CI platform UI settings. Build steps should be reproducible locally.

**Action items for SubForge:**
- Split the current CI pipeline into two stages:
  - **Fast presubmit:** `ruff check` + `tsc -b` + `pytest -m small` (target < 2 min)
  - **Full post-submit:** All tests + coverage + Docker build + `pip-audit` + `npm audit`
- Add `pytest -m small` as the presubmit test command.
- Add `pytest --cov=app --cov-fail-under=70` to post-submit for coverage enforcement.
- Ensure all CI steps can be run locally with a single `make ci-fast` or `make ci-full` command.

### 6.6 SRE Practices (Four Golden Signals)

Google's SRE book defines four golden signals that every service should monitor. These signals, combined with SLOs and error budgets, form the foundation of reliable operations.

**Four Golden Signals:**

| Signal | What to measure | SubForge implementation |
|--------|----------------|------------------------|
| **Latency** | Time to serve a request (p50, p95, p99) | Track per-route response times in `app/services/analytics.py`. Separate successful vs failed request latency. |
| **Traffic** | Requests per second by endpoint | Already tracked via analytics counters. Add per-route breakdown. |
| **Errors** | Error rate by type (4xx client, 5xx server, timeout) | Track via middleware. Separate validation errors (expected) from server errors (unexpected). |
| **Saturation** | Resource utilization approaching limits | Already monitored: CPU, RAM, disk, VRAM via `health_monitor.py`. Add task queue depth (semaphore utilization). |

**SLIs, SLOs, and SLAs:**

| Term | Definition | SubForge example |
|------|-----------|-----------------|
| **SLI** (Service Level Indicator) | A quantitative measure of service behavior | "Percentage of /upload requests completing in < 5s" |
| **SLO** (Service Level Objective) | A target value for an SLI | "99.5% of uploads complete in < 5s over a 30-day window" |
| **SLA** (Service Level Agreement) | A contract with consequences for missing SLOs | Not applicable (internal service), but SLOs still drive prioritization |

**Proposed SLOs for SubForge:**

| SLO | Target | Measurement |
|-----|--------|-------------|
| Upload availability | 99.5% of uploads accepted (non-5xx) over 30 days | Error rate on POST /upload |
| Transcription success rate | 99% of transcriptions complete without error | Pipeline completion rate |
| API latency (non-transcription) | p99 < 500ms for health, download, status endpoints | Per-route latency tracking |
| SSE delivery | 99.9% of pipeline events delivered to connected clients | Event delivery confirmation |

**Error budgets:** If the SLO is 99.5% availability, the error budget is 0.5% (approximately 3.6 hours of downtime per month). When the error budget is nearly exhausted, freeze feature work and focus on reliability. When the error budget is healthy, invest in features.

**Blameless postmortems:** When incidents occur, conduct a blameless postmortem focused on systemic causes, not individual blame. Document: what happened, timeline, root cause, what went well, what could be improved, and action items with owners. Store postmortems in a `postmortems/` directory in the repository.

**Action items for SubForge:**
- Define SLOs for the four golden signals (see proposed SLOs above).
- Add latency percentile tracking (p50/p95/p99) to the analytics service, broken down by route.
- Add task queue saturation metric: `active_tasks / MAX_CONCURRENT_TASKS`.
- Create a postmortem template in `.github/POSTMORTEM_TEMPLATE.md`:
  ```markdown
  # Postmortem: [Incident Title]
  **Date:** YYYY-MM-DD
  **Duration:** X hours
  **Impact:** [What was affected, how many users]

  ## Timeline
  - HH:MM — [Event]

  ## Root Cause
  [Systemic cause, not individual blame]

  ## What Went Well
  - [Thing that helped]

  ## What Could Be Improved
  - [Process gap]

  ## Action Items
  - [ ] [Action] — Owner: @person — Due: YYYY-MM-DD
  ```

### 6.7 Dependency Management

Google is famously skeptical of external dependencies, governed by the principle of Hyrum's Law: "With a sufficient number of users of an API, all observable behaviors of your system will be depended on by somebody." This means that even patch-version upgrades can break your system if you depend on undocumented behavior.

**Key practices:**

- **Pin exact versions:** Use `==` in `requirements.txt`, not `>=` or `~=`. Lock files (`package-lock.json`) must be committed. Reproducible builds require deterministic dependency resolution.
- **Audit for vulnerabilities:** Run `pip-audit` (Python) and `npm audit` (Node.js) in CI. Block merges on known high/critical CVEs.
- **SemVer skepticism (Hyrum's Law):** Do not trust that a minor or patch version bump is backward-compatible. Always test after dependency upgrades. Treat every upgrade as potentially breaking.
- **Minimize dependency count:** Every dependency is a liability (maintenance burden, security surface, build complexity). Before adding a dependency, ask: can we write this in < 100 lines? Is the dependency actively maintained? Does it pull in a large transitive tree?

**Action items for SubForge:**
- Pin all versions in `requirements.txt` to exact versions (`faster-whisper==1.1.0`, not `faster-whisper>=1.0`).
- Commit `frontend/package-lock.json` (already done) and verify it is up to date.
- Add `pip-audit` to CI post-submit stage:
  ```yaml
  - name: Audit Python dependencies
    run: pip install pip-audit && pip-audit -r requirements.txt
  ```
- Add `npm audit` to CI post-submit stage:
  ```yaml
  - name: Audit Node dependencies
    run: cd frontend && npm audit --audit-level=high
  ```
- Configure Dependabot (`.github/dependabot.yml`) for automated dependency update PRs:
  ```yaml
  version: 2
  updates:
    - package-ecosystem: "pip"
      directory: "/"
      schedule:
        interval: "weekly"
    - package-ecosystem: "npm"
      directory: "/frontend"
      schedule:
        interval: "weekly"
  ```

### 6.8 Version Control (Trunk-Based Development)

Google practices trunk-based development: all developers work off a single main branch, with short-lived feature branches that merge back quickly. This minimizes merge conflicts and integration pain.

**Key practices:**

- **Short-lived branches (< 1 week):** Branches that live longer than a week accumulate merge conflicts and integration risk. If a feature takes longer than a week, break it into smaller increments that can be merged independently.
- **Small commits:** Each commit should represent a single logical change. This makes bisecting easier, code review faster, and reverts safer. Target < 400 lines per commit (same as PR size guidance).
- **Feature flags over long branches:** Instead of keeping a feature branch alive until the feature is complete, merge incomplete features behind a flag. This keeps main moving forward and allows testing in production without exposing unfinished work.
  ```python
  # app/config.py
  ENABLE_SPEAKER_DIARIZATION = os.getenv("ENABLE_SPEAKER_DIARIZATION", "true").lower() == "true"
  ENABLE_BATCH_UPLOAD = os.getenv("ENABLE_BATCH_UPLOAD", "false").lower() == "true"  # WIP feature
  ```
- **release-please for automated versioning:** Google's open-source tool `release-please` (https://github.com/googleapis/release-please) automates version bumps and changelog generation from Conventional Commits. It creates a "release PR" that, when merged, tags the release and generates a GitHub Release with a changelog.

**Action items for SubForge:**
- Configure release-please via GitHub Action:
  ```yaml
  # .github/workflows/release.yml
  name: Release
  on:
    push:
      branches: [main]
  jobs:
    release:
      runs-on: ubuntu-latest
      steps:
        - uses: googleapis/release-please-action@v4
          with:
            release-type: python
            package-name: subforge
  ```
- Tag the current state as `v2.0.0` (initial release baseline).
- Tag the next release as `v2.1.0` after merging current pending work (multi-model preload, distributed deploy).
- Enforce the one-week branch lifetime: add a CI check or bot that warns on branches older than 7 days.

### 6.9 Deprecation

Google's philosophy on deprecation is captured in the principle: "Code is a liability, not an asset." Every line of code has a maintenance cost: it must be understood, tested, secured, and migrated when dependencies change. Removing code is always a net positive if the code is no longer needed.

**Two deprecation modes:**

| Mode | Description | SubForge example |
|------|------------|-----------------|
| **Advisory** | Mark as deprecated with warnings, provide migration path, remove after grace period | Deprecating an old API endpoint version while the new one is available |
| **Compulsory** | Set a hard removal deadline, actively migrate callers, remove on schedule | Removing a feature flag after the feature is fully launched |

**Deprecation process:**
1. **Identify:** Find unused or redundant code through usage analytics, test coverage gaps, and code review.
2. **Announce:** Mark with `@deprecated` decorator/comment, log warnings on use, update docs.
3. **Migrate:** Move callers to the replacement. Provide examples.
4. **Remove:** Delete the code, remove tests, update imports.

**Action items for SubForge:**
- Audit for dead code: identify routes, services, and utility functions that are never called or tested.
- Check for unused routes: compare `app/routes/__init__.py` registrations against actual frontend API calls in `frontend/src/api/client.ts`.
- Check for unused services: look for service modules that are imported but never called from routes or pipeline.
- Remove or consolidate redundant endpoints (e.g., if both polling and SSE provide the same data, consider deprecating polling).
- Add a `@deprecated` decorator for Python functions scheduled for removal:
  ```python
  import warnings
  import functools

  def deprecated(reason: str):
      def decorator(func):
          @functools.wraps(func)
          def wrapper(*args, **kwargs):
              warnings.warn(
                  f"{func.__name__} is deprecated: {reason}",
                  DeprecationWarning,
                  stacklevel=2,
              )
              return func(*args, **kwargs)
          return wrapper
      return decorator
  ```

### 6.10 Priority Action Items

Ranked by impact-to-effort ratio, organized into three time horizons.

**Immediate (this session):**

| Action | Effort | Impact | Reference |
|--------|--------|--------|-----------|
| Add `*.pem` to `.gitignore` | 1 min | Prevents accidental secret commit | 6.7 Dependency Management |
| Create `CODEOWNERS` file | 5 min | Auto-assigns reviewers, enforces ownership | 6.1 Code Review |
| Enable `ruff format` | 5 min | Consistent Python formatting, eliminates style debates | 6.4 Style Guides |
| Make ESLint blocking in CI | 5 min | Catches TypeScript issues before merge | 6.4 Style Guides |

**Short-term (this month):**

| Action | Effort | Impact | Reference |
|--------|--------|--------|-----------|
| Split CI into fast presubmit / full post-submit | 2 hours | Faster PR feedback loop (< 2 min presubmit) | 6.5 CI/CD |
| Pin all dependency versions | 1 hour | Reproducible builds, prevents surprise breakage | 6.7 Dependency Management |
| Add pytest markers `@pytest.mark.small/medium/large` | 2 hours | Enables fast presubmit with small tests only | 6.2 Testing |
| Add `pip-audit` + `npm audit` to CI | 30 min | Catches known vulnerabilities automatically | 6.7 Dependency Management |
| Add type annotations to all public functions | 4 hours | Better IDE support, catches bugs at development time | 6.4 Style Guides |

**Medium-term (this quarter):**

| Action | Effort | Impact | Reference |
|--------|--------|--------|-----------|
| Define and measure SLOs for four golden signals | 1 week | Data-driven reliability decisions, error budgets | 6.6 SRE Practices |
| Add mypy/pyright to CI (gradual strictness) | 1 week | Catches type errors, improves maintainability | 6.4 Style Guides |
| Add property-based testing (Hypothesis) for formatters | 3 days | Finds edge cases in SRT/VTT generation | 6.2 Testing |
| Create incident runbook and postmortem template | 2 days | Structured incident response, blameless culture | 6.6 SRE Practices |
| Implement golden signals dashboard (latency percentiles, error rates, saturation) | 1 week | Real-time visibility into service health | 6.6 SRE Practices |

**References:**
- *Software Engineering at Google* (Winters, Manshreck, Wright, O'Reilly, 2020) — Chapters on code review, testing, deprecation, dependency management, version control
- *Site Reliability Engineering* (Beyer, Jones, Petoff, Murphy, O'Reilly, 2016) — Chapters on monitoring, SLOs, error budgets, postmortems
- Google Python Style Guide: https://google.github.io/styleguide/pyguide.html
- Google TypeScript Style Guide: https://google.github.io/styleguide/tsguide.html
- Google Engineering Practices (Code Review): https://google.github.io/eng-practices/
- release-please: https://github.com/googleapis/release-please
