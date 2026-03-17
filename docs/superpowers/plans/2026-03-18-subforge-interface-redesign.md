# SubForge "Drop, See, Refine" Frontend — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Full frontend rebuild with "Drop, See, Refine" philosophy — drop a file, see subtitles, refine from the editor. Zero-config upload, editor-centric, adaptive file detection.

**Architecture:** Replace all existing frontend code. Landing page with upload zone + recent projects. Editor page at `/editor/:id` with inline subtitle editing, download, translate, embed, re-transcribe — all accessible from one workspace. 5 Zustand stores, parameterized client-side routing, SSE for real-time progress.

**Tech Stack:** React 19, TypeScript 5.9, Vite 6, Tailwind CSS v4 (CSS-in-CSS), Zustand 5, Radix UI, Lucide React, react-dropzone, class-variance-authority, clsx + tailwind-merge, Vitest + Playwright.

**Spec:** `docs/superpowers/specs/2026-03-18-subforge-interface-redesign-design.md`

---

## Parallel Execution Map

```
Phase 0: Foundation (sequential — everything depends on this)
  Task 1: Shared types + utilities
  Task 2: Design tokens (index.css)
  Task 3: cn utility + Toast store

Phase 1: Independent streams (ALL PARALLEL)
  Stream A — UI Primitives:     Tasks 4-12
  Stream B — Stores:            Tasks 13-16
  Stream C — API Client:        Task 17
  Stream D — Hooks:             Tasks 18-20

Phase 2: Pages + Features (ALL PARALLEL, depends on Phase 1)
  Stream E — Layout + Router:   Tasks 21-24
  Stream F — Landing Page:      Tasks 25-27
  Stream G — Editor Page:       Tasks 28-35
  Stream H — System:            Tasks 36-37

Phase 3: Integration (depends on Phase 2)
  Task 38: Wire landing → editor flow
  Task 39: Static pages
  Task 40: Session restore + edge cases

Phase 4: Testing + Deploy (depends on Phase 3)
  Task 41: Integration tests
  Task 42: Accessibility + responsive tests
  Task 43: Build + deploy to newui
```

---

## File Structure

```
frontend/src/
├── types.ts                          # Shared types + utilities
├── index.css                         # Design tokens (rewrite)
├── main.tsx                          # Entry point (minor update)
├── Router.tsx                        # Parameterized routing (rewrite)
│
├── components/
│   ├── ui/                           # UI Primitives (all new)
│   │   ├── Button.tsx
│   │   ├── IconButton.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   ├── Select.tsx
│   │   ├── Badge.tsx
│   │   ├── Dialog.tsx
│   │   ├── ConfirmDialog.tsx
│   │   ├── Tooltip.tsx
│   │   ├── Toast.tsx
│   │   ├── ToastContainer.tsx
│   │   ├── Alert.tsx
│   │   ├── ProgressBar.tsx
│   │   ├── Spinner.tsx
│   │   ├── Skeleton.tsx
│   │   ├── EmptyState.tsx
│   │   ├── Divider.tsx
│   │   └── cn.ts
│   │
│   ├── layout/                       # Layout shell
│   │   ├── AppShell.tsx
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   └── PageLayout.tsx
│   │
│   ├── landing/                      # Landing page components
│   │   ├── UploadZone.tsx
│   │   ├── UploadProgress.tsx
│   │   ├── ProjectGrid.tsx
│   │   └── ProjectCard.tsx
│   │
│   ├── editor/                       # Editor page components
│   │   ├── EditorToolbar.tsx
│   │   ├── ProgressView.tsx
│   │   ├── PipelineSteps.tsx
│   │   ├── LivePreview.tsx
│   │   ├── SegmentList.tsx
│   │   ├── SegmentRow.tsx
│   │   ├── SearchBar.tsx
│   │   ├── ContextPanel.tsx
│   │   ├── DownloadMenu.tsx
│   │   ├── TranslatePanel.tsx
│   │   ├── EmbedPanel.tsx
│   │   ├── RetranscribeDialog.tsx
│   │   ├── SmartSuggestion.tsx
│   │   └── CombineView.tsx
│   │
│   └── system/                       # System components
│       ├── HealthIndicator.tsx
│       ├── ConnectionBanner.tsx
│       └── ErrorBoundary.tsx
│
├── store/                            # 5 Zustand stores
│   ├── editorStore.ts
│   ├── uiStore.ts
│   ├── preferencesStore.ts
│   ├── toastStore.ts
│   └── recentProjectsStore.ts
│
├── hooks/                            # Custom hooks
│   ├── useSSE.ts
│   ├── useHealthStream.ts
│   └── useFocusTrap.ts
│
├── pages/                            # Page components
│   ├── LandingPage.tsx
│   ├── EditorPage.tsx
│   ├── StatusPage.tsx
│   ├── AboutPage.tsx
│   ├── SecurityPage.tsx
│   └── ContactPage.tsx
│
├── api/                              # API client (modify existing)
│   ├── client.ts
│   └── types.ts
│
└── __tests__/                        # Tests
    ├── types.test.ts
    ├── ui/
    │   ├── Button.test.tsx
    │   ├── Card.test.tsx
    │   ├── Input.test.tsx
    │   ├── Dialog.test.tsx
    │   ├── ProgressBar.test.tsx
    │   └── Toast.test.tsx
    ├── store/
    │   ├── editorStore.test.ts
    │   ├── uiStore.test.ts
    │   ├── preferencesStore.test.ts
    │   ├── toastStore.test.ts
    │   └── recentProjectsStore.test.ts
    ├── hooks/
    │   └── useSSE.test.ts
    ├── landing/
    │   └── UploadZone.test.tsx
    ├── editor/
    │   ├── SegmentRow.test.tsx
    │   ├── SegmentList.test.tsx
    │   └── SearchBar.test.tsx
    ├── integration/
    │   ├── upload-flow.test.tsx
    │   └── session-restore.test.tsx
    ├── accessibility.test.tsx
    └── responsive.test.tsx
```

---

## Phase 0: Foundation

### Task 1: Shared Types + Utilities

**Files:**
- Create: `frontend/src/types.ts`
- Test: `frontend/src/__tests__/types.test.ts`

- [ ] **Step 1: Write types and utility functions**

```typescript
// frontend/src/types.ts
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
  start: number
  end: number
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

export function formatTimecode(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return [h, m, s].map(v => String(v).padStart(2, '0')).join(':')
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

export function detectUploadType(files: File[]): 'transcribe' | 'combine' | 'edit-srt' | 'unknown' {
  const mediaExts = ['.mp4', '.mkv', '.avi', '.webm', '.mov', '.mp3', '.wav', '.flac']
  const subtitleExts = ['.srt', '.vtt']
  const hasMedia = files.some(f => mediaExts.some(e => f.name.toLowerCase().endsWith(e)))
  const hasSubtitle = files.some(f => subtitleExts.some(e => f.name.toLowerCase().endsWith(e)))
  if (hasMedia && hasSubtitle) return 'combine'
  if (hasMedia) return 'transcribe'
  if (hasSubtitle) return 'edit-srt'
  return 'unknown'
}
```

