# SubForge Interface Redesign — Full Rebuild

**Date:** 2026-03-18
**Author:** Atlas (Tech Lead), Team Sentinel
**Status:** Approved (brainstorming complete)
**Deployment target:** `newui.openlabs.club` (promote to production after investor approval)

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Visual Identity](#2-visual-identity)
3. [Information Architecture](#3-information-architecture)
4. [Component System](#4-component-system)
5. [Feature Logic & Relationships](#5-feature-logic--relationships)
6. [Backend Integration Notes](#6-backend-integration-notes)
7. [State Architecture](#7-state-architecture)
8. [Layout Specifications](#8-layout-specifications)
9. [Key Screen Designs](#9-key-screen-designs)
10. [Responsive Behavior](#10-responsive-behavior)
11. [Animation System](#11-animation-system)
12. [Accessibility](#12-accessibility)
13. [Component API Reference](#13-component-api-reference)
14. [Interaction Patterns](#14-interaction-patterns)
15. [Required API Additions](#15-required-api-additions)

---

## 1. Design Philosophy

### "Guided Confidence"

Every design decision is filtered through one question: **"Does this help the user feel confident about what's happening?"**

**Principles:**

- **Smart defaults** — The interface pre-selects the best option so users can just click "Go." Preferences are remembered across sessions.
- **Contextual guidance** — Hints, tooltips, and inline explanations appear where decisions are made, not buried in documentation.
- **Visible progress** — Every process shows exactly what stage it's at, what's next, and how long it will take.
- **Confirmation before action** — Destructive or costly actions always ask first via a confirmation dialog.
- **Completion signals** — Clear success states that tell the user "you're done, here's what you got."

**Design direction:** Cool Professional — inspired by GitHub, Atlassian, Microsoft 365. Trustworthy, technical, information-dense when needed but spacious by default.

**Theme:** Light only. One perfectly polished experience. No dark mode.

---

## 2. Visual Identity

### Color System

**Foundation & Surfaces:**

| Token | Value | Usage |
|-------|-------|-------|
| `--color-bg` | `#F3F4F6` (gray-100) | Page foundation background |
| `--color-surface` | `#FFFFFF` | Cards, panels |
| `--color-surface-raised` | `#FFFFFF` | Modals, popovers (same color as surface; differentiated via shadow-lg/shadow-xl only) |
| `--color-border` | `#E5E7EB` (gray-200) | Subtle borders |
| `--color-border-strong` | `#D1D5DB` (gray-300) | Dividers, active borders |

**Text:**

| Token | Value | Usage |
|-------|-------|-------|
| `--color-text` | `#111827` (gray-900) | Primary text |
| `--color-text-secondary` | `#4B5563` (gray-600) | Labels, supporting text |
| `--color-text-muted` | `#6B7280` (gray-500) | Hints, timestamps, metadata |
| `--color-text-placeholder` | `#9CA3AF` (gray-400) | Input placeholders |

**Brand & Accent:**

| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary` | `#2563EB` (blue-600) | Primary actions, links, active states |
| `--color-primary-hover` | `#1D4ED8` (blue-700) | Hover state for primary elements |
| `--color-primary-light` | `rgba(37,99,235,0.08)` | Tinted backgrounds for active/selected |
| `--color-primary-border` | `rgba(37,99,235,0.20)` | Tinted borders for active elements |

**Status:**

| Token | Value | Usage |
|-------|-------|-------|
| `--color-success` | `#059669` (emerald-600) | Completed states, confirmations |
| `--color-success-light` | `rgba(5,150,105,0.08)` | Success backgrounds |
| `--color-warning` | `#D97706` (amber-600) | Attention needed |
| `--color-warning-light` | `rgba(217,119,6,0.08)` | Warning backgrounds |
| `--color-danger` | `#DC2626` (red-600) | Errors, destructive actions |
| `--color-danger-light` | `rgba(220,38,38,0.08)` | Error backgrounds |

### Typography

**Font Stack:**

```
--font-sans:  'Inter', system-ui, -apple-system, sans-serif
--font-mono:  'JetBrains Mono', 'Fira Code', ui-monospace, monospace
```

**Type Scale:**

| Token | Size / Line Height | Weight | Usage |
|-------|--------------------|--------|-------|
| `text-xs` | 12px / 16px | 400–500 | Captions, badges |
| `text-sm` | 14px / 20px | 400–500 | Labels, secondary text |
| `text-base` | 16px / 24px | 400 | Body text |
| `text-lg` | 18px / 28px | 600 | Section headers |
| `text-xl` | 20px / 28px | 600 | Page section titles |
| `text-2xl` | 24px / 32px | 700 | Page titles |
| `text-3xl` | 30px / 36px | 700 | Hero headings |

**Font Weights:**

| Token | Value |
|-------|-------|
| `weight-normal` | 400 |
| `weight-medium` | 500 |
| `weight-semibold` | 600 |
| `weight-bold` | 700 |

### Spacing

4px base grid:

| Token | Value |
|-------|-------|
| `1` | 4px |
| `2` | 8px |
| `3` | 12px |
| `4` | 16px |
| `5` | 20px |
| `6` | 24px |
| `8` | 32px |
| `10` | 40px |
| `12` | 48px |
| `16` | 64px |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 4px | Badges, tags |
| `--radius-md` | 6px | Buttons, inputs |
| `--radius-lg` | 8px | Cards |
| `--radius-xl` | 12px | Modals, panels |

### Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgb(0 0 0 / 0.05)` | Buttons, inputs |
| `--shadow-md` | `0 2px 4px rgb(0 0 0 / 0.06), 0 1px 2px rgb(0 0 0 / 0.04)` | Cards |
| `--shadow-lg` | `0 8px 16px rgb(0 0 0 / 0.08), 0 2px 4px rgb(0 0 0 / 0.04)` | Dropdowns, popovers |
| `--shadow-xl` | `0 16px 32px rgb(0 0 0 / 0.10), 0 4px 8px rgb(0 0 0 / 0.05)` | Modals |

### Transitions

| Token | Value |
|-------|-------|
| `--transition-fast` | 150ms ease |
| `--transition-normal` | 200ms ease |
| `--transition-slow` | 300ms ease |

### Visual Personality

- Clean but not sterile — subtle shadows and spacing create warmth
- Information-dense when needed (stats, timecodes) but spacious by default
- Blue accent used sparingly — primarily for CTAs and active states, not decoration
- Gray scale does the heavy lifting for hierarchy; color is for meaning

---

## 3. Information Architecture

### Core Concept: File → Project → Workspace

Every uploaded file becomes a **project**. A project is a persistent workspace where all tools operate on that file. The user never leaves their workspace to access a related feature.

### Page Map

| Page | Path | Purpose |
|------|------|---------|
| Home | `/` | Upload zone (primary CTA) + project drawer (collapsible) |
| Workspace | `/project/:id` | Step bar + main panel + context panel. `:id` maps to backend `task_id`. |
| Status | `/status` | System status with incident detection |
| About | `/about` | Feature showcase |
| Security | `/security` | Security information |
| Contact | `/contact` | Contact form |

**Routing note:** The current custom router (`Router.tsx`) only supports static paths. It must be extended to support parameterized routes (`:id` extraction) for the workspace. No external router library required — add a simple path-matching regex to the existing router.

### Workspace Step Bar

The horizontal step bar is the primary navigation within a workspace:

| Step | Name | Description | Available When |
|------|------|-------------|----------------|
| 1 | **Upload** | File info, format, duration, size | Always (completed on entry) |
| 2 | **Transcribe** | Model selection, language, progress | After upload |
| 3 | **Translate** | Source/target language, progress | After transcription (optional, skippable) |
| 4 | **Embed** | Soft mux or hard burn, styles | After transcription + video input (optional, skippable) |
| 5 | **Export** | Download SRT/VTT/JSON, preview, stats | After transcription |

**Step bar behaviors:**

- Completed steps show a **checkmark** and are always clickable (revisit)
- Active step shows a **blue dot with pulse animation**
- Future applicable steps are **grayed out** but visible (user knows what's coming)
- Optional steps (Translate, Embed) show a "Skip" affordance when active
- **Non-applicable steps are fully hidden** (e.g., Embed is not shown at all for audio-only files). This is distinct from grayed-out: hidden means removed from the step bar entirely.

### Project Drawer

A collapsible right-side section on the home screen:

- **Recent projects** — Last 20, sorted by recency: filename, date, status (completed/in-progress), duration
- **Quick resume** — Click a project to re-enter its workspace at the last active step
- **Search** — Filter by filename
- **Bulk actions** — Delete old projects, download all subtitles

### Navigation Flow

```
Landing (Upload zone + Project drawer)
    |
    +-- Upload file --> Workspace opens at Step 2 (Transcribe)
    |       |
    |       +-- Transcription completes --> Step 3 (Translate) or Step 5 (Export)
    |       +-- User clicks Translate --> Step 3
    |       +-- User clicks Embed --> Step 4
    |       +-- User clicks Export --> Step 5
    |
    +-- Click existing project --> Workspace opens at last step
```

### Context Panel (Right Sidebar in Workspace)

Always visible on desktop, content adapts to active step:

| Active Step | Context Panel Shows |
|-------------|-------------------|
| Upload | File metadata: format, codec, duration, size, resolution |
| Transcribe | Live subtitle preview, segment count, elapsed time |
| Translate | Side-by-side original vs translated preview |
| Embed | Video preview thumbnail, selected style preview |
| Export | File sizes, timing breakdown, quality stats |

---

## 4. Component System

### Component Inventory

**Layout Components:**

| Component | Purpose | Variants |
|-----------|---------|----------|
| `AppShell` | Root layout — header + content + optional drawer | — |
| `Header` | Sticky top bar — logo, nav, actions | — |
| `Workspace` | Step bar + main panel + context panel | — |
| `StepBar` | Horizontal pipeline navigation | — |
| `MainPanel` | Primary content area | padded, flush |
| `ContextPanel` | Right sidebar, adapts to step | collapsible on mobile |
| `ProjectDrawer` | Collapsible section on home | open, closed |
| `PageLayout` | Wrapper for static pages | narrow, wide |

**UI Primitives:**

| Component | Variants | Sizes | States |
|-----------|----------|-------|--------|
| `Button` | primary, secondary, ghost, danger, success | sm, md, lg | default, hover, active, disabled, loading |
| `IconButton` | primary, secondary, ghost | sm, md, lg | default, hover, disabled |
| `Input` | text, password, search | sm, md | default, focus, error, disabled |
| `Select` | default | sm, md | default, focus, error, disabled |
| `Textarea` | default | sm, md | default, focus, error, disabled |
| `Checkbox` | default | — | unchecked, checked, indeterminate, disabled |
| `Toggle` | default | sm, md | off, on, disabled |
| `Badge` | default, success, warning, danger, info | sm, md | — |
| `Tag` | default, removable | — | default, hover |

**Feedback Components:**

| Component | Purpose |
|-----------|---------|
| `Toast` | Temporary notifications (success, error, warning, info) |
| `Alert` | Inline persistent messages with icon |
| `ProgressBar` | Determinate/indeterminate progress |
| `Spinner` | Loading indicator |
| `Skeleton` | Content placeholder during load |
| `EmptyState` | Illustrated placeholder when no content |
| `StepIndicator` | Numbered step with status (pending, active, done, skipped) |

**Overlay Components:**

| Component | Purpose |
|-----------|---------|
| `Dialog` | Modal with title, body, actions. Focus trapped. |
| `ConfirmDialog` | Specialized Dialog for confirm/cancel actions |
| `Tooltip` | Hover hint (Radix-based) |
| `Popover` | Click-triggered floating content |
| `Drawer` | Slide-in panel from edge |

**Data Display:**

| Component | Purpose |
|-----------|---------|
| `Card` | Container with optional header, border, shadow |
| `Table` | Data rows with optional sorting |
| `KeyValue` | Label-value pair display |
| `FileInfo` | File metadata card (name, size, duration, format) |
| `SubtitlePreview` | Scrollable timecoded subtitle segments |
| `TimingBreakdown` | Pipeline step timing table |
| `StatCard` | Metric display (number + label + trend) |

**Domain Components:**

| Component | Step | Purpose |
|-----------|------|---------|
| `UploadZone` | Home | Drag-and-drop file upload with progress |
| `ProjectCard` | Drawer | Project summary in drawer list |
| `ModelSelector` | Transcribe | Model selection with descriptions |
| `LanguageSelect` | Transcribe | Language picker with search |
| `TranscribeOptions` | Transcribe | Advanced options (diarization, timestamps) |
| `TranscribeProgress` | Transcribe | Live progress with segment preview |
| `TranslatePanel` | Translate | Source/target language + progress |
| `EmbedPanel` | Embed | Mux mode, style options, preview |
| `ExportPanel` | Export | Format buttons, download, copy |
| `HealthIndicator` | Header | System health dot + tooltip |
| `ConnectionStatus` | Header | SSE connection state banner |

---

## 5. Feature Logic & Relationships

### Feature Relationship Map

```
                    [UPLOAD]
                       |
                       v
                  [TRANSCRIBE]
                   /        \
                  v          v
            [TRANSLATE]   (audio-only
            (optional)     skips embed)
                  |          |
                  v          |
              [EMBED]        |
            (optional,       |
             video only)     |
                  |          |
                  v          v
               [EXPORT] <----+
```

### Step-by-Step Feature Logic

#### Step 1 — Upload

- User drops or selects a file on the home screen
- System validates: file type (audio/video), size limit, magic bytes
- System probes with ffprobe: extracts duration, codec, resolution, bitrate
- If valid: project created, workspace opens at Step 2
- If invalid: inline error with specific reason ("File too large", "Unsupported format")
- Context panel shows: file card with all metadata
- Guided confidence: "Your file is ready. Choose a model to begin transcription."

#### Step 2 — Transcribe

**Pre-transcription form:**
- Model selector (tiny to large) with descriptions, accuracy hints, speed estimates
- Language: auto-detect (default) or manual selection
- Advanced options (collapsed by default): speaker diarization, word-level timestamps
- Smart defaults from user preferences (localStorage)

**Confirmation dialog:** Shows summary — file name, model, language, estimated time

**During transcription:**
- Progress bar with percentage and ETA
- Step bar shows Step 2 as active (blue pulse)
- Context panel shows live subtitle preview (segments appear in real-time via SSE)
- Liveness indicator: pulsing dot confirms SSE is active
- Cancel button with confirmation dialog

**On completion:**
- Step 2 shows checkmark
- Toast: "Transcription complete — X segments in Y seconds"
- Auto-advances to next relevant step with smart suggestion:
  - Video file: "Embed subtitles into your video?" or "Translate?" or "Go to Export"
  - Audio file: "Translate subtitles?" or "Go to Export"

#### Step 3 — Translate (Optional)

**Backend integration:** Translation can happen two ways: (a) bundled with transcription at Step 2 via `translate_to_english` / `translate_to` params in `POST /upload`, or (b) as a separate post-hoc action via `POST /translate/{task_id}` (new endpoint — see Section 15). The Step 2 form includes an optional "Translate after transcription" toggle; if the user skips it there, they can still translate at Step 3.

- Only appears in step bar if subtitles exist to translate
- Source language auto-detected from transcription
- Two translation engines as radio cards:
  - **Whisper translate** (any to English): "Higher quality, limited to English"
  - **Argos translate** (any to any): "Supports 30+ languages"
  - System recommends the best option based on target language
- During translation: progress bar, batch progress events
- Context panel: side-by-side original vs translated preview
- Skip: "Skip" link below step title advances to Embed or Export

#### Step 4 — Embed (Optional)

- Only appears for video inputs
- Mode selector as radio cards:
  - **Soft embed (mux):** "Adds subtitle track. No re-encoding. Fast." (Recommended badge)
  - **Hard burn:** "Renders text onto video. Permanent. Slow."
- Style options (hard burn only): preset selector + custom (font, color, position, opacity)
- Context panel: style preview thumbnail
- Confirmation dialog: mode, style, estimated time

#### Step 5 — Export

- Always the final step, available as soon as transcription completes
- **Download section:** SRT, VTT, JSON buttons with file sizes. Video download if embedded. "Download All" zip.
- **Preview section:** Full subtitle text with timecodes, copy-to-clipboard
- **Stats section:** Total segments, duration, processing time, per-step timing breakdown
- **Next actions:** "New Transcription", "Re-transcribe with different model", "Translate to another language"

### Cross-Feature Triggers

| When this happens... | ...the system suggests: |
|---------------------|------------------------|
| Transcription completes on video file | "Embed subtitles into your video?" |
| Transcription completes with non-English source | "Translate to English?" |
| Translation completes on video file | "Embed translated subtitles?" |
| User revisits Step 2 from Export | If `File` object is still in memory (same session): pre-fills same file, offers "Try a different model" which re-submits to `POST /upload` creating a new task. If page was refreshed: shows "Upload the file again to re-transcribe" |
| User has preferences saved | All forms pre-fill with saved defaults |
| Model not loaded | "This model needs ~30s to load. Proceed?" + option to pick loaded model |
| System under load | "Queue position: 3. Estimated wait: ~2 minutes" |

### Error Recovery

| Error | User sees | Recovery |
|-------|-----------|----------|
| Upload fails (size/type) | Inline error on upload zone | "Try a different file" |
| SSE disconnects | Yellow banner: "Connection lost. Reconnecting..." | Auto-reconnect with backoff |
| Transcription fails | Red alert with error detail | "Retry" or "Try different model" |
| Translation fails | Red alert with reason | "Retry" or "Skip translation" |
| Embed fails (ffmpeg) | Red alert with reason | "Retry" or "Download subtitles without embedding" |
| Server critical | Full-width red banner | "System is recovering. Your project is saved." |

---

## 6. Backend Integration Notes

The workspace step model is a **frontend abstraction** over the backend's pipeline-based API. The backend has no "project" entity — it has **tasks**. Each task is created by `POST /upload` which accepts file + all options and runs the full pipeline. The frontend must bridge this gap.

### Step-to-API Mapping

| Workspace Step | Backend API Call | Notes |
|----------------|-----------------|-------|
| **Step 1: Upload** | Client-side only | File is selected and validated (type, size) on the client. `ffprobe` metadata is obtained via `POST /upload` response. No separate "upload without processing" endpoint exists. |
| **Step 2: Transcribe** | `POST /upload` (multipart form: file + model + language + options) | This is the main API call. Upload and transcription are bundled. The file is sent along with model selection, language, diarization, and translation options. Returns `task_id`. |
| **Step 3: Translate** | Included in `POST /upload` via `translate_to_english` or `translate_to` params, OR new `POST /translate/{task_id}` endpoint (see Section 15) | If the user selects translation at Step 2, it runs as part of the pipeline. For post-hoc translation (user decides after seeing results), a new backend endpoint is required. |
| **Step 4: Embed** | `POST /embed/{task_id}/quick` (soft mux) or `POST /combine` (hard burn) | These endpoints already exist and operate on completed tasks. No changes needed. |
| **Step 5: Export** | `GET /download/{task_id}/{format}`, `GET /download/{task_id}/all` | Existing endpoints. No changes needed. |

### Key Integration Decisions

1. **"Project" = `task_id`**: The frontend route `/project/:id` uses `task_id` as `:id`. There is no separate project entity.

2. **Step 1 is client-side only**: File selection, validation, and preview happen before any API call. The `UploadZone` component holds the `File` object in memory. The actual upload happens when the user clicks "Begin Transcription" at Step 2.

3. **Translation at Step 2 vs Step 3**: The user can optionally select translation at Step 2 (pre-transcription), which runs as part of the pipeline. If they skip it at Step 2 and later want to translate at Step 3, the new `POST /translate/{task_id}` endpoint is called (see Section 15).

4. **Re-transcription**: "Re-transcribe with different model" (from Export) works by keeping the `File` object in the workspace store's memory. The client re-submits to `POST /upload` with the same file and new options, creating a new `task_id`. The old project remains in history.

5. **SSE connection**: `GET /events/{task_id}` is connected as soon as `POST /upload` returns the `task_id`. Progress events drive Step 2's progress display.

6. **Session restore**: When navigating to `/project/:id` directly (bookmark, page refresh):
   - Poll `GET /progress/{task_id}` for current task state
   - If task status is `processing`: connect SSE via `GET /events/{task_id}`, render Step 2 in-progress view
   - If task status is `completed`: render Export step with results
   - If task status is `failed`: render error state at Step 2 with retry option
   - File metadata is restored from the task's stored info (no need to re-probe)

### Project Drawer Data Source

Recent projects are sourced from:
1. **localStorage** — `recentProjects[]` array of `{ taskId, filename, createdAt, status, duration }` (max 20 entries, client-managed)
2. **Backend validation** — On load, batch-validate task IDs still exist via `GET /progress/{task_id}` (prune stale entries)
3. **Search/filter** — Client-side filtering on the localStorage list (no backend search endpoint needed)

---

## 7. State Architecture

### Zustand Stores

The rebuild replaces all existing stores with a new architecture:

```typescript
// workspaceStore.ts — Core workspace state
interface WorkspaceState {
  // Project identity
  projectId: string | null;           // task_id from backend
  file: File | null;                  // Held in memory for re-transcription
  fileMetadata: {
    filename: string;
    duration: number;                 // seconds
    format: string;                   // "H.264/AAC"
    resolution: string | null;        // "1920x1080" or null for audio
    size: number;                     // bytes
    codec: string;
    isVideo: boolean;
  } | null;

  // Step navigation
  currentStep: 'upload' | 'transcribe' | 'translate' | 'embed' | 'export';
  stepStatuses: {
    upload: 'pending' | 'completed';
    transcribe: 'pending' | 'active' | 'completed' | 'failed';
    translate: 'pending' | 'active' | 'completed' | 'skipped' | 'hidden';
    embed: 'pending' | 'active' | 'completed' | 'skipped' | 'hidden';
    export: 'pending' | 'active' | 'completed';
  };

  // Transcription state
  transcribeOptions: {
    model: string;
    language: string;
    diarization: boolean;
    wordTimestamps: boolean;
    translateToEnglish: boolean;
    translateTo: string | null;
  };
  transcribeProgress: {
    percentage: number;
    segmentCount: number;
    totalSegments: number;
    eta: number | null;               // seconds
    currentStep: string;              // "extracting_audio", "transcribing", etc.
    elapsed: number;                  // seconds
    speed: number | null;             // e.g. 3.2 (realtime multiplier)
  } | null;
  segments: Array<{
    index: number;
    start: number;
    end: number;
    text: string;
    speaker?: string;
  }>;

  // Translation state
  translationProgress: {
    percentage: number;
    batchesCompleted: number;
    totalBatches: number;
  } | null;
  translatedSegments: Array<{
    index: number;
    start: number;
    end: number;
    text: string;
  }>;

  // Embed state
  embedMode: 'soft' | 'hard' | null;
  embedStyle: string | null;
  embedProgress: number | null;

  // Export data
  downloadUrls: {
    srt: string | null;
    vtt: string | null;
    json: string | null;
    video: string | null;
    all: string | null;
  };
  timingBreakdown: Array<{ step: string; duration: number }>;

  // Actions
  initFromUpload: (file: File, metadata: FileMetadata) => void;
  setProjectId: (id: string) => void;
  setCurrentStep: (step: string) => void;
  updateTranscribeProgress: (progress: Partial<TranscribeProgress>) => void;
  addSegment: (segment: Segment) => void;
  completeStep: (step: string) => void;
  skipStep: (step: string) => void;
  reset: () => void;
  restoreFromTask: (taskData: TaskProgress) => void;
}

// uiStore.ts — App chrome state
interface UIState {
  // Navigation
  currentPage: string;                // '/', '/project/:id', '/status', etc.

  // Layout
  contextPanelOpen: boolean;          // mobile: collapsible
  projectDrawerOpen: boolean;         // home: collapsible

  // Connection
  sseConnected: boolean;
  sseReconnecting: boolean;
  lastEventTime: number | null;

  // System
  systemHealth: 'healthy' | 'degraded' | 'critical';
  modelPreloadStatus: Record<string, 'loaded' | 'loading' | 'unloaded'>;

  // Actions
  navigate: (path: string) => void;
  toggleContextPanel: () => void;
  toggleProjectDrawer: () => void;
  setSSEConnected: (connected: boolean) => void;
  setSystemHealth: (health: string) => void;
}

// preferencesStore.ts — User defaults (persisted to localStorage)
interface PreferencesState {
  defaultModel: string;               // default: 'medium'
  defaultLanguage: string;            // default: 'auto'
  defaultFormat: string;              // default: 'srt'
  autoCopyOnComplete: boolean;        // default: false
  confirmBeforeTranscribe: boolean;   // default: true
  dismissedSuggestions: string[];     // suggestion IDs dismissed this session

  // Actions
  updatePreference: (key: string, value: any) => void;
  resetDefaults: () => void;
}

// toastStore.ts — Notification state
interface ToastState {
  toasts: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    description?: string;
    duration: number;
    action?: { label: string; onClick: () => void };
  }>;

  // Actions
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

// recentProjectsStore.ts — Project history (persisted to localStorage)
interface RecentProjectsState {
  projects: Array<{
    taskId: string;
    filename: string;
    createdAt: string;                // ISO date
    status: 'processing' | 'completed' | 'failed';
    duration: number | null;          // file duration in seconds
    lastStep: string;                 // last active step for quick resume
  }>;

  // Actions
  addProject: (project: RecentProject) => void;
  updateProject: (taskId: string, updates: Partial<RecentProject>) => void;
  removeProject: (taskId: string) => void;
  pruneStale: (validIds: string[]) => void;
}
```

### Store Relationships

```
recentProjectsStore (localStorage)
        |
        v (user clicks project)
workspaceStore (active project state)
        |
        +-- reads --> preferencesStore (smart defaults)
        +-- triggers --> toastStore (notifications)
        +-- reads/writes --> uiStore (navigation, SSE status)
```

---

## 8. Layout Specifications

### Global Layout

| Property | Value |
|----------|-------|
| Max content width | 1280px, centered |
| Header height | 56px, sticky top, white, border-bottom gray-200 |
| Page padding | 24px horizontal (desktop), 16px (mobile) |
| Foundation bg | #F3F4F6 (gray-100) |

### Home Screen Layout

| Element | Desktop | Mobile |
|---------|---------|--------|
| Upload card | flex-1 (fills remaining space), white card, shadow-md | Full width |
| Project drawer | 320px fixed width, white card | Collapsible accordion below upload |
| Gap | 24px (spacing-6) | 16px vertical |
| Feature cards | 3-column row below | Stacked vertical |

### Workspace Layout

| Element | Desktop (>=1024px) | Mobile (<1024px) |
|---------|-------------------|-------------------|
| Step bar | Full width, single line, white bg, border-bottom | Horizontally scrollable |
| Main panel | flex-1 (fills remaining space), white card | Full width |
| Context panel | 360px fixed width, white card | Below main panel, collapsible |
| Gap between panels | 24px | 16px vertical |

---

## 9. Key Screen Designs

### Home (Quick-Start)

```
+--------------------------------------------------------------+
| HEADER  [SubForge logo]     Home  Status  About    [Prefs]   |
+--------------------------------------------------------------+
| bg: gray-100                                                  |
|                                                               |
|  +-----------------------------------+  +-------------------+|
|  | white card, shadow-md              |  | PROJECTS [search] ||
|  |                                    |  | white card        ||
|  |  +------------------------------+ |  |                   ||
|  |  | Upload Zone                   | |  | +---------------+||
|  |  | dashed border gray-300        | |  | | interview.mp4 |||
|  |  | bg: gray-50                   | |  | | 2m ago - Done  |||
|  |  |                               | |  | +---------------+||
|  |  | [cloud upload icon]           | |  | +---------------+||
|  |  | "Drop your file here"         | |  | | lecture.wav   |||
|  |  | "or click to browse"          | |  | | 1h ago - Done  |||
|  |  |                               | |  | +---------------+||
|  |  | Supports MP4, MKV, WAV,       | |  |                   ||
|  |  | MP3, FLAC and more            | |  |                   ||
|  |  +------------------------------+ |  |                   ||
|  |  Max file size: 2GB               |  |                   ||
|  +-----------------------------------+  +-------------------+|
|                                                               |
|  +-----------------------------------------------------------+|
|  | 3 feature cards:                                           ||
|  | [Accurate] [30+ Languages] [Fast Processing]               ||
|  +-----------------------------------------------------------+|
+--------------------------------------------------------------+
```

### Workspace — Transcribe (Form)

```
+--------------------------------------------------------------+
| HEADER                                                        |
+--------------------------------------------------------------+
| STEP BAR                                                      |
| [v Upload] -- [* Transcribe] -- [ Translate ] -- [ Embed ]   |
|              -- [ Export ]                                     |
| file: interview.mp4 - 12:34 - 1080p - 245 MB        [Home]  |
+--------------------------------------------------------------+
|                                                               |
|  MAIN PANEL (65%)               | CONTEXT PANEL (35%)        |
|  white card                     | white card                  |
|                                 |                             |
|  Transcription Model            | FILE INFO                   |
|  +---------------------------+  | +-------------------------+ |
|  | o Tiny    - Fastest       |  | | interview.mp4           | |
|  | o Base    - Fast          |  | | Duration: 12:34         | |
|  | o Small   - Balanced      |  | | Format: H.264/AAC       | |
|  | * Medium  - Recommended   |  | | Resolution: 1080p       | |
|  | o Large   - Most accurate |  | | Size: 245 MB            | |
|  +---------------------------+  | +-------------------------+ |
|                                 |                             |
|  Language                       | HINTS                       |
|  [Auto-detect            v]    | "Medium model offers the    |
|                                 |  best balance of speed      |
|  > Advanced Options             |  and accuracy for most      |
|    [ ] Speaker diarization      |  content."                  |
|    [ ] Word-level timestamps    |                             |
|                                 |                             |
|  [Begin Transcription ->]      |                             |
|                                 |                             |
+---------------------------------+-----------------------------+
```

### Workspace — Transcribe (In Progress)

```
+--------------------------------------------------------------+
| STEP BAR                                                      |
| [v Upload] -- [* Transcribe @] -- [ Translate ] -- [ Embed ] |
+--------------------------------------------------------------+
|                                                               |
|  MAIN PANEL                     | CONTEXT PANEL               |
|                                 |                             |
|  Transcribing...                | LIVE PREVIEW                |
|  Model: medium - Language: en   | +-------------------------+ |
|                                 | | 00:00:01 -> 00:00:04    | |
|  ============----  67%          | | "Welcome to today's     | |
|  142 / 212 segments             | |  interview about..."    | |
|  ETA: ~45 seconds               | |                         | |
|                                 | | 00:00:04 -> 00:00:08    | |
|  * Live  -  Elapsed: 1:23      | | "Thank you for          | |
|                                 | |  having me here."       | |
|  Pipeline Steps:                | |                         | |
|  v Audio extraction   0.8s      | | 00:00:08 -> 00:00:12    | |
|  v Model loaded       0.2s      | | "Let's start with       | |
|  * Transcribing...    1:22      | |  the basics..."         | |
|  o Formatting                   | |                         | |
|  o Writing output               | | [auto-scrolling]        | |
|                                 | +-------------------------+ |
|       [Cancel]                  |                             |
|                                 | Segments: 142               |
|                                 | Speed: 3.2x realtime        |
+---------------------------------+-----------------------------+
```

### Workspace — Export

```
+--------------------------------------------------------------+
| STEP BAR                                                      |
| [v Upload] -- [v Transcribe] -- [- Translate] -- [v Embed]   |
|              -- [* Export]                                     |
+--------------------------------------------------------------+
|                                                               |
|  MAIN PANEL                     | CONTEXT PANEL               |
|                                 |                             |
|  v Your subtitles are ready     | SUBTITLE PREVIEW            |
|                                 | +-------------------------+ |
|  Download Subtitles             | | 1                       | |
|  +--------+ +--------+ +-----+ | | 00:00:01 -> 00:00:04    | |
|  | SRT    | | VTT    | | JSON| | | Welcome to today's      | |
|  | 12 KB  | | 14 KB  | |89KB | | | interview about...      | |
|  +--------+ +--------+ +-----+ | |                         | |
|                                 | | 2                       | |
|  Download Video (embedded)      | | 00:00:04 -> 00:00:08    | |
|  +----------------------------+ | | Thank you for           | |
|  | interview_subtitled.mkv    | | | having me here.         | |
|  | 247 MB - Soft embed        | | |                         | |
|  +----------------------------+ | | ...212 segments         | |
|                                 | | [Copy all]              | |
|  [Download All (.zip)]         | +-------------------------+ |
|                                 |                             |
|  > Timing Breakdown             | STATS                       |
|    Audio extraction:  0.8s      | Segments: 212               |
|    Model loading:     0.2s      | Duration: 12:34             |
|    Transcription:     2:05      | Model: medium               |
|    Embedding:         1.2s      | Language: English            |
|    Total:             2:08      | Speed: 5.8x realtime        |
|                                 |                             |
|  What's next?                   |                             |
|  [New Transcription]            |                             |
|  [Re-transcribe with Large]     |                             |
|  [Translate to another lang]    |                             |
+---------------------------------+-----------------------------+
```

---

## 10. Responsive Behavior

| Breakpoint | Layout Change |
|------------|--------------|
| < 640px (mobile) | Single column. Context panel below main. Step bar scrolls horizontally. Project drawer becomes collapsible accordion. |
| 640–1023px (tablet) | Single column. Context panel collapsible (toggle button). Step bar wraps to 2 lines if needed. |
| >= 1024px (desktop) | Two columns: main 65% + context 35%. Step bar single line. Full project drawer. |
| >= 1280px (wide) | Same as desktop, content max-width 1280px, centered. |

**Touch targets:** 44px minimum on mobile (WCAG 2.5.5).

---

## 11. Animation System

| Animation | Where | Behavior | Duration |
|-----------|-------|----------|----------|
| Step pulse | Active step dot | Gentle blue pulse | 2s cycle |
| Progress shimmer | Progress bar | Left-to-right gradient sweep | Continuous |
| Segment slide-in | Live preview | New segments slide from bottom | 200ms |
| Success bounce | Completion checkmark | Scale 0 -> 1.1 -> 1 | 300ms |
| Card hover lift | Project cards | translateY(-1px) + shadow increase | 150ms |
| Panel transition | Step change | Fade out -> fade in | 150ms + 150ms |
| Drawer slide | Project drawer | SlideInRight | 200ms |
| Toast enter/exit | Notifications | Slide in from top-right, fade out | 200ms / 300ms |

All animations respect `prefers-reduced-motion: reduce`.

---

## 12. Accessibility

### Standards
- **WCAG 2.1 AA** compliance across all components
- **Keyboard navigation** — all interactive elements reachable via Tab, operable via Enter/Space
- **Focus management** — visible focus rings (2px blue outline, 2px offset), `:focus-visible` only
- **Focus trapping** — dialogs and modals trap focus within
- **Skip navigation** — hidden link to skip to main content
- **Screen reader support** — semantic HTML, ARIA labels, live regions for dynamic content
- **Reduced motion** — all animations disabled when `prefers-reduced-motion: reduce`
- **Color contrast** — minimum 4.5:1 for text, 3:1 for large text and UI components
- **Touch targets** — 44px minimum on mobile

### ARIA Patterns
- Step bar: `role="navigation"` with `aria-label="Pipeline steps"`, `aria-current="step"` on active
- Progress bar: `role="progressbar"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- Live preview: `aria-live="polite"` for new segments
- Toast: `role="status"` with `aria-live="polite"`
- Dialogs: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- Connection banner: `role="alert"` for connection loss

---

## 13. Component API Reference

### Button

```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
  size: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  icon?: ReactNode;       // Leading icon
  iconRight?: ReactNode;  // Trailing icon
  fullWidth?: boolean;
  children: ReactNode;
  onClick?: () => void;
}
```

**Dimensions:**
- sm: h-32px, px-12px, text-sm
- md: h-36px, px-16px, text-sm
- lg: h-40px, px-20px, text-base

### Card

```typescript
interface CardProps {
  padding?: 'sm' | 'md' | 'lg';  // 12px, 16px, 24px
  shadow?: boolean;                // default true
  border?: boolean;                // default false
  header?: {
    title: string;
    subtitle?: string;
    action?: ReactNode;
  };
  children: ReactNode;
}
```

### Input

```typescript
interface InputProps {
  type?: 'text' | 'password' | 'search';
  size?: 'sm' | 'md';
  label?: string;
  placeholder?: string;
  error?: string;
  helperText?: string;
  disabled?: boolean;
  icon?: ReactNode;         // Leading icon
  value: string;
  onChange: (value: string) => void;
}
```

### Select

```typescript
interface SelectProps {
  size?: 'sm' | 'md';
  label?: string;
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  options: Array<{ value: string; label: string; group?: string }>;
  value: string;
  onChange: (value: string) => void;
}
```

### Dialog

```typescript
interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;     // Footer buttons
  size?: 'sm' | 'md' | 'lg';  // 400px, 500px, 640px
}
```

### ConfirmDialog

```typescript
interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;   // default "Confirm"
  cancelLabel?: string;    // default "Cancel"
  variant?: 'default' | 'danger';
  loading?: boolean;
}
```

### Toast

```typescript
interface ToastProps {
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  description?: string;
  duration?: number;       // ms, default 5000
  action?: {
    label: string;
    onClick: () => void;
  };
}
```

### StepIndicator

```typescript
interface StepIndicatorProps {
  steps: Array<{
    id: string;
    label: string;
    status: 'pending' | 'active' | 'completed' | 'skipped';
    optional?: boolean;
    hidden?: boolean;      // true for non-applicable steps
  }>;
  onStepClick: (stepId: string) => void;
}
```

### ProgressBar

```typescript
interface ProgressBarProps {
  value: number;           // 0-100
  indeterminate?: boolean;
  label?: string;
  showPercentage?: boolean;
  size?: 'sm' | 'md';     // 4px, 8px height
}
```

### UploadZone

```typescript
interface UploadZoneProps {
  onFileAccepted: (file: File) => void;
  onError: (error: string) => void;
  maxSize?: number;        // bytes, default 2GB
  accept?: string[];       // MIME types
  uploading?: boolean;
  uploadProgress?: number; // 0-100
}
```

### SubtitlePreview

```typescript
interface SubtitlePreviewProps {
  segments: Array<{
    index: number;
    start: number;         // seconds (float), e.g. 1.0 — component formats to "00:00:01" internally
    end: number;           // seconds (float), e.g. 4.0 — matches backend SegmentEvent format
    text: string;
  }>;
  autoScroll?: boolean;
  highlightIndex?: number;
  onCopyAll?: () => void;
}
```

### FileInfo

```typescript
interface FileInfoProps {
  filename: string;
  duration?: string;
  format?: string;
  resolution?: string;
  size: string;
  codec?: string;
}
```

### ModelSelector

```typescript
interface ModelSelectorProps {
  models: Array<{
    id: string;
    name: string;
    description: string;
    speed: string;
    accuracy: string;
    recommended?: boolean;
    loaded?: boolean;        // true if model is ready in memory
    preloading?: boolean;    // true if model is currently being loaded
  }>;
  value: string;
  onChange: (modelId: string) => void;
}
```

**Model status display:** Models marked `loaded: true` show a green "Ready" badge. Models with `preloading: true` show a spinner + "Loading..." badge. Unloaded models show "~30s to load" hint. Status polled from `GET /api/model-status`.

---

## 14. Interaction Patterns

### Hover
- Background shift: transparent to gray-50 (150ms)
- Cards: translateY(-1px) + shadow increase
- Buttons: background darkens one shade
- Links: underline appears

### Focus
- 2px blue (#2563EB) outline with 2px offset
- `:focus-visible` only (no outline on mouse click)
- Tab order follows visual layout

### Loading States
- **Button loading:** Spinner replaces icon, text changes to "Processing...", button disabled
- **Page loading:** Skeleton placeholders for cards, text blocks, and media
- **Data loading:** Spinner centered in empty area with "Loading..." text
- **Model loading:** Connection banner: "Loading model... This may take up to 30 seconds"

### Error States
- **Field error:** Red border on input, error message below (text-sm, danger color)
- **Form error:** Toast notification with error summary
- **System error:** Red alert inline with retry action
- **Critical error:** Full-width red banner with status message

### Empty States
- **No projects:** Illustrated icon + "No projects yet. Upload a file to get started." + Upload CTA
- **No subtitles:** "Transcription hasn't started. Choose a model above."
- **No translations:** "Original subtitles only. Add a translation?"

### Confirmation Pattern
All actions that start a process or are destructive use `ConfirmDialog`:
- Starting transcription: summary of file + model + language + estimated time
- Cancelling transcription: "Are you sure? Progress will be lost."
- Deleting a project: "This will remove the file and all subtitles."
- Starting embed (hard burn): "This will re-encode your video. Estimated time: X"

### Smart Suggestions
After each step completes, the system offers contextual next actions:
- Displayed as a light blue tinted card (`primary-light` background)
- Contains 2-3 action buttons for the most likely next steps
- Dismissable — "Skip" or "Later" option always available
- Remembers dismissed suggestions per session

### Session Restore

When a user navigates to `/project/:id` directly (bookmark, page refresh, or clicking a project in the drawer):

1. **Fetch task state:** `GET /progress/{task_id}` returns current status, progress, and results
2. **Restore workspace store:** `workspaceStore.restoreFromTask(taskData)` populates all fields
3. **Determine current step:**
   - If `status === 'processing'`: set `currentStep` to `transcribe`, connect SSE via `GET /events/{task_id}`, render in-progress view
   - If `status === 'completed'`: set `currentStep` to `export`, populate download URLs and segments from task data
   - If `status === 'failed'`: set `currentStep` to `transcribe`, render error state with retry option
4. **File metadata:** Restored from the task's stored probe data (no need to re-probe). The `File` object is NOT available after refresh — "Re-transcribe" requires re-uploading.
5. **SSE reconnection:** Exponential backoff (1s, 2s, 4s, 8s, 16s, max 30s). Yellow banner shown during reconnection. Auto-recovers when server comes back.

---

## 15. Required API Additions

New backend endpoints needed to support the workspace model:

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `POST /translate/{task_id}` | POST | Post-hoc translation of an already-completed task's subtitles. Accepts `target_language` and `engine` (whisper/argos). Returns task progress via SSE. | **Required** — enables Step 3 as a separate action after transcription |
| `DELETE /tasks/bulk` | DELETE | Bulk delete tasks by ID list. Body: `{ "task_ids": ["id1", "id2"] }`. | **Nice-to-have** — for project drawer bulk actions. Workaround: loop `DELETE /tasks/{id}` |
| `GET /download/{task_id}/all` | GET | Download all subtitle formats as zip. | **Verify** — may already exist. If not, required for Export "Download All" button |

**Endpoints already sufficient (no changes needed):**
- `POST /upload` — handles file + transcription + optional translation in one call
- `POST /embed/{task_id}/quick` — soft mux embedding
- `POST /combine` — hard burn embedding
- `GET /download/{task_id}/{format}` — individual format download
- `GET /progress/{task_id}` — task status and progress
- `GET /events/{task_id}` — SSE stream for real-time updates
- `GET /api/model-status` — model preload status
- `GET /health/stream` — system health SSE
- `DELETE /tasks/{task_id}` — single task deletion

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
| UI Primitives | Radix UI (Tooltip, Collapsible, Progress, Separator) |
| Drag & Drop | react-dropzone |
| Variant Management | class-variance-authority |
| Class Merging | clsx + tailwind-merge |
| Testing | Vitest (unit) + Playwright (e2e) |
| Real-time | Server-Sent Events (EventSource API) |
| Upload | XHR with progress tracking |
