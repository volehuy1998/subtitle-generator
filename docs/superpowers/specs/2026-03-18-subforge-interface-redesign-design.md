# SubForge Interface Redesign — "Drop, See, Refine"

**Date:** 2026-03-18
**Author:** Atlas (Tech Lead), Team Sentinel
**Status:** Approved (brainstorming complete)
**Replaces:** Previous workspace/step-bar spec (anchored on old UI — discarded)
**Deployment target:** `newui.openlabs.club` (promote to production after investor approval)

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Visual Identity](#2-visual-identity)
3. [Information Architecture](#3-information-architecture)
4. [Landing Page](#4-landing-page)
5. [Editor Page](#5-editor-page)
6. [Component Architecture](#6-component-architecture)
7. [State Architecture](#7-state-architecture)
8. [Backend Integration](#8-backend-integration)
9. [Responsive Behavior](#9-responsive-behavior)
10. [Animations & Interactions](#10-animations--interactions)
11. [Accessibility](#11-accessibility)

---

## 1. Design Philosophy

### "Drop, See, Refine"

Three principles derived from research, not from the existing UI:

**1. Zero friction to first result**

Drop a file, see subtitles. No configuration, no model selection, no account required. Smart defaults handle everything. Refine after you see results, not before.

Research basis:
- 70% of new users churn before engaging with core features (Rubyroid Labs 2026)
- Users who experience value in <5 minutes show 40% higher 30-day retention (Rework 2026)
- "It's difficult for users to decide on preferences before they've even used the product" (Rubyroid Labs 2026)
- Each Required Decision costs 2 friction points (Baymard Institute)

**2. The editor is the product**

After transcription, the user lands in a subtitle editor. Every action (download, translate, embed, re-transcribe) is accessible from the editor. The editor is the hub, not a side feature.

Research basis:
- Every successful competitor (Descript, Sonix, VEED, Kapwing, Happy Scribe, Simon Says) makes the editor the core post-transcription experience
- Subtitle editors have evolved into core features in 2026 transcription SaaS, particularly for enterprise
- Descript's entire product IS the transcript editor

**3. Adaptive, not modal**

The interface adapts to what the user gives it. No mode selection, no tabs, no explicit workflow choice. The upload zone IS the router.

Research basis:
- 2026 UX shift to Orchestrated User Interfaces (OUI) — system detects intent, assembles interface dynamically (UX Collective 2026)
- Kapwing, VEED, Descript all auto-detect file type and adapt workflow
- "The concept of a static interface where every user sees the same menu options is becoming obsolete" (UX Collective 2026)

### SubForge's unique advantage

`POST /tasks/{task_id}/retranscribe` — re-transcribe with different parameters without re-uploading. No competitor offers this for free. This makes "smart defaults first, upgrade later" zero-risk: bad model choice? One click to redo. The UI must exploit this.

---

## 2. Visual Identity

### "Cool Professional"

Investor criteria: not too bright, not dark, enterprise-grade. Matches GitHub, Atlassian, Microsoft 365.

### Color System

**Foundation & Surfaces:**

| Token | Value | Usage |
|-------|-------|-------|
| `--color-bg` | `#F3F4F6` (gray-100) | Page foundation |
| `--color-surface` | `#FFFFFF` | Cards, panels, editor |
| `--color-border` | `#E5E7EB` (gray-200) | Subtle borders |
| `--color-border-strong` | `#D1D5DB` (gray-300) | Dividers, active borders |

**Text:**

| Token | Value | Usage |
|-------|-------|-------|
| `--color-text` | `#111827` (gray-900) | Primary text |
| `--color-text-secondary` | `#4B5563` (gray-600) | Labels, supporting |
| `--color-text-muted` | `#6B7280` (gray-500) | Timestamps, metadata |
| `--color-text-placeholder` | `#9CA3AF` (gray-400) | Input placeholders |

**Brand:**

| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary` | `#2563EB` (blue-600) | CTAs, active states, links |
| `--color-primary-hover` | `#1D4ED8` (blue-700) | Hover |
| `--color-primary-light` | `rgba(37,99,235,0.08)` | Active backgrounds |
| `--color-primary-border` | `rgba(37,99,235,0.20)` | Active borders |

**Status:**

| Token | Value | Usage |
|-------|-------|-------|
| `--color-success` | `#059669` (emerald-600) | Completions |
| `--color-success-light` | `rgba(5,150,105,0.08)` | Success backgrounds |
| `--color-warning` | `#D97706` (amber-600) | Attention |
| `--color-warning-light` | `rgba(217,119,6,0.08)` | Warning backgrounds |
| `--color-danger` | `#DC2626` (red-600) | Errors |
| `--color-danger-light` | `rgba(220,38,38,0.08)` | Error backgrounds |
| `--color-info-light` | `rgba(37,99,235,0.06)` | Smart suggestion backgrounds |

### Typography

```
--font-sans:  'Inter', system-ui, -apple-system, sans-serif
--font-mono:  'JetBrains Mono', 'Fira Code', ui-monospace, monospace
```

| Token | Size / Line Height | Usage |
|-------|--------------------|-------|
| text-xs | 12px / 16px | Captions, badges |
| text-sm | 14px / 20px | Labels, secondary |
| text-base | 16px / 24px | Body, editor text |
| text-lg | 18px / 28px | Section headers |
| text-xl | 20px / 28px | Page titles |
| text-2xl | 24px / 32px | Hero text |

### Spacing, Radius, Shadows

Spacing: 4px base grid (1=4px through 16=64px).

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 4px | Badges, tags |
| `--radius-md` | 6px | Buttons, inputs |
| `--radius` | 8px | Cards |
| `--radius-lg` | 12px | Modals, panels |

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgb(0 0 0 / 0.05)` | Buttons |
| `--shadow-md` | `0 2px 4px rgb(0 0 0 / 0.06), 0 1px 2px rgb(0 0 0 / 0.04)` | Cards |
| `--shadow-lg` | `0 8px 16px rgb(0 0 0 / 0.08), 0 2px 4px rgb(0 0 0 / 0.04)` | Dropdowns |
| `--shadow-xl` | `0 16px 32px rgb(0 0 0 / 0.10), 0 4px 8px rgb(0 0 0 / 0.05)` | Modals |

### Theme

Light only. One polished experience. No dark mode.

---

## 3. Information Architecture

### Page Map

| Page | Path | Purpose |
|------|------|---------|
| Landing | `/` | Upload zone + recent projects grid |
| Editor | `/editor/:id` | Subtitle editor workspace (`:id` = backend `task_id`) |
| Status | `/status` | System health |
| About | `/about` | Product info |
| Security | `/security` | Security info |
| Contact | `/contact` | Contact form |

### Adaptive Upload Detection

The upload zone detects what the user gives it and routes to the appropriate flow:

| User drops... | Detected as | Backend call | Editor shows |
|--------------|-------------|-------------|--------------|
| Single video (.mp4/.mkv/.avi/.webm/.mov) | Transcription | `POST /upload` | Full editor: edit, translate, embed, download |
| Single audio (.mp3/.wav/.flac) | Transcription | `POST /upload` | Editor without embed option |
| Video + subtitle (.srt/.vtt) | Combine | `POST /combine` | Combine progress, download embedded video |
| Subtitle alone (.srt/.vtt) | Edit existing | Client-side parse | Subtitle editor (edit, re-export) |

No mode selector. No tabs. The file type IS the router.

### User Flows

**Flow 1 -- Transcription (primary):**
```
Drop file on /
  -> POST /upload (auto: best model, auto language, no diarization)
  -> Navigate to /editor/:task_id
  -> SSE /events/:task_id drives progress view
  -> Transcription completes -> editor view
  -> User edits, downloads, translates, embeds from editor
```

**Flow 2 -- Combine (detected from input):**
```
Drop video + SRT/VTT on /
  -> POST /combine (auto: soft mode)
  -> Navigate to /editor/:task_id
  -> Progress view (embedding)
  -> Complete -> download embedded video
```

**Flow 3 -- Re-transcribe (from editor):**
```
User clicks "Re-transcribe" in editor
  -> POST /tasks/:id/retranscribe (no re-upload)
  -> New task_id -> navigate to /editor/:new_id
  -> SSE drives progress -> new results
```

**Flow 4 -- Session restore (bookmark/refresh):**
```
User navigates to /editor/:id directly
  -> GET /progress/:id -> determine state
  -> If processing -> connect SSE, show progress
  -> If done -> show editor with results
  -> If failed -> show error with retry
```

### Duplicate Detection

Before uploading, frontend calls `GET /tasks/duplicates?filename=...&file_size=...`. If duplicates found, shows dialog: "This file was already transcribed. Open existing results?" with options to open existing or transcribe again.

---

## 4. Landing Page

### Layout

```
+--------------------------------------------------------------+
| HEADER  SubForge     [Status] [About]           [Health *]   |
+--------------------------------------------------------------+
| bg: gray-100                                                  |
|                                                               |
|  +----------------------------------------------------------+|
|  | Upload Zone (full width, prominent)                        ||
|  | bg: white, shadow-md, rounded-lg, padding-lg              ||
|  |                                                            ||
|  |  +------------------------------------------------------+ ||
|  |  |  dashed border gray-300, bg: gray-50, rounded         | ||
|  |  |                                                       | ||
|  |  |  [cloud-upload icon, 48px, blue-600]                  | ||
|  |  |                                                       | ||
|  |  |  "Drop your file to start"           text-lg, bold    | ||
|  |  |  "or click to browse"                text-sm, muted   | ||
|  |  |                                                       | ||
|  |  |  MP4, MKV, WAV, MP3, SRT and more -- Up to 2GB       | ||
|  |  +------------------------------------------------------+ ||
|  |                                                            ||
|  |  "Transcription starts automatically -- no setup needed"   ||
|  +----------------------------------------------------------+||
|                                                               |
|  Recent Projects                                    [Clear]  |
|  +------------+ +------------+ +------------+ +------------+|
|  | interview  | | podcast    | | lecture    | | meeting    ||
|  | .mp4       | | .mp3       | | .wav      | | .mp4       ||
|  | 12:34      | | 45:01      | | 1:02:33   | | 32:10      ||
|  | Done       | | Done       | | Failed    | | Done       ||
|  | 2m ago     | | Yesterday  | | 3d ago    | | 1w ago     ||
|  +------------+ +------------+ +------------+ +------------+|
|                                                               |
+--------------------------------------------------------------+
| Footer                                                        |
+--------------------------------------------------------------+
```

### Key decisions

- **Upload zone is the entire focus** -- no sidebar, no drawer, no dashboard. One action: drop a file.
- **"Transcription starts automatically"** -- tells user there's no configuration step
- **No model selection, no language picker, no options** -- smart defaults, refine later
- **Recent projects as grid** -- cards show filename, duration, status badge, relative time. Click navigates to `/editor/:id`
- **Multi-file drop** -- video + SRT together detected as combine flow
- **Upload progress** -- after drop, zone transforms into progress bar. On XHR complete, auto-navigates to editor.

### Recent projects data source

- `localStorage` array of `{taskId, filename, createdAt, status, duration}` (max 20)
- Validated on load via `GET /progress/:id` -- prune stale entries
- "Clear" button removes all

---

## 5. Editor Page

The core of the product. Two states: **progress** (during transcription) and **editing** (after completion).

### State 1: Progress View

```
+--------------------------------------------------------------+
| HEADER                                                        |
+--------------------------------------------------------------+
| bg: gray-100                                                  |
|                                                               |
|  +----------------------------------------------------------+|
|  | white card, full width                                     ||
|  |                                                            ||
|  |  Transcribing interview.mp4                                ||
|  |  Model: large -- Language: detecting...                    ||
|  |                                                            ||
|  |  =============================---------  78%               ||
|  |  142 / ~180 segments -- ETA: ~25s -- 3.2x realtime        ||
|  |                                                            ||
|  |  * Live                              Elapsed: 1:23         ||
|  |                                                            ||
|  |  Pipeline:                                                 ||
|  |  v Audio extracted        0.8s                             ||
|  |  v Model loaded           0.2s                             ||
|  |  * Transcribing...        1:22                             ||
|  |  o Writing output                                          ||
|  |                                                            ||
|  |                          [Pause] [Cancel]                  ||
|  +----------------------------------------------------------+||
|                                                               |
|  Live Preview                                                |
|  +----------------------------------------------------------+|
|  | 00:00:01 -> 00:00:04  Welcome to today's interview...     ||
|  | 00:00:04 -> 00:00:08  Thank you for having me here.       ||
|  | 00:00:08 -> 00:00:12  Let's start with the basics...      ||
|  | [auto-scrolling]                                           ||
|  +----------------------------------------------------------+|
+--------------------------------------------------------------+
```

**SSE events drive the entire view:**

| SSE event | UI update |
|-----------|-----------|
| `progress` | Updates percentage, ETA, speed, segment count |
| `segment` | Appends to live preview |
| `step_change` | Updates pipeline steps |
| `done` | Transitions to editing state |
| `error` | Shows error alert with retry |
| `paused` / `resumed` | Updates pause button |
| `cancelled` | Shows cancelled state with re-try |

### State 2: Editing View

```
+--------------------------------------------------------------+
| HEADER                                                        |
+--------------------------------------------------------------+
| TOOLBAR                                                       |
| [Download v] [Translate] [Embed] [Re-transcribe]             |
| [Search...]                         interview.mp4 -- 12:34   |
+--------------------------------------------------------------+
|                                                               |
|  EDITOR (flex-1)                   |  PANEL (360px)          |
|  white card                        |  white card              |
|                                    |                          |
|  1  00:00:01 -> 00:00:04          |  FILE INFO               |
|  Welcome to today's interview     |  interview.mp4            |
|  about artificial intelligence.    |  Duration: 12:34          |
|  [click to edit]                   |  Format: H.264/AAC        |
|                                    |  Size: 245 MB             |
|  2  00:00:04 -> 00:00:08          |  Language: English         |
|  Speaker 1                         |  Segments: 212            |
|  Thank you for having me here.     |                          |
|  [click to edit]                   |  STATS                    |
|                                    |  Speed: 5.8x realtime     |
|  3  00:00:08 -> 00:00:12          |  Model: large             |
|  Speaker 2                         |  Processing: 2:08         |
|  Let's start with the basics       |                          |
|  of machine learning.              |  SUGGESTION               |
|  [click to edit]                   |  "Want to translate to     |
|                                    |   another language?"       |
|  ...212 segments                   |  [Translate ->]           |
|                                    |                          |
+------------------------------------+--------------------------+
```

### Editor features

**Inline editing:**
- Click any segment text to edit. On blur: `PUT /subtitles/:id/:index`
- Timecodes editable (click timecode, input fields appear)
- SRT/VTT auto-regenerated on every edit
- Speaker labels shown if diarization was enabled (always visible, not hidden)

**Search:**
- Search bar in toolbar: `GET /search/:id?q=...`
- Results highlighted in editor, scroll to match
- Match count: "3 matches for 'machine learning'"

**Download (dropdown):**
- SRT, VTT, JSON, ZIP
- Custom line length option (20-120 chars via `max_line_chars`)
- `GET /download/:id?format=srt`, `GET /download/:id/all`

**Translate (right panel):**
- Source language (auto-detected, read-only)
- Target language dropdown (from `GET /translation/languages`, 147 pairs)
- Engine: Whisper (English-only, higher quality) or Argos (any language)
- Progress bar (SSE `translate_progress` events)
- Side-by-side preview: original | translated

**Embed (right panel, video inputs only):**
- Mode: Soft mux (recommended, fast) vs Hard burn (re-encodes)
- Style presets from `GET /embed/presets` (default, youtube_white, youtube_yellow, cinema, large_bold, top)
- Custom: font, size, color, position, opacity
- Progress bar, then download embedded video
- Uses `POST /embed/:id/quick`

**Re-transcribe:**
- One-click: `POST /tasks/:id/retranscribe`
- Optional expand: change model, language, enable diarization
- Creates new task, navigates to `/editor/:new_id`
- No re-upload needed

### Right panel -- adaptive content

| Context | Panel shows |
|---------|-------------|
| Just completed | File info + stats + smart suggestion |
| Translating | Translation progress + side-by-side preview |
| Embedding | Embed progress + style preview |
| Searching | Search results with context snippets |
| Default | File info + stats |

### Smart suggestions

Contextual prompts after transcription completes:

| Condition | Suggestion |
|-----------|-----------|
| Video file, not embedded | "Add subtitles to your video? [Embed]" |
| Non-English source | "Translate to English? [Translate]" |
| Used medium model, large available | "Want higher accuracy? [Re-transcribe with Large]" |
| First time user | "Your subtitles are ready. [Download SRT]" |

Dismissable. Don't reappear in same session.

### State 3: Combine View (video + SRT upload)

When the user drops a video + subtitle file together, the editor shows a simplified view:

```
+--------------------------------------------------------------+
| TOOLBAR                                                       |
| [Download]                          video.mp4 + subs.srt      |
+--------------------------------------------------------------+
|                                                               |
|  MAIN                              |  PANEL                   |
|                                    |                          |
|  Embedding subtitles...            |  FILE INFO               |
|  Mode: Soft mux (lossless)        |  video.mp4               |
|  ====================------  65%   |  Duration: 12:34         |
|                                    |  Subtitles: subs.srt     |
|  [Cancel]                          |  Mode: Soft              |
|                                    |                          |
|  --- OR after completion ---       |                          |
|                                    |                          |
|  Subtitles embedded successfully   |  DOWNLOAD                |
|  [Download Video]  245 MB          |  video_subtitled.mkv     |
|  [Back to Home]                    |  Soft embed              |
|                                    |                          |
+------------------------------------+--------------------------+
```

No subtitle editor in combine mode -- there are no segments to edit (the SRT was provided by the user). The editor shows progress and download only.

### State 4: SRT-Only Edit Mode (subtitle file dropped alone)

When the user drops only an SRT/VTT file, the editor parses it client-side and shows the editing view:

**Available features:**
- View and edit segment text (client-side)
- View and edit timecodes (client-side)
- Download edited version (client-side SRT/VTT generation)

**NOT available (no backend task_id):**
- Translate (requires backend task)
- Embed (requires video file)
- Re-transcribe (no media file)
- Search (requires backend endpoint)

The toolbar shows only the [Download] button. Translate, Embed, Re-transcribe are hidden. A subtle note: "Editing local file -- upload media to access full features."

---

## 6. Component Architecture

### Layout Components

| Component | Purpose |
|-----------|---------|
| `AppShell` | Root: header + main content + footer |
| `Header` | Sticky top: logo, nav, health indicator |
| `Footer` | Static links |
| `PageLayout` | Wrapper for static pages (narrow max-width) |

### Landing Components

| Component | Purpose |
|-----------|---------|
| `UploadZone` | Drag-and-drop with adaptive file detection |
| `UploadProgress` | Progress bar during XHR upload |
| `ProjectGrid` | Grid of recent project cards |
| `ProjectCard` | Single project: filename, duration, status, time |

### Editor Components

| Component | Purpose |
|-----------|---------|
| `EditorToolbar` | Action bar: download, translate, embed, re-transcribe, search |
| `ProgressView` | Real-time transcription progress (SSE-driven) |
| `PipelineSteps` | Step list with checkmarks and spinner |
| `LivePreview` | Auto-scrolling segment preview during transcription |
| `SegmentList` | Scrollable list of editable segments |
| `SegmentRow` | Single segment: index, timecodes, speaker label, editable text |
| `SearchBar` | Full-text search within transcript |
| `ContextPanel` | Right sidebar: adaptive content |
| `DownloadMenu` | Dropdown: SRT, VTT, JSON, ZIP |
| `TranslatePanel` | Language picker, engine selector, progress, preview |
| `EmbedPanel` | Mode selector, style presets, custom options, progress |
| `RetranscribeDialog` | Model/language/options picker for re-transcription |
| `SmartSuggestion` | Contextual action card (blue-tinted, dismissable) |

### System Components

| Component | Purpose |
|-----------|---------|
| `HealthIndicator` | Colored dot in header + tooltip |
| `ConnectionBanner` | Full-width banner for SSE disconnect/reconnect |
| `ErrorBoundary` | React error boundary with styled fallback |

### UI Primitives

Button, IconButton, Card, Input, Select, Textarea, Checkbox, Toggle, Badge, Tag, Dialog, ConfirmDialog, Tooltip, Toast, ToastContainer, Alert, ProgressBar, Spinner, Skeleton, EmptyState, Divider

---

## 7. State Architecture

### 5 Stores

```typescript
// editorStore.ts -- Core editor state
interface EditorState {
  // Project
  taskId: string | null
  fileMetadata: FileMetadata | null

  // Phase
  phase: 'idle' | 'uploading' | 'processing' | 'editing' | 'error'

  // Upload
  uploadPercent: number

  // Transcription progress (SSE-driven)
  progress: {
    percent: number
    segmentCount: number
    estimatedSegments: number
    eta: number | null
    elapsed: number
    speed: number | null
    pipelineStep: string
    message: string
  } | null
  liveSegments: Segment[]

  // Completed results
  segments: Segment[]
  language: string | null
  modelUsed: string | null
  timings: Record<string, number>
  isVideo: boolean

  // Editing
  searchQuery: string
  searchResults: SearchResult[]
  editingSegmentIndex: number | null

  // Actions
  startUpload: (file: File) => void
  setTaskId: (id: string) => void
  updateProgress: (data: ProgressData) => void
  addLiveSegment: (segment: Segment) => void
  setComplete: (data: CompleteData) => void
  setError: (message: string) => void
  updateSegment: (index: number, text: string) => void
  setSearchQuery: (query: string) => void
  setSearchResults: (results: SearchResult[]) => void
  reset: () => void
}

// uiStore.ts -- App chrome
interface UIState {
  currentPage: string
  contextPanelContent: 'info' | 'translate' | 'embed' | 'search'
  sseConnected: boolean
  sseReconnecting: boolean
  systemHealth: 'healthy' | 'degraded' | 'critical'
  modelPreloadStatus: Record<string, string>
  dismissedSuggestions: string[]

  setCurrentPage: (page: string) => void
  setContextPanel: (content: string) => void
  setSSEConnected: (connected: boolean) => void
  setSystemHealth: (health: string) => void
  dismissSuggestion: (id: string) => void
}

// preferencesStore.ts -- User defaults (localStorage)
interface PreferencesState {
  preferredFormat: 'srt' | 'vtt' | 'json'
  maxLineChars: number

  setPreference: (key: string, value: any) => void
  resetDefaults: () => void
}

// toastStore.ts -- Notifications
interface ToastState {
  toasts: Toast[]
  addToast: (toast: ToastInput) => void
  removeToast: (id: string) => void
}

// recentProjectsStore.ts -- Project history (localStorage)
interface RecentProjectsState {
  projects: RecentProject[]
  addProject: (project: RecentProject) => void
  updateProject: (taskId: string, updates: Partial<RecentProject>) => void
  removeProject: (taskId: string) => void
  clearAll: () => void
}
```

### Translation and embed state (component-local, not in stores)

These are small, panel-scoped state that lives in the component, not in a global store:

```typescript
// TranslatePanel local state
const [targetLanguage, setTargetLanguage] = useState<string>('')
const [engine, setEngine] = useState<'whisper' | 'argos'>('argos')
const [translating, setTranslating] = useState(false)
const [translatePercent, setTranslatePercent] = useState(0)
const [translatedSegments, setTranslatedSegments] = useState<Segment[]>([])

// EmbedPanel local state
const [mode, setMode] = useState<'soft' | 'hard'>('soft')
const [preset, setPreset] = useState('default')
const [customStyle, setCustomStyle] = useState<CustomStyle | null>(null)
const [embedding, setEmbedding] = useState(false)
const [embedPercent, setEmbedPercent] = useState(0)
const [embedDownloadUrl, setEmbedDownloadUrl] = useState<string | null>(null)
```

These are component-local because: (a) they're only relevant while the panel is open, (b) they don't need to survive panel close, (c) they're never read by other components.

### Why 5 stores, not 9

The old spec split into 9 stores (workspace, transcribe, translate, embed, export, etc.) for "parallel development." But that was anchored on a step-bar architecture with separate pages per step. The new editor-centric design has one workspace with one concern. Translation state is 3 fields. Embed state is 4 fields. These live as local component state or sections of `editorStore`, not separate stores.

### Shared types (types.ts)

```typescript
export interface FileMetadata {
  filename: string
  duration: number
  format: string
  resolution: string | null
  size: number
  codec: string
  isVideo: boolean
}

export interface Segment {
  index: number
  start: number    // seconds (float)
  end: number      // seconds (float)
  text: string
  speaker?: string
}

export interface SearchResult {
  segmentIndex: number
  text: string
  matchStart: number
  matchEnd: number
}

export interface RecentProject {
  taskId: string
  filename: string
  createdAt: string
  status: 'processing' | 'completed' | 'failed'
  duration: number | null
}

export type EditorPhase = 'idle' | 'uploading' | 'processing' | 'editing' | 'error'

// Utilities
export function formatTimecode(seconds: number): string { ... }
export function formatFileSize(bytes: number): string { ... }
export function formatDuration(seconds: number): string { ... }
```

---

## 8. Backend Integration

### API mapping

| Editor action | API call | Notes |
|--------------|----------|-------|
| Drop file | `POST /upload` (file only, auto defaults) | No model/language params |
| Drop file + SRT | `POST /combine` (video + subtitle) | Auto-detected |
| View progress | `GET /events/:id` (SSE) | 18+ event types |
| Session restore | `GET /progress/:id` | Determines phase |
| Edit segment | `PUT /subtitles/:id/:index` | Auto-regenerates SRT/VTT |
| Bulk edit | `PUT /subtitles/:id` | Full segment array |
| Search | `GET /search/:id?q=...&limit=20` | Full-text, case-insensitive |
| Download | `GET /download/:id?format=srt` | Also max_line_chars |
| Download all | `GET /download/:id/all` | ZIP archive |
| Translate | `POST /upload` with `translate_to`, OR new `POST /translate/:id` | Pre or post-hoc |
| Embed (soft) | `POST /embed/:id/quick` | Original video |
| Embed (hard) | `POST /embed/:id/quick` mode=hard + style | Re-encodes |
| Embed presets | `GET /embed/presets` | 6 presets |
| Re-transcribe | `POST /tasks/:id/retranscribe` | No re-upload |
| Cancel | `POST /cancel/:id` | During transcription |
| Pause/Resume | `POST /pause/:id`, `POST /resume/:id` | During transcription |
| Delete | `DELETE /tasks/:id` | Terminal state only |
| System info | `GET /system-info` | Models, GPU |
| Health stream | `GET /health/stream` (SSE) | Every 3s |
| Languages | `GET /languages` | 99 languages |
| Translation langs | `GET /translation/languages` | 147 pairs |
| Model status | `GET /api/model-status` | Preload status |
| Duplicates | `GET /tasks/duplicates?filename=...&file_size=...` | Before upload |
| Task stats | `GET /tasks/stats` | Aggregates |

### Smart defaults (server-side)

`POST /upload` with minimal params -- server handles defaults:
- `model_size: "auto"` -- server picks best model based on GPU/VRAM
- `language: "auto"` -- Whisper auto-detects
- `diarize: false` -- off by default
- `word_timestamps: false` -- off by default

Frontend sends only the `file` form field. All other form params (`model_size`, `language`, `device`, `diarize`, etc.) use server defaults (`"auto"`, `"auto"`, `"cuda"` with CPU fallback, `false`, etc.). The server handles all decision-making.

### max_line_chars discrepancy

The upload route clamps `max_line_chars` to 20-80. The download route accepts 20-120. The frontend should use the download route's range (20-120) for the "custom line length" option since it applies to the download, not the original transcription. This discrepancy exists in the backend and is not a frontend concern.

### Required backend addition: POST /translate/{task_id}

Post-hoc translation of a completed task's subtitles. This is the single biggest implementation dependency.

**Request:**
```
POST /translate/{task_id}
Content-Type: application/json

{
  "target_language": "es",
  "engine": "argos"          // "whisper" (English-only) or "argos" (any)
}
```

**Response:**
```json
{
  "task_id": "original-task-id",
  "message": "Translation started",
  "target_language": "es",
  "engine": "argos"
}
```

**SSE events (via existing /events/{task_id}):**
- `translate_start` -- `{target_language, engine}`
- `translate_progress` -- `{percent, translated, total, message}`
- `translate_done` -- `{segments: [...translated segments...]}`

**Without this endpoint**, the TranslatePanel falls back to showing a message: "To translate, re-transcribe with translation enabled" with a one-click re-transcribe action that passes `translate_to` to `POST /upload`. This fallback works but requires re-transcription.

### Client-side file validation

Before upload, the frontend validates:
- File extension is in accepted list (from `GET /api/capabilities`)
- File size <= 2GB and >= 1KB
- If file too large: "File exceeds 2GB limit. Try a shorter clip or compressed format."
- If wrong type: "Unsupported format. We accept MP4, MKV, WAV, MP3, and more."
- If upload fails mid-stream (network): "Upload interrupted. [Retry]"

Backend rejections (magic bytes, duration, ClamAV) show the error message from the API response directly.

### Network and critical state handling

- Upload fails mid-stream: show "Upload interrupted" with retry button. File reference kept in memory.
- API calls fail (500/503): toast with error message + retry option
- `GET /health/stream` reports `critical`: full-width red banner "System recovering. Uploads paused." Upload zone disabled.
- SSE disconnect: yellow banner "Reconnecting..." with exponential backoff (1s, 2s, 4s, 8s, max 30s)

### Recent projects validation strategy

On landing page load, validate recent projects **lazily**:
- Render cards immediately from localStorage (show cached status)
- Fire `GET /progress/:id` for each project in a staggered queue (100ms apart, max 3 concurrent)
- Update card status as responses arrive (done/failed/processing/404)
- 404 responses → remove from list silently
- Timeout after 5s → keep cached status, mark as "unknown"

### Session restore for edge cases

- Task deleted (404): redirect to `/` with toast "Project not found or deleted"
- Task in terminal error state: show error view with "Re-try" and "Back to home" buttons
- Partial failure (transcription done, translation fails): show editor with available segments + error alert for the failed step

---

## 9. Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| < 640px (mobile) | Single column. Editor full-width. Context panel collapses to bottom sheet. Toolbar hamburger menu. Upload zone stacked above project grid. |
| 640-1023px (tablet) | Single column. Context panel collapsible (toggle). Toolbar condensed (icons, labels on hover). |
| >= 1024px (desktop) | Two columns: editor flex-1 + context panel 360px. Full toolbar. |
| >= 1280px (wide) | Same as desktop, max-width 1280px, centered. |

Touch targets: 44px minimum on mobile.

---

## 10. Animations & Interactions

| Animation | Where | Duration |
|-----------|-------|----------|
| Upload pulse | Drag-over state on drop zone | 2s cycle |
| Progress shimmer | Progress bar fill | Continuous |
| Segment slide-in | Live preview during transcription | 200ms |
| Phase transition | Progress view to editor view | Fade 200ms |
| Suggestion enter | Smart suggestion card appears | Slide-up 200ms |
| Toast enter/exit | Notifications | Slide-in 200ms, fade-out 300ms |
| Card hover lift | Project cards | translateY(-1px), 150ms |
| Search highlight | Matched text in segments | Background flash 300ms |

All respect `prefers-reduced-motion: reduce`.

---

## 11. Accessibility

- **WCAG 2.1 AA** compliance
- **Keyboard navigation** -- Tab through segments, Enter to edit, Escape to cancel
- **Focus management** -- visible focus rings (2px blue, `:focus-visible` only)
- **Focus trapping** -- dialogs and panels
- **Skip navigation** -- hidden link to skip to editor content
- **Screen reader** -- ARIA labels, `aria-live="polite"` on live preview and progress
- **Color contrast** -- minimum 4.5:1 text, 3:1 UI components
- **Touch targets** -- 44px minimum on mobile
- **Reduced motion** -- all animations disabled when `prefers-reduced-motion: reduce`

### ARIA patterns

- Progress bar: `role="progressbar"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- Live preview: `aria-live="polite"` for new segments
- Toast: `role="status"` with `aria-live="polite"`
- Dialogs: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- Connection banner: `role="alert"` for connection loss
- Segment list: `role="list"` with `role="listitem"` per segment
- Search results: `aria-live="polite"` for match count updates

---

## Appendix: Technology Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 19 |
| Language | TypeScript 5.9 |
| Build | Vite 6 |
| Styling | Tailwind CSS v4 (CSS-in-CSS config) |
| State | Zustand 5 |
| Icons | Lucide React |
| UI Primitives | Radix UI (Tooltip, Collapsible, Progress) |
| Drag & Drop | react-dropzone |
| Variant Management | class-variance-authority |
| Class Merging | clsx + tailwind-merge |
| Testing | Vitest (unit) + Playwright (e2e) |
| Real-time | Server-Sent Events (EventSource API) |
| Upload | XHR with progress tracking |