- [ ] **Step 2: Write tests**

```typescript
// frontend/src/__tests__/types.test.ts
import { describe, it, expect } from 'vitest'
import { formatTimecode, formatFileSize, formatDuration, detectUploadType } from '../types'

describe('formatTimecode', () => {
  it('formats zero', () => expect(formatTimecode(0)).toBe('00:00:00'))
  it('formats seconds', () => expect(formatTimecode(65)).toBe('00:01:05'))
  it('formats hours', () => expect(formatTimecode(3661)).toBe('01:01:01'))
})

describe('formatFileSize', () => {
  it('formats bytes', () => expect(formatFileSize(500)).toBe('500 B'))
  it('formats KB', () => expect(formatFileSize(1536)).toBe('1.5 KB'))
  it('formats MB', () => expect(formatFileSize(245 * 1024 * 1024)).toBe('245.0 MB'))
  it('formats GB', () => expect(formatFileSize(2 * 1024 * 1024 * 1024)).toBe('2.00 GB'))
})

describe('formatDuration', () => {
  it('formats minutes', () => expect(formatDuration(754)).toBe('12:34'))
  it('formats hours', () => expect(formatDuration(3754)).toBe('1:02:34'))
  it('formats zero', () => expect(formatDuration(0)).toBe('0:00'))
})

describe('detectUploadType', () => {
  const file = (name: string) => new File([''], name)
  it('detects transcription', () => expect(detectUploadType([file('video.mp4')])).toBe('transcribe'))
  it('detects combine', () => expect(detectUploadType([file('video.mp4'), file('subs.srt')])).toBe('combine'))
  it('detects SRT edit', () => expect(detectUploadType([file('subs.srt')])).toBe('edit-srt'))
  it('detects unknown', () => expect(detectUploadType([file('readme.txt')])).toBe('unknown'))
  it('detects audio', () => expect(detectUploadType([file('podcast.mp3')])).toBe('transcribe'))
})
```

- [ ] **Step 3: Run tests**

Run: `cd frontend && npx vitest run src/__tests__/types.test.ts`
Expected: 14 tests PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types.ts frontend/src/__tests__/types.test.ts
git commit -m "feat(ui): add shared types, utilities, and adaptive upload detection"
```

---

### Task 2: Design Tokens

**Files:**
- Rewrite: `frontend/src/index.css`

- [ ] **Step 1: Rewrite index.css with "Cool Professional" tokens**

Complete CSS file with all tokens from spec Section 2: gray-100 foundation, blue-600 accent, Inter/JetBrains Mono fonts, 4px spacing grid, light-only theme, all animations, accessibility utilities, scrollbar styling. (Full CSS identical to old plan Task 2 — same visual identity, different architecture.)

Key tokens: `--color-bg: #F3F4F6`, `--color-surface: #FFFFFF`, `--color-primary: #2563EB`, `--color-text: #111827`.

- [ ] **Step 2: Verify build compiles**

Run: `cd frontend && npx vite build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "feat(ui): add Drop See Refine design tokens — cool professional light theme"
```

---

### Task 3: cn Utility + Toast Store

**Files:**
- Rewrite: `frontend/src/components/ui/cn.ts`
- Rewrite: `frontend/src/store/toastStore.ts`
- Test: `frontend/src/__tests__/store/toastStore.test.ts`

Toast store must exist before Phase 1 because `ToastContainer` (UI primitive) imports it.

- [ ] **Step 1: Write cn.ts**

```typescript
// frontend/src/components/ui/cn.ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}
```

- [ ] **Step 2: Write toastStore with test**

```typescript
// frontend/src/store/toastStore.ts
import { create } from 'zustand'

export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  description?: string
  duration: number
  action?: { label: string; onClick: () => void }
}

interface ToastState {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id' | 'duration'> & { duration?: number }) => void
  removeToast: (id: string) => void
}

let counter = 0

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  addToast: (toast) => {
    const id = `toast-${++counter}-${Date.now()}`
    const duration = toast.duration ?? 5000
    set(s => ({ toasts: [...s.toasts, { ...toast, id, duration }] }))
    if (duration > 0) {
      setTimeout(() => set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })), duration)
    }
  },
  removeToast: (id) => set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })),
}))
```

Test: verify add, remove, unique IDs (same pattern as old plan).

- [ ] **Step 3: Run tests, commit**

```bash
git commit -m "feat(ui): add cn utility and toastStore foundation"
```

---

## Phase 1, Stream A: UI Primitives (Tasks 4-12)

These are identical in API to the old plan but listed here for completeness. Each task: write test first, then component, run test, commit.

### Task 4: Button + IconButton
- `frontend/src/components/ui/Button.tsx` — CVA variants: primary, secondary, ghost, danger, success. Sizes: sm, md, lg. Loading spinner. Icon slots.
- `frontend/src/components/ui/IconButton.tsx` — Icon-only button with aria-label.
- Test: render, click handler, loading state, disabled state.
- Commit: `feat(ui): add Button and IconButton`

### Task 5: Card
- `frontend/src/components/ui/Card.tsx` — Padding sm/md/lg. Shadow/border variants. Optional header with title/subtitle/action.
- Test: renders children, renders header, applies shadow, applies border.
- Commit: `feat(ui): add Card`

### Task 6: Input + Select
- `frontend/src/components/ui/Input.tsx` — Label, error, helper text, icon. Uses `useId()`.
- `frontend/src/components/ui/Select.tsx` — Options with optional groups. Same styling as Input.
- Test: label association, error display, onChange callback.
- Commit: `feat(ui): add Input and Select`

### Task 7: Dialog + ConfirmDialog
- `frontend/src/components/ui/Dialog.tsx` — Overlay, focus trap, Escape to close. `useId()` for aria-labelledby. Sizes: `max-w-[400px]`, `max-w-[500px]`, `max-w-[640px]`.
- `frontend/src/components/ui/ConfirmDialog.tsx` — Wraps Dialog with confirm/cancel buttons. Danger variant.
- Test: renders when open, hidden when closed, Escape calls onClose, confirm callback.
- Commit: `feat(ui): add Dialog and ConfirmDialog`

### Task 8: Badge + Divider
- `frontend/src/components/ui/Badge.tsx` — CVA variants: default, success, warning, danger, info. Dot indicator.
- `frontend/src/components/ui/Divider.tsx` — Horizontal line, optional label.
- Commit: `feat(ui): add Badge and Divider`

### Task 9: ProgressBar + Spinner + Skeleton
- `frontend/src/components/ui/ProgressBar.tsx` — Determinate/indeterminate. ARIA progressbar role. Label + percentage display.
- `frontend/src/components/ui/Spinner.tsx` — Animated SVG, sizes sm/md/lg.
- `frontend/src/components/ui/Skeleton.tsx` — Pulsing placeholder.
- Test: aria-valuenow, percentage display, indeterminate state.
- Commit: `feat(ui): add ProgressBar, Spinner, Skeleton`

### Task 10: Toast + ToastContainer + Alert
- `frontend/src/components/ui/Toast.tsx` — Type-colored (success/error/warning/info). Icon, dismiss button, optional action.
- `frontend/src/components/ui/ToastContainer.tsx` — Fixed top-right, reads from `toastStore`.
- `frontend/src/components/ui/Alert.tsx` — Inline persistent message with icon and optional action.
- Test: renders title/description, dismiss callback, action callback.
- Commit: `feat(ui): add Toast, ToastContainer, Alert`

### Task 11: EmptyState
- `frontend/src/components/ui/EmptyState.tsx` — Animated icon, title, description, action slot.
- Commit: `feat(ui): add EmptyState`

### Task 12: Tooltip
- `frontend/src/components/ui/Tooltip.tsx` — Radix-based. TooltipProvider wrapper.
- Commit: `feat(ui): add Tooltip`

---

## Phase 1, Stream B: Stores (Tasks 13-16)

### Task 13: Editor Store

**Files:**
- Create: `frontend/src/store/editorStore.ts`
- Test: `frontend/src/__tests__/store/editorStore.test.ts`

- [ ] **Step 1: Write editorStore test**

```typescript
// frontend/src/__tests__/store/editorStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { useEditorStore } from '../../store/editorStore'

describe('editorStore', () => {
  beforeEach(() => useEditorStore.getState().reset())

  it('starts in idle phase', () => {
    expect(useEditorStore.getState().phase).toBe('idle')
    expect(useEditorStore.getState().taskId).toBeNull()
  })

  it('sets task ID and transitions to processing', () => {
    useEditorStore.getState().setTaskId('task-123')
    expect(useEditorStore.getState().taskId).toBe('task-123')
  })

  it('updates progress', () => {
    useEditorStore.getState().updateProgress({
      percent: 45, segmentCount: 20, estimatedSegments: 50,
      eta: 30, elapsed: 15, speed: 3.2, pipelineStep: 'transcribing', message: 'Transcribing...'
    })
    expect(useEditorStore.getState().progress?.percent).toBe(45)
  })

  it('adds live segments', () => {
    useEditorStore.getState().addLiveSegment({ index: 0, start: 0, end: 5, text: 'Hello' })
    useEditorStore.getState().addLiveSegment({ index: 1, start: 5, end: 10, text: 'World' })
    expect(useEditorStore.getState().liveSegments).toHaveLength(2)
  })

  it('completes transcription', () => {
    useEditorStore.getState().setComplete({
      segments: [{ index: 0, start: 0, end: 5, text: 'Hello' }],
      language: 'en', modelUsed: 'large',
      timings: { extract: 0.8, transcribe: 45.2 }, isVideo: true
    })
    expect(useEditorStore.getState().phase).toBe('editing')
    expect(useEditorStore.getState().segments).toHaveLength(1)
    expect(useEditorStore.getState().language).toBe('en')
  })

  it('updates a segment', () => {
    useEditorStore.getState().setComplete({
      segments: [{ index: 0, start: 0, end: 5, text: 'Hello' }],
      language: 'en', modelUsed: 'large', timings: {}, isVideo: false
    })
    useEditorStore.getState().updateSegment(0, 'Hello World')
    expect(useEditorStore.getState().segments[0].text).toBe('Hello World')
  })

  it('sets error state', () => {
    useEditorStore.getState().setError('Something failed')
    expect(useEditorStore.getState().phase).toBe('error')
  })

  it('resets to initial state', () => {
    useEditorStore.getState().setTaskId('task-123')
    useEditorStore.getState().reset()
    expect(useEditorStore.getState().taskId).toBeNull()
    expect(useEditorStore.getState().phase).toBe('idle')
  })
})
```

- [ ] **Step 2: Write editorStore**

```typescript
// frontend/src/store/editorStore.ts
import { create } from 'zustand'
import type { Segment, SearchResult, EditorPhase, FileMetadata } from '../types'

interface ProgressData {
  percent: number
  segmentCount: number
  estimatedSegments: number
  eta: number | null
  elapsed: number
  speed: number | null
  pipelineStep: string
  message: string
}

interface CompleteData {
  segments: Segment[]
  language: string | null
  modelUsed: string | null
  timings: Record<string, number>
  isVideo: boolean
}

interface EditorState {
  taskId: string | null
  fileMetadata: FileMetadata | null
  phase: EditorPhase
  uploadPercent: number
  progress: ProgressData | null
  liveSegments: Segment[]
  segments: Segment[]
  language: string | null
  modelUsed: string | null
  timings: Record<string, number>
  isVideo: boolean
  searchQuery: string
  searchResults: SearchResult[]
  editingSegmentIndex: number | null

  setTaskId: (id: string) => void
  setFileMetadata: (meta: FileMetadata) => void
  setPhase: (phase: EditorPhase) => void
  setUploadPercent: (percent: number) => void
  updateProgress: (data: ProgressData) => void
  addLiveSegment: (segment: Segment) => void
  setComplete: (data: CompleteData) => void
  setError: (message: string) => void
  updateSegment: (index: number, text: string) => void
  setSearchQuery: (query: string) => void
  setSearchResults: (results: SearchResult[]) => void
  setEditingSegment: (index: number | null) => void
  reset: () => void
}

const initial = {
  taskId: null as string | null,
  fileMetadata: null as FileMetadata | null,
  phase: 'idle' as EditorPhase,
  uploadPercent: 0,
  progress: null as ProgressData | null,
  liveSegments: [] as Segment[],
  segments: [] as Segment[],
  language: null as string | null,
  modelUsed: null as string | null,
  timings: {} as Record<string, number>,
  isVideo: false,
  errorMessage: null as string | null,
  searchQuery: '',
  searchResults: [] as SearchResult[],
  editingSegmentIndex: null as number | null,
}

export const useEditorStore = create<EditorState>((set) => ({
  ...initial,

  setTaskId: (id) => set({ taskId: id }),
  setFileMetadata: (meta) => set({ fileMetadata: meta }),
  setPhase: (phase) => set({ phase }),
  setUploadPercent: (percent) => set({ uploadPercent: percent }),

  updateProgress: (data) => set({ progress: data, phase: 'processing' }),

  addLiveSegment: (segment) => set(s => ({
    liveSegments: [...s.liveSegments, segment],
  })),

  setComplete: (data) => set({
    phase: 'editing',
    segments: data.segments,
    language: data.language,
    modelUsed: data.modelUsed,
    timings: data.timings,
    isVideo: data.isVideo,
    liveSegments: [],
    progress: null,
  }),

  setError: (message) => set({
    phase: 'error',
    errorMessage: message,
    progress: null,
  }),

  updateSegment: (index, text) => set(s => ({
    segments: s.segments.map((seg, i) => i === index ? { ...seg, text } : seg),
  })),

  setSearchQuery: (query) => set({ searchQuery: query }),
  setSearchResults: (results) => set({ searchResults: results }),
  setEditingSegment: (index) => set({ editingSegmentIndex: index }),

  reset: () => set(initial),
}))
```

- [ ] **Step 3: Run tests**

Run: `cd frontend && npx vitest run src/__tests__/store/editorStore.test.ts`
Expected: 8 tests PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/store/editorStore.ts frontend/src/__tests__/store/editorStore.test.ts
git commit -m "feat(store): add editorStore — core state for Drop See Refine editor"
```

---

### Task 14: UI Store

**Files:**
- Rewrite: `frontend/src/store/uiStore.ts`
- Test: `frontend/src/__tests__/store/uiStore.test.ts`

- [ ] **Step 1: Write uiStore**

```typescript
// frontend/src/store/uiStore.ts
import { create } from 'zustand'

type ContextPanelContent = 'info' | 'translate' | 'embed' | 'search'

interface UIState {
  currentPage: string
  contextPanelContent: ContextPanelContent
  sseConnected: boolean
  sseReconnecting: boolean
  systemHealth: 'healthy' | 'degraded' | 'critical'
  modelPreloadStatus: Record<string, string>
  dismissedSuggestions: string[]

  setCurrentPage: (page: string) => void
  setContextPanel: (content: ContextPanelContent) => void
  setSSEConnected: (connected: boolean) => void
  setReconnecting: (reconnecting: boolean) => void
  setSystemHealth: (health: 'healthy' | 'degraded' | 'critical') => void
  setModelPreloadStatus: (status: Record<string, string>) => void
  dismissSuggestion: (id: string) => void
}

export const useUIStore = create<UIState>((set) => ({
  currentPage: '/',
  contextPanelContent: 'info',
  sseConnected: false,
  sseReconnecting: false,
  systemHealth: 'healthy',
  modelPreloadStatus: {},
  dismissedSuggestions: [],

  setCurrentPage: (page) => set({ currentPage: page }),
  setContextPanel: (content) => set({ contextPanelContent: content }),
  setSSEConnected: (connected) => set({ sseConnected: connected }),
  setReconnecting: (reconnecting) => set({ sseReconnecting: reconnecting }),
  setSystemHealth: (health) => set({ systemHealth: health }),
  setModelPreloadStatus: (status) => set({ modelPreloadStatus: status }),
  dismissSuggestion: (id) => set(s => ({
    dismissedSuggestions: [...s.dismissedSuggestions, id],
  })),
}))
```

- [ ] **Step 2: Write tests, run, commit**

```bash
git commit -m "feat(store): add uiStore for app chrome state"
```

---

### Task 15: Preferences Store

**Files:**
- Rewrite: `frontend/src/store/preferencesStore.ts`
- Test: `frontend/src/__tests__/store/preferencesStore.test.ts`

- [ ] **Step 1: Write with localStorage persistence via `persist` middleware**

Fields: `preferredFormat` (default 'srt'), `maxLineChars` (default 42).

- [ ] **Step 2: Test defaults, update, reset. Commit.**

```bash
git commit -m "feat(store): add preferencesStore with localStorage persistence"
```

---

### Task 16: Recent Projects Store

**Files:**
- Create: `frontend/src/store/recentProjectsStore.ts`
- Test: `frontend/src/__tests__/store/recentProjectsStore.test.ts`

- [ ] **Step 1: Write with localStorage persistence**

```typescript
// frontend/src/store/recentProjectsStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { RecentProject } from '../types'

const MAX_PROJECTS = 20

interface RecentProjectsState {
  projects: RecentProject[]
  addProject: (project: RecentProject) => void
  updateProject: (taskId: string, updates: Partial<RecentProject>) => void
  removeProject: (taskId: string) => void
  clearAll: () => void
}

export const useRecentProjectsStore = create<RecentProjectsState>()(
  persist(
    (set) => ({
      projects: [],
      addProject: (project) => set(s => ({
        projects: [project, ...s.projects.filter(p => p.taskId !== project.taskId)].slice(0, MAX_PROJECTS),
      })),
      updateProject: (taskId, updates) => set(s => ({
        projects: s.projects.map(p => p.taskId === taskId ? { ...p, ...updates } : p),
      })),
      removeProject: (taskId) => set(s => ({
        projects: s.projects.filter(p => p.taskId !== taskId),
      })),
      clearAll: () => set({ projects: [] }),
    }),
    { name: 'sg-recent-projects' }
  )
)
```

- [ ] **Step 2: Test add (max 20), update, remove, clear. Commit.**

```bash
git commit -m "feat(store): add recentProjectsStore with localStorage and max 20 limit"
```

---

## Phase 1, Stream C: API Client (Task 17)

### Task 17: Update API Client

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/types.ts`

- [ ] **Step 1: Verify existing endpoints work, add missing ones**

Ensure these exist in `api/client.ts` (most already do):
- `upload(fd)` — POST /upload
- `combineStart(fd)` — POST /combine
- `progress(taskId)` — GET /progress/:id
- `subtitles(taskId)` — GET /subtitles/:id
- `updateSubtitle(taskId, index, text)` — PUT /subtitles/:id/:index (may need to add)
- `updateSubtitles(taskId, segments)` — PUT /subtitles/:id (may need to add)
- `search(taskId, query, limit)` — GET /search/:id?q=...&limit=... (may need to add)
- `retranscribe(taskId, options)` — POST /tasks/:id/retranscribe (may need to add)
- `duplicates(filename, fileSize)` — GET /tasks/duplicates?... (may need to add)
- `embedPresets()` — GET /embed/presets
- `translationLanguages()` — GET /translation/languages

- [ ] **Step 2: Add missing methods**

```typescript
// Add to frontend/src/api/client.ts

  updateSubtitle: (taskId: string, index: number, text: string) =>
    fetch(`/subtitles/${taskId}/${index}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    }).then(r => json(r)),

  updateSubtitles: (taskId: string, segments: Array<{ start: number; end: number; text: string }>) =>
    fetch(`/subtitles/${taskId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ segments }),
    }).then(r => json(r)),

  search: (taskId: string, query: string, limit = 20) =>
    fetch(`/search/${taskId}?q=${encodeURIComponent(query)}&limit=${limit}`).then(r => json(r)),

  retranscribe: (taskId: string, options?: { model_size?: string; language?: string; diarize?: boolean }) =>
    fetch(`/tasks/${taskId}/retranscribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options ?? {}),
    }).then(r => json(r)),

  duplicates: (filename: string, fileSize: number) =>
    fetch(`/tasks/duplicates?filename=${encodeURIComponent(filename)}&file_size=${fileSize}`).then(r => json(r)),

  embedPresets: () =>
    fetch('/embed/presets').then(r => json(r)),
```

**Note:** The existing `api.uploadWithProgress()` method (XHR-based with progress callback) already exists in the codebase and supports both `/upload` and `/combine`. For combine uploads, the LandingPage should construct the FormData with `video` + `subtitle` fields and use the appropriate endpoint URL. The `uploadWithProgress` method accepts a `url` parameter or defaults to `/upload`.


- [ ] **Step 3: Commit**

```bash
git commit -m "feat(api): add subtitle editing, search, retranscribe, duplicates, embed presets endpoints"
```

---

## Phase 1, Stream D: Hooks (Tasks 18-20)

### Task 18: useSSE Hook

**Files:**
- Rewrite: `frontend/src/hooks/useSSE.ts`
- Test: `frontend/src/__tests__/hooks/useSSE.test.ts`

- [ ] **Step 1: Write useSSE that dispatches to editorStore**

Key SSE event → store action mapping:
- `progress` → `editorStore.updateProgress()`
- `segment` → `editorStore.addLiveSegment()`
- `step_change` → `editorStore.updateProgress()` (updates pipelineStep)
- `done` → `editorStore.setComplete()` + `recentProjectsStore.updateProject()`
- `error` → `editorStore.setError()`
- `paused` / `resumed` → update progress message
- `cancelled` → `editorStore.setError('Cancelled')`
- `embed_progress` / `embed_done` / `embed_error` → handled by EmbedPanel local state
- `translate_progress` / `translate_done` → handled by TranslatePanel local state

Reconnection: exponential backoff 1s → 2s → 4s → 8s → max 30s.
Watchdog: 45s no events → poll `GET /progress/:id` → decide reconnect or final state.

- [ ] **Step 2: Test with mock EventSource. Commit.**

```bash
git commit -m "feat(hooks): add useSSE dispatching to editorStore"
```

---

### Task 19: useHealthStream Hook

**Files:**
- Rewrite: `frontend/src/hooks/useHealthStream.ts`

- [ ] **Step 1: Write — SSE to /health/stream, dispatches to uiStore**

Updates: `systemHealth`, `sseConnected`, `modelPreloadStatus`. Grace period 2.5s before marking offline.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(hooks): add useHealthStream for system health SSE"
```

---

### Task 20: useFocusTrap Hook

**Files:**
- Keep/update: `frontend/src/hooks/useFocusTrap.ts`

- [ ] **Step 1: Verify existing hook works, update if needed. Commit if changed.**

---

## Phase 2, Stream E: Layout + Router (Tasks 21-24)

### Task 21: Router

**Files:**
- Rewrite: `frontend/src/Router.tsx`

- [ ] **Step 1: Write parameterized router**

```typescript
// frontend/src/Router.tsx
import { useState, useEffect, useMemo } from 'react'
import { LandingPage } from './pages/LandingPage'
import { EditorPage } from './pages/EditorPage'
import { StatusPage } from './pages/StatusPage'
import { AboutPage } from './pages/AboutPage'
import { SecurityPage } from './pages/SecurityPage'
import { ContactPage } from './pages/ContactPage'
import { useHealthStream } from './hooks/useHealthStream'
import { useUIStore } from './store/uiStore'

function matchRoute(path: string): { page: string; params: Record<string, string> } {
  const editorMatch = path.match(/^\/editor\/([^/]+)$/)
  if (editorMatch) return { page: 'editor', params: { id: editorMatch[1] } }
  const routes: Record<string, string> = {
    '/': 'landing', '/status': 'status', '/about': 'about',
    '/security': 'security', '/contact': 'contact',
  }
  return { page: routes[path] || 'landing', params: {} }
}

export function navigate(path: string) {
  window.history.pushState(null, '', path)
  window.dispatchEvent(new CustomEvent('spa-navigate'))
}

export function Router() {
  const [path, setPath] = useState(window.location.pathname)
  const setCurrentPage = useUIStore(s => s.setCurrentPage)
  useHealthStream()

  useEffect(() => {
    const handle = () => setPath(window.location.pathname)
    window.addEventListener('popstate', handle)
    window.addEventListener('spa-navigate', handle)
    return () => {
      window.removeEventListener('popstate', handle)
      window.removeEventListener('spa-navigate', handle)
    }
  }, [])

  const route = useMemo(() => matchRoute(path), [path])
  useEffect(() => { setCurrentPage(path) }, [path, setCurrentPage])

  switch (route.page) {
    case 'editor': return <EditorPage taskId={route.params.id} />
    case 'status': return <StatusPage />
    case 'about': return <AboutPage />
    case 'security': return <SecurityPage />
    case 'contact': return <ContactPage />
    default: return <LandingPage />
  }
}
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): add parameterized Router with /editor/:id support"
```

---

### Task 22: AppShell + Header

**Files:**
- Create: `frontend/src/components/layout/AppShell.tsx`
- Create: `frontend/src/components/layout/Header.tsx`

- [ ] **Step 1: Write AppShell** — skip-nav link, ConnectionBanner, Header, main content (max-w 1280px centered), Footer.

- [ ] **Step 2: Write Header** — sticky, logo (click → navigate('/')), nav links (Status, About), HealthIndicator.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(ui): add AppShell and Header layout"
```

---

### Task 23: Footer

**Files:**
- Rewrite: `frontend/src/components/layout/Footer.tsx`

- [ ] **Step 1: Write** — About, Status, Security, Contact links. Copyright year.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): add Footer"
```

---

### Task 24: PageLayout

**Files:**
- Create: `frontend/src/components/layout/PageLayout.tsx`

- [ ] **Step 1: Write** — narrow max-width wrapper for static pages. Title, optional subtitle.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): add PageLayout for static pages"
```

---

## Phase 2, Stream F: Landing Page (Tasks 25-27)

### Task 25: UploadZone + UploadProgress

**Files:**
- Create: `frontend/src/components/landing/UploadZone.tsx`
- Create: `frontend/src/components/landing/UploadProgress.tsx`
- Test: `frontend/src/__tests__/landing/UploadZone.test.tsx`

- [ ] **Step 1: Write UploadZone test**

```typescript
// frontend/src/__tests__/landing/UploadZone.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { UploadZone } from '../../components/landing/UploadZone'

describe('UploadZone', () => {
  it('renders drop zone text', () => {
    render(<UploadZone onUpload={() => {}} />)
    expect(screen.getByText(/drop your file/i)).toBeDefined()
  })

  it('shows supported formats', () => {
    render(<UploadZone onUpload={() => {}} />)
    expect(screen.getByText(/mp4.*mkv.*wav.*mp3/i)).toBeDefined()
  })

  it('shows size limit', () => {
    render(<UploadZone onUpload={() => {}} />)
    expect(screen.getByText(/2gb/i)).toBeDefined()
  })
})
```

- [ ] **Step 2: Write UploadZone**

Uses `react-dropzone`. Accepts media + subtitle files. On drop:
1. Call `detectUploadType(files)` from `types.ts`
2. Client-side validation (extension, size <= 2GB, size >= 1KB)
3. If `transcribe` → call `onUpload(file, 'transcribe')`
4. If `combine` → call `onUpload(files, 'combine')`
5. If `edit-srt` → call `onUpload(file, 'edit-srt')`
6. If `unknown` → show error toast

Drag state: dashed border pulses blue (animation from index.css).

- [ ] **Step 3: Write UploadProgress** — replaces upload zone during XHR. Shows filename + progress bar + percentage.

- [ ] **Step 4: Run tests, commit**

```bash
git commit -m "feat(ui): add UploadZone with adaptive file detection and UploadProgress"
```

---

### Task 26: ProjectCard + ProjectGrid

**Files:**
- Create: `frontend/src/components/landing/ProjectCard.tsx`
- Create: `frontend/src/components/landing/ProjectGrid.tsx`

- [ ] **Step 1: Write ProjectCard** — filename, duration (formatDuration), status badge, relative time. Click → `navigate('/editor/' + taskId)`. Hover lift animation.

- [ ] **Step 2: Write ProjectGrid** — header "Recent Projects" + "Clear" button. Grid of ProjectCards (responsive: 1-4 columns). Empty state if no projects.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(ui): add ProjectCard and ProjectGrid for recent projects"
```

---

### Task 27: LandingPage

**Files:**
- Create: `frontend/src/pages/LandingPage.tsx`

- [ ] **Step 1: Write LandingPage**

```typescript
// frontend/src/pages/LandingPage.tsx
import { AppShell } from '../components/layout/AppShell'
import { UploadZone } from '../components/landing/UploadZone'
import { UploadProgress } from '../components/landing/UploadProgress'
import { ProjectGrid } from '../components/landing/ProjectGrid'
import { Card } from '../components/ui/Card'
import { useEditorStore } from '../store/editorStore'
import { useRecentProjectsStore } from '../store/recentProjectsStore'
import { useToastStore } from '../store/toastStore'
import { navigate } from '../Router'
import { api } from '../api/client'
import { useState } from 'react'
import type { FileMetadata } from '../types'

export function LandingPage() {
  const [uploading, setUploading] = useState(false)
  const [uploadPercent, setUploadPercent] = useState(0)
  const [uploadFilename, setUploadFilename] = useState('')
  const reset = useEditorStore(s => s.reset)
  const addProject = useRecentProjectsStore(s => s.addProject)
  const addToast = useToastStore(s => s.addToast)

  const handleUpload = async (files: File[], type: string) => {
    reset()

    if (type === 'edit-srt') {
      // Client-side SRT editing — navigate to editor with local file
      navigate('/editor/local')
      return
    }

    const file = files[0]
    setUploading(true)
    setUploadFilename(file.name)
    setUploadPercent(0)

    try {
      // Check for duplicates
      const dupes = await api.duplicates(file.name, file.size)
      if (dupes.duplicates_found) {
        // TODO: show duplicate dialog
      }

      // Upload
      const fd = new FormData()
      if (type === 'combine') {
        const videoFile = files.find(f => !f.name.match(/\.(srt|vtt)$/i))!
        const subFile = files.find(f => f.name.match(/\.(srt|vtt)$/i))!
        fd.append('video', videoFile)
        fd.append('subtitle', subFile)
      } else {
        fd.append('file', file)
      }

      // uploadWithProgress uses XHR for progress tracking (already exists in codebase)
      const endpoint = type === 'combine' ? '/combine' : '/upload'
      const result = await api.uploadWithProgress(fd, setUploadPercent, endpoint)

      addProject({
        taskId: result.task_id,
        filename: file.name,
        createdAt: new Date().toISOString(),
        status: 'processing',
        duration: null,
      })

      navigate(`/editor/${result.task_id}`)
    } catch (err: any) {
      addToast({ type: 'error', title: 'Upload failed', description: err.message })
      setUploading(false)
    }
  }

  return (
    <AppShell>
      <Card shadow padding="lg" className="mb-8">
        {uploading ? (
          <UploadProgress filename={uploadFilename} percent={uploadPercent} />
        ) : (
          <UploadZone onUpload={handleUpload} />
        )}
      </Card>
      <ProjectGrid />
    </AppShell>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): add LandingPage with upload zone and project grid"
```

---

## Phase 2, Stream G: Editor Page (Tasks 28-35)

### Task 28: ProgressView + PipelineSteps + LivePreview

**Files:**
- Create: `frontend/src/components/editor/ProgressView.tsx`
- Create: `frontend/src/components/editor/PipelineSteps.tsx`
- Create: `frontend/src/components/editor/LivePreview.tsx`

- [ ] **Step 1: Write PipelineSteps** — list of steps with checkmark/spinner/circle. Reads step from `editorStore.progress.pipelineStep`.

- [ ] **Step 2: Write LivePreview** — auto-scrolling segment list from `editorStore.liveSegments`. Shows timecodes + text. `aria-live="polite"`.

- [ ] **Step 3: Write ProgressView** — composes: filename + model info, ProgressBar, segment count + ETA + speed, PipelineSteps, LivePreview, Pause/Cancel buttons.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(ui): add ProgressView with PipelineSteps and LivePreview"
```

---

### Task 29: SegmentRow

**Files:**
- Create: `frontend/src/components/editor/SegmentRow.tsx`
- Test: `frontend/src/__tests__/editor/SegmentRow.test.tsx`

- [ ] **Step 1: Write SegmentRow test**

```typescript
// frontend/src/__tests__/editor/SegmentRow.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SegmentRow } from '../../components/editor/SegmentRow'

describe('SegmentRow', () => {
  const segment = { index: 0, start: 1.5, end: 4.8, text: 'Hello world' }

  it('renders timecodes and text', () => {
    render(<SegmentRow segment={segment} onEdit={() => {}} />)
    expect(screen.getByText('00:00:01')).toBeDefined()
    expect(screen.getByText('Hello world')).toBeDefined()
  })

  it('enters edit mode on click', () => {
    render(<SegmentRow segment={segment} onEdit={() => {}} editing={true} />)
    const input = screen.getByRole('textbox')
    expect(input).toBeDefined()
  })

  it('calls onEdit with new text on blur', () => {
    const fn = vi.fn()
    render(<SegmentRow segment={segment} onEdit={fn} editing={true} />)
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'New text' } })
    fireEvent.blur(input)
    expect(fn).toHaveBeenCalledWith(0, 'New text')
  })

  it('shows speaker label', () => {
    const seg = { ...segment, speaker: 'Speaker 1' }
    render(<SegmentRow segment={seg} onEdit={() => {}} />)
    expect(screen.getByText('Speaker 1')).toBeDefined()
  })
})
```

- [ ] **Step 2: Write SegmentRow** — index, formatted timecodes, speaker label (if present), text (click to edit). Editing mode: textarea that auto-saves on blur. Highlighted if in search results.

- [ ] **Step 3: Run tests, commit**

```bash
git commit -m "feat(ui): add SegmentRow with inline editing"
```

---

### Task 30: SegmentList

**Files:**
- Create: `frontend/src/components/editor/SegmentList.tsx`
- Test: `frontend/src/__tests__/editor/SegmentList.test.tsx`

- [ ] **Step 1: Write SegmentList** — scrollable container of SegmentRows. Reads `editorStore.segments`. On edit: calls `api.updateSubtitle()` then `editorStore.updateSegment()`. Manages `editingSegmentIndex`.

- [ ] **Step 2: Test: renders segments, edit propagates. Commit.**

```bash
git commit -m "feat(ui): add SegmentList with API-backed inline editing"
```

---

### Task 31: SearchBar

**Files:**
- Create: `frontend/src/components/editor/SearchBar.tsx`
- Test: `frontend/src/__tests__/editor/SearchBar.test.tsx`

- [ ] **Step 1: Write SearchBar** — Input with search icon. Debounced (300ms) call to `api.search()`. Updates `editorStore.searchResults`. Shows match count. Pressing Enter scrolls to first match.

- [ ] **Step 2: Test: renders, calls search on input. Commit.**

```bash
git commit -m "feat(ui): add SearchBar with debounced full-text search"
```

---

### Task 32: EditorToolbar + DownloadMenu

**Files:**
- Create: `frontend/src/components/editor/EditorToolbar.tsx`
- Create: `frontend/src/components/editor/DownloadMenu.tsx`

- [ ] **Step 1: Write DownloadMenu** — dropdown with SRT, VTT, JSON, ZIP options. Each links to `api.downloadUrl()`. Custom line length input (20-120).

- [ ] **Step 2: Write EditorToolbar** — horizontal bar: DownloadMenu, Translate button, Embed button (if video), Re-transcribe button, SearchBar. Right side: filename + duration.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(ui): add EditorToolbar with DownloadMenu and action buttons"
```

---

### Task 33: ContextPanel + SmartSuggestion

**Files:**
- Create: `frontend/src/components/editor/ContextPanel.tsx`
- Create: `frontend/src/components/editor/SmartSuggestion.tsx`

- [ ] **Step 1: Write SmartSuggestion** — blue-tinted card (`primary-light` bg). Title + action button + dismiss X. Reads `uiStore.dismissedSuggestions`.

- [ ] **Step 2: Write ContextPanel** — right sidebar (360px desktop, bottom sheet mobile). Adaptive content based on `uiStore.contextPanelContent`:
  - `info`: FileInfo card + stats + SmartSuggestions
  - `translate`: TranslatePanel
  - `embed`: EmbedPanel
  - `search`: Search results with context

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(ui): add ContextPanel with SmartSuggestion"
```

---

### Task 34: TranslatePanel + EmbedPanel + RetranscribeDialog

**Files:**
- Create: `frontend/src/components/editor/TranslatePanel.tsx`
- Create: `frontend/src/components/editor/EmbedPanel.tsx`
- Create: `frontend/src/components/editor/RetranscribeDialog.tsx`

- [ ] **Step 1: Write TranslatePanel** — all state component-local (per spec Section 7). Source language (read-only), target language dropdown (fetched from `api.translationLanguages()`), engine selector (Whisper vs Argos radio cards), "Begin Translation" button, progress bar. If `POST /translate/:id` doesn't exist yet, show fallback message with re-transcribe option.

- [ ] **Step 2: Write EmbedPanel** — mode selector (soft/hard radio cards), style presets (from `api.embedPresets()`), custom style options (shown for hard burn only), "Embed" button with ConfirmDialog, progress bar, download button on completion.

- [ ] **Step 3: Write RetranscribeDialog** — Dialog with: model selector, language override, diarization toggle. "Re-transcribe" button → `api.retranscribe()` → `navigate('/editor/' + newTaskId)`.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(ui): add TranslatePanel, EmbedPanel, RetranscribeDialog"
```

---

### Task 35: EditorPage + CombineView

**Files:**
- Create: `frontend/src/pages/EditorPage.tsx`
- Create: `frontend/src/components/editor/CombineView.tsx`

- [ ] **Step 1: Write CombineView** — simplified view for video+SRT combine. Progress bar during embed, download button after completion. No segment editor.

- [ ] **Step 2: Write EditorPage** — the core page.

```typescript
// frontend/src/pages/EditorPage.tsx
import { useEffect } from 'react'
import { AppShell } from '../components/layout/AppShell'
import { ProgressView } from '../components/editor/ProgressView'
import { EditorToolbar } from '../components/editor/EditorToolbar'
import { SegmentList } from '../components/editor/SegmentList'
import { ContextPanel } from '../components/editor/ContextPanel'
import { CombineView } from '../components/editor/CombineView'
import { Spinner } from '../components/ui/Spinner'
import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'
import { useEditorStore } from '../store/editorStore'
import { useSSE } from '../hooks/useSSE'
import { api } from '../api/client'
import { navigate } from '../Router'

export function EditorPage({ taskId }: { taskId: string }) {
  const phase = useEditorStore(s => s.phase)
  const storedTaskId = useEditorStore(s => s.taskId)
  const setTaskId = useEditorStore(s => s.setTaskId)
  const setComplete = useEditorStore(s => s.setComplete)
  const setError = useEditorStore(s => s.setError)
  const setPhase = useEditorStore(s => s.setPhase)

  // Session restore
  useEffect(() => {
    if (taskId === 'local') return // SRT-only edit mode
    if (storedTaskId === taskId && phase !== 'idle') return // already loaded

    setTaskId(taskId)
    setPhase('processing')

    api.progress(taskId).then(data => {
      if (data.status === 'done') {
        // Fetch full subtitles for editor
        api.subtitles(taskId).then(subs => {
          setComplete({
            segments: subs.segments || [],
            language: data.language || null,
            modelUsed: data.model || null,
            timings: data.step_timings || {},
            isVideo: data.is_video ?? false,
          })
        })
      } else if (data.status === 'error' || data.status === 'cancelled') {
        setError(data.error || data.message || 'Task failed')
      }
      // else: processing — SSE will handle updates
    }).catch(() => {
      setError('Project not found or deleted')
    })
  }, [taskId])

  // Connect SSE for in-progress tasks
  useSSE(taskId === 'local' ? null : taskId)

  // Loading state
  if (phase === 'idle' && taskId !== 'local') {
    return <AppShell><div className="flex justify-center py-20"><Spinner size="lg" /></div></AppShell>
  }

  // Error state
  if (phase === 'error') {
    return (
      <AppShell>
        <Alert type="error" title="Something went wrong" action={
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => navigate('/')}>Back to Home</Button>
            <Button variant="primary" onClick={() => { setPhase('processing'); /* retry logic */ }}>Retry</Button>
          </div>
        }>
          <p>Check your connection or try a different file.</p>
        </Alert>
      </AppShell>
    )
  }

  // Progress state
  if (phase === 'uploading' || phase === 'processing') {
    return <AppShell><ProgressView taskId={taskId} /></AppShell>
  }

  // Editing state
  return (
    <AppShell>
      <EditorToolbar />
      <div className="flex gap-6 flex-col lg:flex-row mt-4">
        <div className="flex-1 min-w-0">
          <SegmentList />
        </div>
        <div className="w-full lg:w-[360px] shrink-0">
          <ContextPanel />
        </div>
      </div>
    </AppShell>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(ui): add EditorPage with session restore, progress, editing, and error states"
```

---

## Phase 2, Stream H: System (Tasks 36-37)

### Task 36: HealthIndicator + ConnectionBanner

**Files:**
- Create: `frontend/src/components/system/HealthIndicator.tsx`
- Create: `frontend/src/components/system/ConnectionBanner.tsx`

- [ ] **Step 1: Write HealthIndicator** — colored dot (green/amber/red). Tooltip on hover showing CPU/RAM/disk. Reads `uiStore.systemHealth`.

- [ ] **Step 2: Write ConnectionBanner** — full-width banner above header. Shows when: SSE disconnected (yellow), system critical (red), model loading (blue). Reads `uiStore`.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(ui): add HealthIndicator and ConnectionBanner"
```

---

### Task 37: ErrorBoundary

**Files:**
- Create: `frontend/src/components/system/ErrorBoundary.tsx`

- [ ] **Step 1: Write** — React class component error boundary. Fallback: "Something went wrong" card with "Reload" button.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): add ErrorBoundary with styled fallback"
```

---

## Phase 3: Integration (Tasks 38-40)

### Task 38: Wire Landing → Editor Flow

**Files:**
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Update main.tsx**

```typescript
// frontend/src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { Router } from './Router'
import { ErrorBoundary } from './components/system/ErrorBoundary'
import { ToastContainer } from './components/ui/ToastContainer'
import { TooltipProvider } from './components/ui/Tooltip'

async function bootstrap() {
  if (import.meta.env.DEV && import.meta.env.VITE_MOCK === 'true') {
    const { worker } = await import('./mocks/browser')
    await worker.start({ onUnhandledRequest: 'bypass' })
  }
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <ErrorBoundary>
        <TooltipProvider>
          <Router />
          <ToastContainer />
        </TooltipProvider>
      </ErrorBoundary>
    </StrictMode>,
  )
}
bootstrap()
```

- [ ] **Step 2: Smoke test** — `cd frontend && npm run dev` → verify landing page renders, drop zone visible, header/footer present.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(ui): wire main.tsx entry point with all providers"
```

---

### Task 39: Static Pages

**Files:**
- Create: `frontend/src/pages/StatusPage.tsx`
- Create: `frontend/src/pages/AboutPage.tsx`
- Create: `frontend/src/pages/SecurityPage.tsx`
- Create: `frontend/src/pages/ContactPage.tsx`

- [ ] **Step 1: Write all 4 pages** using `AppShell` + `PageLayout` + new design tokens. Port content from existing pages, apply new styling.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): add static pages (Status, About, Security, Contact)"
```

---

### Task 40: Session Restore + Edge Cases

**Files:**
- Modify: `frontend/src/pages/EditorPage.tsx` (if needed)
- Modify: `frontend/src/pages/LandingPage.tsx` (if needed)

- [ ] **Step 1: Implement recent projects lazy validation**

On LandingPage mount: stagger `GET /progress/:id` calls (100ms apart, max 3 concurrent). Update card status. Remove 404s. Timeout 5s → keep cached.

- [ ] **Step 2: Implement edge cases**

- Task deleted (404) → redirect to `/` with toast
- Partial failure → show editor with available segments + error alert
- Duplicate detection dialog before upload

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(ui): add session restore, lazy validation, edge case handling"
```

---

## Phase 4: Testing + Deploy (Tasks 41-43)

### Task 41: Integration Tests

**Files:**
- Create: `frontend/src/__tests__/integration/upload-flow.test.tsx`
- Create: `frontend/src/__tests__/integration/session-restore.test.tsx`

- [ ] **Step 1: Write upload flow test** — render LandingPage, simulate file drop, verify navigation to editor, mock SSE events, verify progress updates, verify transition to editing state.

- [ ] **Step 2: Write session restore test** — navigate to `/editor/:id` directly, mock progress API, verify correct phase restoration.

- [ ] **Step 3: Run, commit**

```bash
git commit -m "test(ui): add integration tests for upload flow and session restore"
```

---

### Task 42: Accessibility + Responsive Tests

**Files:**
- Create: `frontend/src/__tests__/accessibility.test.tsx`
- Create: `frontend/src/__tests__/responsive.test.tsx`

- [ ] **Step 1: Write accessibility tests** — focus management in dialogs, ARIA attributes on progress bar, keyboard navigation in segment list, skip nav link.

- [ ] **Step 2: Write responsive tests** — verify layout changes at breakpoints.

- [ ] **Step 3: Run, commit**

```bash
git commit -m "test(ui): add accessibility and responsive tests"
```

---

### Task 43: Build + Deploy to newui

- [ ] **Step 1: Run full test suite**

Run: `cd frontend && npx vitest run`
Expected: All tests PASS

- [ ] **Step 2: Lint**

Run: `cd frontend && npx eslint src/ --max-warnings 0 && npx tsc -b --noEmit`
Expected: No errors

- [ ] **Step 3: Build**

Run: `cd frontend && npx vite build`
Expected: `frontend/dist/` created with index.html + assets

- [ ] **Step 4: Deploy to newui**

Run: `sudo docker compose --profile newui up -d --build --force-recreate`
Expected: Container rebuilds

- [ ] **Step 5: Verify**

Run: `curl -s http://127.0.0.1:8001/health | python3 -m json.tool`
Expected: `{"status": "ok", ...}`

- [ ] **Step 6: Commit if any final fixes**

```bash
git commit -m "chore: build verification for Drop See Refine deployment"
```

---

## Cleanup (After Investor Approval)

- [ ] Delete old frontend component files no longer imported
- [ ] Delete old store files (taskStore.ts if fully replaced)
- [ ] Update documentation to reflect new design
- [ ] Deploy to production: `sudo docker compose --profile cpu up -d --build --force-recreate`

---

## Summary

| Phase | Tasks | Parallel Streams | Steps |
|-------|-------|------------------|-------|
| Phase 0: Foundation | 1-3 | Sequential | ~15 |
| Phase 1: Primitives + Stores + API + Hooks | 4-20 | 4 streams | ~70 |
| Phase 2: Pages + Features | 21-37 | 4 streams | ~55 |
| Phase 3: Integration | 38-40 | Sequential | ~15 |
| Phase 4: Testing + Deploy | 41-43 | Sequential | ~15 |
| **Total** | **43 tasks** | **Up to 4 parallel** | **~170 steps** |
