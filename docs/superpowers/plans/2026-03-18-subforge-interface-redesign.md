# SubForge Interface Redesign — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Full frontend rebuild with "Guided Confidence" design philosophy, workspace model, and split Zustand stores — deployed to `newui.openlabs.club`.

**Architecture:** Replace all existing frontend components with a new component library built from scratch. New design tokens (blue accent, gray foundation, light-only), workspace-based navigation (step bar: Upload → Transcribe → Translate → Embed → Export), 9 isolated Zustand stores for parallel development, and parameterized client-side routing.

**Tech Stack:** React 19, TypeScript 5.9, Vite 6, Tailwind CSS v4 (CSS-in-CSS), Zustand 5, Radix UI, Lucide React, react-dropzone, class-variance-authority, clsx + tailwind-merge, Vitest + Playwright.

**Spec:** `docs/superpowers/specs/2026-03-18-subforge-interface-redesign-design.md`

---

## Parallel Execution Map

```
Phase 0: Foundation (sequential — everything depends on this)
  Task 1: Shared types
  Task 2: Design tokens (index.css)
  Task 3: cn utility upgrade
  Task 3b: Toast store (needed by UI primitives in Phase 1)
  Task 3c: Backend prerequisite check (verify /download/{task_id}/all exists, plan /translate/{task_id})

Phase 1: Independent streams (ALL PARALLEL)
  Stream A — UI Primitives:    Tasks 4-13 (depends on Task 3b for ToastContainer)
  Stream B — Stores:           Tasks 14-22 (Task 14/toastStore already done in Phase 0)
  Stream C — API Client:       Task 23
  Stream D — Hooks:            Tasks 24-27

Phase 2: Layout + Features (ALL PARALLEL, depends on Phase 1)
  Stream E — Layout Shell:     Tasks 28-32
  Stream F — Step Components:  Tasks 33-39
  Stream G — System:           Tasks 40-42

Phase 3: Integration + Pages (depends on Phase 2)
  Task 43: Wire workspace flow
  Task 44: Static pages
  Task 45: Preferences panel

Phase 4: Testing + Deploy (depends on Phase 3)
  Task 46: Integration tests
  Task 47: Accessibility tests
  Task 48: Responsive tests
  Task 49: Build + deploy to newui
```

---

## File Structure

### New files to create

```
frontend/src/
├── types.ts                          # Shared types (StepName, Segment, FileMetadata, etc.)
├── index.css                         # REWRITE: New design tokens
├── Router.tsx                        # REWRITE: Parameterized routing
├── main.tsx                          # MODIFY: Minor updates
│
├── components/
│   ├── ui/                           # UI Primitives (all new)
│   │   ├── Button.tsx
│   │   ├── IconButton.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   ├── Select.tsx
│   │   ├── Textarea.tsx
│   │   ├── Checkbox.tsx
│   │   ├── Toggle.tsx
│   │   ├── Badge.tsx
│   │   ├── Tag.tsx
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
│   │   ├── StepIndicator.tsx
│   │   ├── Divider.tsx
│   │   └── cn.ts
│   │
│   ├── layout/                       # Layout shell (all new)
│   │   ├── AppShell.tsx
│   │   ├── Header.tsx
│   │   ├── Workspace.tsx
│   │   ├── StepBar.tsx
│   │   ├── MainPanel.tsx
│   │   ├── ContextPanel.tsx
│   │   ├── ProjectDrawer.tsx
│   │   ├── Footer.tsx
│   │   └── PageLayout.tsx
│   │
│   ├── upload/                       # Step 1 (new domain)
│   │   ├── UploadZone.tsx
│   │   ├── ProjectCard.tsx
│   │   └── FileInfo.tsx
│   │
│   ├── transcribe/                   # Step 2 (new)
│   │   ├── ModelSelector.tsx
│   │   ├── LanguageSelect.tsx
│   │   ├── TranscribeOptions.tsx
│   │   ├── TranscribeProgress.tsx
│   │   └── TranscribeForm.tsx
│   │
│   ├── translate/                    # Step 3 (new domain)
│   │   └── TranslatePanel.tsx
│   │
│   ├── embed/                        # Step 4 (new)
│   │   ├── EmbedPanel.tsx
│   │   ├── ModeSelector.tsx
│   │   └── StyleOptions.tsx
│   │
│   ├── export/                       # Step 5 (new domain)
│   │   ├── ExportPanel.tsx
│   │   ├── DownloadButtons.tsx
│   │   ├── SubtitlePreview.tsx
│   │   └── TimingBreakdown.tsx
│   │
│   ├── system/                       # System components (new)
│   │   ├── HealthIndicator.tsx
│   │   ├── ConnectionBanner.tsx
│   │   └── ErrorBoundary.tsx
│   │
│   └── settings/                     # Settings (new)
│       └── PreferencesPanel.tsx
│
├── store/                            # 8 Zustand stores (all new)
│   ├── workspaceStore.ts
│   ├── uiStore.ts
│   ├── transcribeStore.ts
│   ├── translateStore.ts
│   ├── embedStore.ts
│   ├── exportStore.ts
│   ├── preferencesStore.ts
│   ├── toastStore.ts
│   └── recentProjectsStore.ts
│
├── hooks/                            # Hooks (rewrite)
│   ├── useSSE.ts
│   ├── useHealthStream.ts
│   ├── useFocusTrap.ts
│   └── useTaskQueue.ts
│
├── pages/                            # Pages (all new)
│   ├── HomePage.tsx
│   ├── WorkspacePage.tsx
│   ├── StatusPage.tsx
│   ├── AboutPage.tsx
│   ├── SecurityPage.tsx
│   └── ContactPage.tsx
│
├── api/                              # API client (modify)
│   ├── client.ts
│   └── types.ts
│
└── __tests__/                        # Tests (all new)
    ├── ui/
    │   ├── Button.test.tsx
    │   ├── Card.test.tsx
    │   ├── Input.test.tsx
    │   ├── Dialog.test.tsx
    │   ├── ProgressBar.test.tsx
    │   ├── StepIndicator.test.tsx
    │   └── Toast.test.tsx
    ├── store/
    │   ├── workspaceStore.test.ts
    │   ├── uiStore.test.ts
    │   ├── transcribeStore.test.ts
    │   ├── translateStore.test.ts
    │   ├── embedStore.test.ts
    │   ├── exportStore.test.ts
    │   ├── preferencesStore.test.ts
    │   ├── toastStore.test.ts
    │   └── recentProjectsStore.test.ts
    ├── hooks/
    │   ├── useSSE.test.ts
    │   └── useHealthStream.test.ts
    ├── integration/
    │   ├── workspace-flow.test.tsx
    │   └── session-restore.test.tsx
    ├── accessibility.test.tsx
    └── responsive.test.tsx
```

### Files to delete (after rebuild complete)

All existing `frontend/src/components/`, `frontend/src/store/`, `frontend/src/hooks/`, `frontend/src/pages/` files will be replaced. The old `App.tsx` (root), `Router.tsx`, and `index.css` are rewritten in place.

---

## Phase 0: Foundation

### Task 1: Shared Types

**Files:**
- Create: `frontend/src/types.ts`
- Test: `frontend/src/__tests__/types.test.ts`

- [ ] **Step 1: Write the shared types file**

```typescript
// frontend/src/types.ts

export type StepName = 'upload' | 'transcribe' | 'translate' | 'embed' | 'export'
export type StepStatus = 'pending' | 'active' | 'completed' | 'failed' | 'skipped' | 'hidden'

export interface FileMetadata {
  filename: string
  duration: number          // seconds
  format: string            // "H.264/AAC"
  resolution: string | null // "1920x1080" or null for audio
  size: number              // bytes
  codec: string
  isVideo: boolean
}

export interface Segment {
  index: number
  start: number             // seconds (float)
  end: number               // seconds (float)
  text: string
  speaker?: string
}

export interface TranslatedSegment {
  index: number
  start: number
  end: number
  text: string
}

export interface TimingEntry {
  step: string
  duration: number          // seconds
}

export interface DownloadUrls {
  srt: string | null
  vtt: string | null
  json: string | null
  video: string | null
  all: string | null
}

export interface TranscribeOptions {
  model: string
  language: string
  diarization: boolean
  wordTimestamps: boolean
  translateToEnglish: boolean
  translateTo: string | null
}

export interface TranscribeProgress {
  percentage: number
  segmentCount: number
  totalSegments: number
  eta: number | null
  currentPipelineStep: string
  elapsed: number
  speed: number | null
}

export interface TranslateProgress {
  percentage: number
  batchesCompleted: number
  totalBatches: number
}

export interface CustomEmbedStyle {
  fontSize: number
  color: string
  position: string
  backgroundOpacity: number
}

export interface RecentProject {
  taskId: string
  filename: string
  createdAt: string         // ISO date
  status: 'processing' | 'completed' | 'failed'
  duration: number | null
  lastStep: StepName
}

// Utility: format seconds to timecode "HH:MM:SS"
export function formatTimecode(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return [h, m, s].map(v => String(v).padStart(2, '0')).join(':')
}

// Utility: format bytes to human-readable "245 MB"
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

// Utility: format duration "12:34" or "1:02:34"
export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}
```

- [ ] **Step 2: Write tests for utility functions**

```typescript
// frontend/src/__tests__/types.test.ts
import { describe, it, expect } from 'vitest'
import { formatTimecode, formatFileSize, formatDuration } from '../types'

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
```

- [ ] **Step 3: Run tests**

Run: `cd frontend && npx vitest run src/__tests__/types.test.ts`
Expected: 9 tests PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types.ts frontend/src/__tests__/types.test.ts
git commit -m "feat(ui): add shared types and utility functions for redesign"
```

---

### Task 2: Design Tokens

**Files:**
- Rewrite: `frontend/src/index.css`

This replaces the entire Lumen design system with the new "Guided Confidence" tokens.

- [ ] **Step 1: Rewrite index.css with new design tokens**

```css
/* frontend/src/index.css */
@import 'tailwindcss';

/* ── Design Tokens: SubForge Professional ── */
@theme {
  /* Spacing: 4px base grid */
  --spacing: 0.25rem;

  /* Typography */
  --font-family-sans:    'Inter', system-ui, -apple-system, sans-serif;
  --font-family-display: 'Inter', system-ui, -apple-system, sans-serif;
  --font-family-mono:    'JetBrains Mono', 'Fira Code', ui-monospace, monospace;

  /* Foundation & Surfaces */
  --color-bg:             #F3F4F6;
  --color-surface:        #FFFFFF;
  --color-surface-raised: #FFFFFF;
  --color-border:         #E5E7EB;
  --color-border-strong:  #D1D5DB;

  /* Text */
  --color-text:           #111827;
  --color-text-secondary: #4B5563;
  --color-text-muted:     #6B7280;
  --color-text-placeholder: #9CA3AF;

  /* Brand — Blue (enterprise trust) */
  --color-primary:        #2563EB;
  --color-primary-hover:  #1D4ED8;
  --color-primary-light:  rgba(37, 99, 235, 0.08);
  --color-primary-border: rgba(37, 99, 235, 0.20);

  /* Status */
  --color-success:        #059669;
  --color-success-light:  rgba(5, 150, 105, 0.08);
  --color-success-border: rgba(5, 150, 105, 0.20);

  --color-warning:        #D97706;
  --color-warning-light:  rgba(217, 119, 6, 0.08);
  --color-warning-border: rgba(217, 119, 6, 0.20);

  --color-danger:         #DC2626;
  --color-danger-light:   rgba(220, 38, 38, 0.08);
  --color-danger-border:  rgba(220, 38, 38, 0.20);

  /* Info (used for smart suggestions) */
  --color-info:           #2563EB;
  --color-info-light:     rgba(37, 99, 235, 0.06);

  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius:    8px;
  --radius-lg: 12px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.05);
  --shadow-md: 0 2px 4px rgb(0 0 0 / 0.06), 0 1px 2px rgb(0 0 0 / 0.04);
  --shadow-lg: 0 8px 16px rgb(0 0 0 / 0.08), 0 2px 4px rgb(0 0 0 / 0.04);
  --shadow-xl: 0 16px 32px rgb(0 0 0 / 0.10), 0 4px 8px rgb(0 0 0 / 0.05);
}

/* ── Base Styles ── */
html {
  font-family: var(--font-family-sans);
  color: var(--color-text);
  background: var(--color-bg);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  min-height: 100vh;
}

/* ── Focus Management ── */
*:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* ── Accessibility ── */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* Skip navigation */
.skip-nav {
  position: absolute;
  top: -100%;
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-primary);
  color: white;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  z-index: 100;
  font-weight: 600;
  text-decoration: none;
}
.skip-nav:focus {
  top: 8px;
}

/* ── Animations ── */
@keyframes step-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes slide-in-bottom {
  from { transform: translateY(8px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes success-bounce {
  0% { transform: scale(0); }
  60% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

@keyframes card-hover-lift {
  to { transform: translateY(-1px); }
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fade-out {
  from { opacity: 1; }
  to { opacity: 0; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes toast-slide-in {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

@keyframes gentle-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

@keyframes dropzone-pulse {
  0%, 100% { border-color: var(--color-primary-border); }
  50% { border-color: var(--color-primary); }
}

/* ── Reduced Motion ── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--color-border-strong);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: var(--color-text-muted); }
```

- [ ] **Step 2: Verify the build compiles with new tokens**

Run: `cd frontend && npx vite build 2>&1 | tail -5`
Expected: Build succeeds (may have warnings about unused classes, that's fine)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "feat(ui): replace Lumen design tokens with Guided Confidence system"
```

---

### Task 3: Upgrade cn Utility

**Files:**
- Rewrite: `frontend/src/components/ui/cn.ts`

The current `cn()` is a simple filter-join. Upgrade it to use `clsx` + `tailwind-merge` (both already in package.json).

- [ ] **Step 1: Rewrite cn.ts**

```typescript
// frontend/src/components/ui/cn.ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ui/cn.ts
git commit -m "refactor(ui): upgrade cn utility to use clsx + tailwind-merge"
```

---

### Task 3b: Toast Store (Phase 0 — needed by ToastContainer in Phase 1)

Moved from Stream B to Phase 0 because `ToastContainer` (Task 10, Stream A) imports `useToastStore`. Must exist before parallel streams begin. See Task 14 for full implementation — execute Task 14 here in Phase 0.

---

### Task 3c: Backend Prerequisites Check

- [ ] **Step 1: Verify `/download/{task_id}/all` endpoint exists**

Run: `grep -r "download.*all" app/routes/ --include="*.py" -l`
Check if the endpoint is implemented. If not, it must be added before Task 39 (ExportPanel).

- [ ] **Step 2: Plan `POST /translate/{task_id}` backend endpoint**

This is a **Required** new endpoint per the spec (Section 15). The frontend TranslatePanel (Task 37) will call it. Options:
- Implement now as a new route in `app/routes/`
- Or defer Task 37 to only support pre-transcription translation (bundled with `/upload`)

**Note:** Backend implementation of `POST /translate/{task_id}` is out of scope for this frontend plan. File as a separate task/issue for the backend team (Forge/Bolt). TranslatePanel (Task 37) should gracefully handle this endpoint not existing yet by disabling post-hoc translation and only offering pre-transcription translation at Step 2.

- [ ] **Step 3: Commit if any changes**

---

## Phase 1, Stream A: UI Primitives

### Task 4: Button + IconButton

**Files:**
- Rewrite: `frontend/src/components/ui/Button.tsx`
- Create: `frontend/src/components/ui/IconButton.tsx`
- Test: `frontend/src/__tests__/ui/Button.test.tsx`

- [ ] **Step 1: Write Button tests**

```typescript
// frontend/src/__tests__/ui/Button.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../../components/ui/Button'

describe('Button', () => {
  it('renders children', () => {
    render(<Button variant="primary" size="md">Click me</Button>)
    expect(screen.getByRole('button', { name: 'Click me' })).toBeDefined()
  })

  it('calls onClick', () => {
    const fn = vi.fn()
    render(<Button variant="primary" size="md" onClick={fn}>Go</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(fn).toHaveBeenCalledOnce()
  })

  it('shows spinner when loading', () => {
    render(<Button variant="primary" size="md" loading>Go</Button>)
    const btn = screen.getByRole('button')
    expect(btn.getAttribute('disabled')).toBe('')
    expect(btn.querySelector('[data-testid="spinner"]')).toBeTruthy()
  })

  it('is disabled when disabled prop set', () => {
    render(<Button variant="primary" size="md" disabled>Go</Button>)
    expect(screen.getByRole('button').getAttribute('disabled')).toBe('')
  })

  it('applies variant classes', () => {
    const { container } = render(<Button variant="danger" size="sm">Del</Button>)
    const btn = container.querySelector('button')
    expect(btn?.className).toContain('danger')
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/__tests__/ui/Button.test.tsx`
Expected: FAIL (Button component doesn't match new API yet)

- [ ] **Step 3: Write Button component**

```typescript
// frontend/src/components/ui/Button.tsx
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from './cn'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 font-medium transition-colors duration-150 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]',
  {
    variants: {
      variant: {
        primary: 'bg-[var(--color-primary)] text-white border border-[var(--color-primary)] shadow-sm hover:bg-[var(--color-primary-hover)] active:bg-[var(--color-primary-hover)]',
        secondary: 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border border-[var(--color-border)] hover:bg-[var(--color-bg)] active:bg-[var(--color-bg)]',
        ghost: 'bg-transparent text-[var(--color-text-secondary)] border border-transparent hover:bg-[var(--color-bg)] active:bg-[var(--color-bg)]',
        danger: 'bg-[var(--color-danger)] text-white border border-[var(--color-danger)] hover:bg-red-700 active:bg-red-800',
        success: 'bg-[var(--color-success)] text-white border border-[var(--color-success)] hover:bg-emerald-700 active:bg-emerald-800',
      },
      size: {
        sm: 'h-8 px-3 text-sm rounded-[var(--radius-md)]',
        md: 'h-9 px-4 text-sm rounded-[var(--radius-md)]',
        lg: 'h-10 px-5 text-base rounded-[var(--radius)]',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean
  icon?: ReactNode
  iconRight?: ReactNode
  fullWidth?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, disabled, icon, iconRight, fullWidth, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size }), fullWidth && 'w-full', className)}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <svg data-testid="spinner" className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : icon ? icon : null}
        {children}
        {iconRight && !loading ? iconRight : null}
      </button>
    )
  }
)
Button.displayName = 'Button'
```

- [ ] **Step 4: Write IconButton component**

```typescript
// frontend/src/components/ui/IconButton.tsx
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from './cn'

const iconButtonVariants = cva(
  'inline-flex items-center justify-center rounded-[var(--radius-md)] transition-colors duration-150 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]',
  {
    variants: {
      variant: {
        primary: 'bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)]',
        secondary: 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border border-[var(--color-border)] hover:bg-[var(--color-bg)]',
        ghost: 'bg-transparent text-[var(--color-text-muted)] hover:bg-[var(--color-bg)] hover:text-[var(--color-text)]',
      },
      size: {
        sm: 'h-7 w-7',
        md: 'h-8 w-8',
        lg: 'h-9 w-9',
      },
    },
    defaultVariants: { variant: 'ghost', size: 'md' },
  }
)

export interface IconButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof iconButtonVariants> {
  icon: ReactNode
  label: string
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, variant, size, icon, label, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(iconButtonVariants({ variant, size }), className)}
        aria-label={label}
        title={label}
        {...props}
      >
        {icon}
      </button>
    )
  }
)
IconButton.displayName = 'IconButton'
```

- [ ] **Step 5: Run tests**

Run: `cd frontend && npx vitest run src/__tests__/ui/Button.test.tsx`
Expected: 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ui/Button.tsx frontend/src/components/ui/IconButton.tsx frontend/src/__tests__/ui/Button.test.tsx
git commit -m "feat(ui): add Button and IconButton components"
```

---

### Task 5: Card

**Files:**
- Rewrite: `frontend/src/components/ui/Card.tsx`
- Test: `frontend/src/__tests__/ui/Card.test.tsx`

- [ ] **Step 1: Write Card tests**

```typescript
// frontend/src/__tests__/ui/Card.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Card } from '../../components/ui/Card'

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Content</Card>)
    expect(screen.getByText('Content')).toBeDefined()
  })

  it('renders header with title and subtitle', () => {
    render(<Card header={{ title: 'Title', subtitle: 'Sub' }}>Body</Card>)
    expect(screen.getByText('Title')).toBeDefined()
    expect(screen.getByText('Sub')).toBeDefined()
  })

  it('applies shadow by default', () => {
    const { container } = render(<Card>Content</Card>)
    expect(container.firstChild?.className).toContain('shadow')
  })

  it('applies border when border prop set', () => {
    const { container } = render(<Card border>Content</Card>)
    expect(container.firstChild?.className).toContain('border')
  })
})
```

- [ ] **Step 2: Write Card component**

```typescript
// frontend/src/components/ui/Card.tsx
import { type ReactNode } from 'react'
import { cn } from './cn'

interface CardHeader {
  title: string
  subtitle?: string
  action?: ReactNode
}

export interface CardProps {
  children: ReactNode
  padding?: 'sm' | 'md' | 'lg'
  shadow?: boolean
  border?: boolean
  header?: CardHeader
  className?: string
}

const paddingMap = { sm: 'p-3', md: 'p-4', lg: 'p-6' }

export function Card({ children, padding = 'md', shadow = true, border = false, header, className }: CardProps) {
  return (
    <div
      className={cn(
        'bg-[var(--color-surface)] rounded-[var(--radius)]',
        shadow && 'shadow-[var(--shadow-md)]',
        border && 'border border-[var(--color-border)]',
        paddingMap[padding],
        className
      )}
    >
      {header && (
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-[var(--color-text)]">{header.title}</h3>
            {header.subtitle && (
              <p className="text-sm text-[var(--color-text-muted)] mt-0.5">{header.subtitle}</p>
            )}
          </div>
          {header.action}
        </div>
      )}
      {children}
    </div>
  )
}
```

- [ ] **Step 3: Run tests**

Run: `cd frontend && npx vitest run src/__tests__/ui/Card.test.tsx`
Expected: 4 tests PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ui/Card.tsx frontend/src/__tests__/ui/Card.test.tsx
git commit -m "feat(ui): add Card component with header, padding, shadow, border variants"
```

---

### Task 6: Input + Select + Textarea

**Files:**
- Rewrite: `frontend/src/components/ui/Input.tsx`
- Rewrite: `frontend/src/components/ui/Select.tsx`
- Create: `frontend/src/components/ui/Textarea.tsx`
- Test: `frontend/src/__tests__/ui/Input.test.tsx`

- [ ] **Step 1: Write Input tests**

```typescript
// frontend/src/__tests__/ui/Input.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Input } from '../../components/ui/Input'

describe('Input', () => {
  it('renders with label', () => {
    render(<Input label="Email" value="" onChange={() => {}} />)
    expect(screen.getByLabelText('Email')).toBeDefined()
  })

  it('shows error message', () => {
    render(<Input label="Email" value="" onChange={() => {}} error="Required" />)
    expect(screen.getByText('Required')).toBeDefined()
  })

  it('calls onChange', () => {
    const fn = vi.fn()
    render(<Input label="Name" value="" onChange={fn} />)
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'hi' } })
    expect(fn).toHaveBeenCalledWith('hi')
  })

  it('shows helper text', () => {
    render(<Input label="Name" value="" onChange={() => {}} helperText="Enter your name" />)
    expect(screen.getByText('Enter your name')).toBeDefined()
  })
})
```

- [ ] **Step 2: Write Input component**

```typescript
// frontend/src/components/ui/Input.tsx
import { type ReactNode, useId } from 'react'
import { cn } from './cn'

export interface InputProps {
  type?: 'text' | 'password' | 'search'
  size?: 'sm' | 'md'
  label?: string
  placeholder?: string
  error?: string
  helperText?: string
  disabled?: boolean
  icon?: ReactNode
  value: string
  onChange: (value: string) => void
  className?: string
}

const sizeMap = { sm: 'h-8 text-sm px-2.5', md: 'h-9 text-sm px-3' }

export function Input({
  type = 'text', size = 'md', label, placeholder, error, helperText,
  disabled, icon, value, onChange, className,
}: InputProps) {
  const id = useId()
  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      {label && (
        <label htmlFor={id} className="text-sm font-medium text-[var(--color-text)]">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]">
            {icon}
          </div>
        )}
        <input
          id={id}
          type={type}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            'w-full rounded-[var(--radius-md)] border bg-[var(--color-surface)] text-[var(--color-text)] placeholder:text-[var(--color-text-placeholder)] transition-colors duration-150',
            'focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-1 focus:border-[var(--color-primary)]',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            error ? 'border-[var(--color-danger)]' : 'border-[var(--color-border)]',
            icon ? 'pl-9' : '',
            sizeMap[size],
          )}
        />
      </div>
      {error && <p className="text-xs text-[var(--color-danger)]">{error}</p>}
      {helperText && !error && <p className="text-xs text-[var(--color-text-muted)]">{helperText}</p>}
    </div>
  )
}
```

- [ ] **Step 3: Write Select component**

```typescript
// frontend/src/components/ui/Select.tsx
import { useId } from 'react'
import { cn } from './cn'

export interface SelectOption {
  value: string
  label: string
  group?: string
}

export interface SelectProps {
  size?: 'sm' | 'md'
  label?: string
  placeholder?: string
  error?: string
  disabled?: boolean
  options: SelectOption[]
  value: string
  onChange: (value: string) => void
  className?: string
}

const sizeMap = { sm: 'h-8 text-sm px-2.5', md: 'h-9 text-sm px-3' }

export function Select({
  size = 'md', label, placeholder, error, disabled, options, value, onChange, className,
}: SelectProps) {
  const id = useId()

  // Group options
  const groups = new Map<string | undefined, SelectOption[]>()
  for (const opt of options) {
    const key = opt.group
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(opt)
  }

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      {label && (
        <label htmlFor={id} className="text-sm font-medium text-[var(--color-text)]">
          {label}
        </label>
      )}
      <select
        id={id}
        value={value}
        onChange={e => onChange(e.target.value)}
        disabled={disabled}
        className={cn(
          'w-full rounded-[var(--radius-md)] border bg-[var(--color-surface)] text-[var(--color-text)] appearance-none cursor-pointer transition-colors duration-150',
          'focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-1 focus:border-[var(--color-primary)]',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          error ? 'border-[var(--color-danger)]' : 'border-[var(--color-border)]',
          sizeMap[size],
        )}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {[...groups.entries()].map(([group, opts]) =>
          group ? (
            <optgroup key={group} label={group}>
              {opts.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </optgroup>
          ) : (
            opts.map(o => <option key={o.value} value={o.value}>{o.label}</option>)
          )
        )}
      </select>
      {error && <p className="text-xs text-[var(--color-danger)]">{error}</p>}
    </div>
  )
}
```

- [ ] **Step 4: Write Textarea component**

```typescript
// frontend/src/components/ui/Textarea.tsx
import { useId } from 'react'
import { cn } from './cn'

export interface TextareaProps {
  size?: 'sm' | 'md'
  label?: string
  placeholder?: string
  error?: string
  disabled?: boolean
  rows?: number
  value: string
  onChange: (value: string) => void
  className?: string
}

export function Textarea({
  size = 'md', label, placeholder, error, disabled, rows = 4, value, onChange, className,
}: TextareaProps) {
  const id = useId()
  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      {label && (
        <label htmlFor={id} className="text-sm font-medium text-[var(--color-text)]">{label}</label>
      )}
      <textarea
        id={id}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        rows={rows}
        className={cn(
          'w-full rounded-[var(--radius-md)] border bg-[var(--color-surface)] text-[var(--color-text)] placeholder:text-[var(--color-text-placeholder)] transition-colors duration-150 resize-y',
          'focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-1',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          error ? 'border-[var(--color-danger)]' : 'border-[var(--color-border)]',
          size === 'sm' ? 'text-sm p-2' : 'text-sm p-3',
        )}
      />
      {error && <p className="text-xs text-[var(--color-danger)]">{error}</p>}
    </div>
  )
}
```

- [ ] **Step 5: Run tests**

Run: `cd frontend && npx vitest run src/__tests__/ui/Input.test.tsx`
Expected: 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ui/Input.tsx frontend/src/components/ui/Select.tsx frontend/src/components/ui/Textarea.tsx frontend/src/__tests__/ui/Input.test.tsx
git commit -m "feat(ui): add Input, Select, Textarea form components"
```

---

### Task 7: Dialog + ConfirmDialog

**Files:**
- Rewrite: `frontend/src/components/ui/Dialog.tsx`
- Create: `frontend/src/components/ui/ConfirmDialog.tsx`
- Test: `frontend/src/__tests__/ui/Dialog.test.tsx`

- [ ] **Step 1: Write Dialog tests**

```typescript
// frontend/src/__tests__/ui/Dialog.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Dialog } from '../../components/ui/Dialog'
import { ConfirmDialog } from '../../components/ui/ConfirmDialog'

describe('Dialog', () => {
  it('renders when open', () => {
    render(<Dialog open onClose={() => {}} title="Test">Body</Dialog>)
    expect(screen.getByRole('dialog')).toBeDefined()
    expect(screen.getByText('Test')).toBeDefined()
    expect(screen.getByText('Body')).toBeDefined()
  })

  it('does not render when closed', () => {
    render(<Dialog open={false} onClose={() => {}} title="Test">Body</Dialog>)
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('calls onClose on Escape', () => {
    const fn = vi.fn()
    render(<Dialog open onClose={fn} title="Test">Body</Dialog>)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(fn).toHaveBeenCalled()
  })
})

describe('ConfirmDialog', () => {
  it('calls onConfirm when confirm button clicked', () => {
    const fn = vi.fn()
    render(<ConfirmDialog open onClose={() => {}} onConfirm={fn} title="Delete?" message="Sure?" />)
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }))
    expect(fn).toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: Write Dialog component**

```typescript
// frontend/src/components/ui/Dialog.tsx
import { useEffect, useRef, useId, type ReactNode } from 'react'
import { cn } from './cn'

export interface DialogProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  children: ReactNode
  actions?: ReactNode
  size?: 'sm' | 'md' | 'lg'
}

const sizeMap = { sm: 'max-w-[400px]', md: 'max-w-[500px]', lg: 'max-w-[640px]' }

export function Dialog({ open, onClose, title, description, children, actions, size = 'md' }: DialogProps) {
  const titleId = useId()
  const overlayRef = useRef<HTMLDivElement>(null)
  const dialogRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const handle = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handle)
    return () => document.removeEventListener('keydown', handle)
  }, [open, onClose])

  // Focus trap
  useEffect(() => {
    if (!open || !dialogRef.current) return
    const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    if (focusable.length > 0) focusable[0].focus()
  }, [open])

  if (!open) return null

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 animate-[fade-in_150ms_ease]"
      onClick={e => { if (e.target === overlayRef.current) onClose() }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={cn(
          'w-full bg-[var(--color-surface)] rounded-[var(--radius-lg)] shadow-[var(--shadow-xl)] p-6 animate-[fade-in_150ms_ease]',
          sizeMap[size],
        )}
      >
        <h2 id={titleId} className="text-lg font-semibold text-[var(--color-text)]">{title}</h2>
        {description && <p className="mt-1 text-sm text-[var(--color-text-muted)]">{description}</p>}
        <div className="mt-4">{children}</div>
        {actions && <div className="mt-6 flex justify-end gap-3">{actions}</div>}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Write ConfirmDialog component**

```typescript
// frontend/src/components/ui/ConfirmDialog.tsx
import { Dialog } from './Dialog'
import { Button } from './Button'

export interface ConfirmDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'default' | 'danger'
  loading?: boolean
}

export function ConfirmDialog({
  open, onClose, onConfirm, title, message,
  confirmLabel = 'Confirm', cancelLabel = 'Cancel',
  variant = 'default', loading = false,
}: ConfirmDialogProps) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={title}
      actions={
        <>
          <Button variant="secondary" size="md" onClick={onClose} disabled={loading}>
            {cancelLabel}
          </Button>
          <Button
            variant={variant === 'danger' ? 'danger' : 'primary'}
            size="md"
            onClick={onConfirm}
            loading={loading}
          >
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p className="text-sm text-[var(--color-text-secondary)]">{message}</p>
    </Dialog>
  )
}
```

- [ ] **Step 4: Run tests**

Run: `cd frontend && npx vitest run src/__tests__/ui/Dialog.test.tsx`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/Dialog.tsx frontend/src/components/ui/ConfirmDialog.tsx frontend/src/__tests__/ui/Dialog.test.tsx
git commit -m "feat(ui): add Dialog and ConfirmDialog with focus trap and Escape handling"
```

---

### Task 8: Badge + Tag + Checkbox + Toggle + Divider

**Files:**
- Rewrite: `frontend/src/components/ui/Badge.tsx`
- Create: `frontend/src/components/ui/Tag.tsx`
- Create: `frontend/src/components/ui/Checkbox.tsx`
- Create: `frontend/src/components/ui/Toggle.tsx`
- Rewrite: `frontend/src/components/ui/Divider.tsx`

- [ ] **Step 1: Write all five small components**

Badge:
```typescript
// frontend/src/components/ui/Badge.tsx
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from './cn'

const badgeVariants = cva(
  'inline-flex items-center font-medium rounded-full',
  {
    variants: {
      variant: {
        default: 'bg-[var(--color-bg)] text-[var(--color-text-secondary)] border border-[var(--color-border)]',
        success: 'bg-[var(--color-success-light)] text-[var(--color-success)] border border-[var(--color-success-border)]',
        warning: 'bg-[var(--color-warning-light)] text-[var(--color-warning)] border border-[var(--color-warning-border)]',
        danger: 'bg-[var(--color-danger-light)] text-[var(--color-danger)] border border-[var(--color-danger-border)]',
        info: 'bg-[var(--color-primary-light)] text-[var(--color-primary)] border border-[var(--color-primary-border)]',
      },
      size: {
        sm: 'px-2 py-0.5 text-[10px]',
        md: 'px-2.5 py-0.5 text-xs',
      },
    },
    defaultVariants: { variant: 'default', size: 'md' },
  }
)

export interface BadgeProps extends VariantProps<typeof badgeVariants> {
  children: React.ReactNode
  dot?: boolean
  className?: string
}

export function Badge({ children, variant, size, dot, className }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant, size }), className)}>
      {dot && <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5" />}
      {children}
    </span>
  )
}
```

Tag:
```typescript
// frontend/src/components/ui/Tag.tsx
import { X } from 'lucide-react'
import { cn } from './cn'

export interface TagProps {
  children: React.ReactNode
  onRemove?: () => void
  className?: string
}

export function Tag({ children, onRemove, className }: TagProps) {
  return (
    <span className={cn(
      'inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-[var(--radius-sm)] bg-[var(--color-bg)] text-[var(--color-text-secondary)] border border-[var(--color-border)]',
      className
    )}>
      {children}
      {onRemove && (
        <button onClick={onRemove} className="hover:text-[var(--color-text)] ml-0.5" aria-label="Remove">
          <X size={12} />
        </button>
      )}
    </span>
  )
}
```

Checkbox:
```typescript
// frontend/src/components/ui/Checkbox.tsx
import { useId } from 'react'
import { cn } from './cn'

export interface CheckboxProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label?: string
  disabled?: boolean
  indeterminate?: boolean
  className?: string
}

export function Checkbox({ checked, onChange, label, disabled, className }: CheckboxProps) {
  const id = useId()
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={e => onChange(e.target.checked)}
        disabled={disabled}
        className="h-4 w-4 rounded border-[var(--color-border)] text-[var(--color-primary)] focus:ring-[var(--color-primary)] focus:ring-offset-1 disabled:opacity-50 cursor-pointer"
      />
      {label && (
        <label htmlFor={id} className={cn('text-sm text-[var(--color-text)]', disabled && 'opacity-50 cursor-not-allowed')}>
          {label}
        </label>
      )}
    </div>
  )
}
```

Toggle:
```typescript
// frontend/src/components/ui/Toggle.tsx
import { cn } from './cn'

export interface ToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
  size?: 'sm' | 'md'
  disabled?: boolean
  label?: string
}

const sizeMap = {
  sm: { track: 'w-8 h-4', thumb: 'h-3 w-3', translate: 'translate-x-4' },
  md: { track: 'w-10 h-5', thumb: 'h-4 w-4', translate: 'translate-x-5' },
}

export function Toggle({ checked, onChange, size = 'md', disabled, label }: ToggleProps) {
  const s = sizeMap[size]
  return (
    <button
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => !disabled && onChange(!checked)}
      disabled={disabled}
      className={cn(
        'relative inline-flex items-center rounded-full transition-colors duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
        s.track,
        checked ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-border-strong)]',
      )}
    >
      <span className={cn(
        'inline-block rounded-full bg-white shadow-sm transition-transform duration-200',
        s.thumb,
        checked ? s.translate : 'translate-x-0.5',
      )} />
    </button>
  )
}
```

Divider:
```typescript
// frontend/src/components/ui/Divider.tsx
import { cn } from './cn'

export interface DividerProps {
  className?: string
  label?: string
}

export function Divider({ className, label }: DividerProps) {
  if (label) {
    return (
      <div className={cn('flex items-center gap-3', className)}>
        <div className="flex-1 h-px bg-[var(--color-border)]" />
        <span className="text-xs text-[var(--color-text-muted)] font-medium">{label}</span>
        <div className="flex-1 h-px bg-[var(--color-border)]" />
      </div>
    )
  }
  return <div className={cn('h-px bg-[var(--color-border)]', className)} />
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ui/Badge.tsx frontend/src/components/ui/Tag.tsx frontend/src/components/ui/Checkbox.tsx frontend/src/components/ui/Toggle.tsx frontend/src/components/ui/Divider.tsx
git commit -m "feat(ui): add Badge, Tag, Checkbox, Toggle, Divider components"
```

---

### Task 9: ProgressBar + Spinner + Skeleton

**Files:**
- Create: `frontend/src/components/ui/ProgressBar.tsx`
- Create: `frontend/src/components/ui/Spinner.tsx`
- Rewrite: `frontend/src/components/ui/Skeleton.tsx`
- Test: `frontend/src/__tests__/ui/ProgressBar.test.tsx`

- [ ] **Step 1: Write ProgressBar test**

```typescript
// frontend/src/__tests__/ui/ProgressBar.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProgressBar } from '../../components/ui/ProgressBar'

describe('ProgressBar', () => {
  it('renders with correct aria attributes', () => {
    render(<ProgressBar value={67} />)
    const bar = screen.getByRole('progressbar')
    expect(bar.getAttribute('aria-valuenow')).toBe('67')
    expect(bar.getAttribute('aria-valuemin')).toBe('0')
    expect(bar.getAttribute('aria-valuemax')).toBe('100')
  })

  it('shows percentage when showPercentage is true', () => {
    render(<ProgressBar value={42} showPercentage />)
    expect(screen.getByText('42%')).toBeDefined()
  })

  it('renders indeterminate state', () => {
    const { container } = render(<ProgressBar value={0} indeterminate />)
    expect(container.querySelector('[data-indeterminate]')).toBeTruthy()
  })
})
```

- [ ] **Step 2: Write ProgressBar component**

```typescript
// frontend/src/components/ui/ProgressBar.tsx
import { cn } from './cn'

export interface ProgressBarProps {
  value: number
  indeterminate?: boolean
  label?: string
  showPercentage?: boolean
  size?: 'sm' | 'md'
  className?: string
}

export function ProgressBar({ value, indeterminate, label, showPercentage, size = 'md', className }: ProgressBarProps) {
  const height = size === 'sm' ? 'h-1' : 'h-2'
  return (
    <div className={cn('w-full', className)}>
      {(label || showPercentage) && (
        <div className="flex justify-between mb-1.5">
          {label && <span className="text-sm text-[var(--color-text-secondary)]">{label}</span>}
          {showPercentage && <span className="text-sm font-medium text-[var(--color-text)]">{Math.round(value)}%</span>}
        </div>
      )}
      <div
        role="progressbar"
        aria-valuenow={indeterminate ? undefined : Math.round(value)}
        aria-valuemin={0}
        aria-valuemax={100}
        className={cn('w-full rounded-full bg-[var(--color-bg)] overflow-hidden', height)}
      >
        {indeterminate ? (
          <div
            data-indeterminate
            className={cn('h-full w-1/3 rounded-full bg-[var(--color-primary)]', height)}
            style={{ animation: 'shimmer 1.5s ease-in-out infinite', backgroundSize: '200% 100%' }}
          />
        ) : (
          <div
            className={cn('h-full rounded-full bg-[var(--color-primary)] transition-[width] duration-300 ease-out', height)}
            style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
          />
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Write Spinner component**

```typescript
// frontend/src/components/ui/Spinner.tsx
import { cn } from './cn'

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeMap = { sm: 'h-4 w-4', md: 'h-5 w-5', lg: 'h-8 w-8' }

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <svg
      className={cn('animate-spin text-[var(--color-primary)]', sizeMap[size], className)}
      viewBox="0 0 24 24"
      fill="none"
      aria-label="Loading"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}
```

- [ ] **Step 4: Write Skeleton component**

```typescript
// frontend/src/components/ui/Skeleton.tsx
import { cn } from './cn'

export interface SkeletonProps {
  className?: string
  width?: string
  height?: string
}

export function Skeleton({ className, width, height }: SkeletonProps) {
  return (
    <div
      className={cn('rounded-[var(--radius-md)] bg-[var(--color-border)] animate-pulse', className)}
      style={{ width, height }}
    />
  )
}
```

- [ ] **Step 5: Run tests**

Run: `cd frontend && npx vitest run src/__tests__/ui/ProgressBar.test.tsx`
Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ui/ProgressBar.tsx frontend/src/components/ui/Spinner.tsx frontend/src/components/ui/Skeleton.tsx frontend/src/__tests__/ui/ProgressBar.test.tsx
git commit -m "feat(ui): add ProgressBar, Spinner, Skeleton feedback components"
```

---

### Task 10: Toast + ToastContainer + Alert

**Files:**
- Create: `frontend/src/components/ui/Toast.tsx`
- Rewrite: `frontend/src/components/ui/ToastContainer.tsx`
- Create: `frontend/src/components/ui/Alert.tsx`
- Test: `frontend/src/__tests__/ui/Toast.test.tsx`

- [ ] **Step 1: Write Toast test**

```typescript
// frontend/src/__tests__/ui/Toast.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Toast } from '../../components/ui/Toast'

describe('Toast', () => {
  it('renders title and description', () => {
    render(<Toast type="success" title="Done" description="All good" onDismiss={() => {}} />)
    expect(screen.getByText('Done')).toBeDefined()
    expect(screen.getByText('All good')).toBeDefined()
  })

  it('calls onDismiss when close clicked', () => {
    const fn = vi.fn()
    render(<Toast type="error" title="Error" onDismiss={fn} />)
    fireEvent.click(screen.getByLabelText('Dismiss'))
    expect(fn).toHaveBeenCalled()
  })

  it('renders action button', () => {
    const fn = vi.fn()
    render(<Toast type="info" title="Info" action={{ label: 'Retry', onClick: fn }} onDismiss={() => {}} />)
    fireEvent.click(screen.getByText('Retry'))
    expect(fn).toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: Write Toast, ToastContainer, and Alert components**

Toast:
```typescript
// frontend/src/components/ui/Toast.tsx
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { cn } from './cn'

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
}

const styles = {
  success: 'border-[var(--color-success-border)] bg-[var(--color-success-light)]',
  error: 'border-[var(--color-danger-border)] bg-[var(--color-danger-light)]',
  warning: 'border-[var(--color-warning-border)] bg-[var(--color-warning-light)]',
  info: 'border-[var(--color-primary-border)] bg-[var(--color-primary-light)]',
}

const iconColors = {
  success: 'text-[var(--color-success)]',
  error: 'text-[var(--color-danger)]',
  warning: 'text-[var(--color-warning)]',
  info: 'text-[var(--color-primary)]',
}

export interface ToastProps {
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  description?: string
  action?: { label: string; onClick: () => void }
  onDismiss: () => void
}

export function Toast({ type, title, description, action, onDismiss }: ToastProps) {
  const Icon = icons[type]
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        'flex items-start gap-3 p-4 rounded-[var(--radius)] border shadow-[var(--shadow-lg)] animate-[toast-slide-in_200ms_ease]',
        styles[type],
      )}
    >
      <Icon size={18} className={cn('mt-0.5 shrink-0', iconColors[type])} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-[var(--color-text)]">{title}</p>
        {description && <p className="text-sm text-[var(--color-text-secondary)] mt-0.5">{description}</p>}
        {action && (
          <button
            onClick={action.onClick}
            className="text-sm font-medium text-[var(--color-primary)] hover:underline mt-1"
          >
            {action.label}
          </button>
        )}
      </div>
      <button onClick={onDismiss} aria-label="Dismiss" className="text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
        <X size={16} />
      </button>
    </div>
  )
}
```

ToastContainer:
```typescript
// frontend/src/components/ui/ToastContainer.tsx
import { useToastStore } from '../../store/toastStore'
import { Toast } from './Toast'

export function ToastContainer() {
  const { toasts, removeToast } = useToastStore()
  if (toasts.length === 0) return null
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 w-80">
      {toasts.map(t => (
        <Toast
          key={t.id}
          type={t.type}
          title={t.title}
          description={t.description}
          action={t.action}
          onDismiss={() => removeToast(t.id)}
        />
      ))}
    </div>
  )
}
```

Alert:
```typescript
// frontend/src/components/ui/Alert.tsx
import { CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { cn } from './cn'
import type { ReactNode } from 'react'

const icons = { success: CheckCircle, error: AlertCircle, warning: AlertTriangle, info: Info }
const styles = {
  success: 'border-[var(--color-success-border)] bg-[var(--color-success-light)]',
  error: 'border-[var(--color-danger-border)] bg-[var(--color-danger-light)]',
  warning: 'border-[var(--color-warning-border)] bg-[var(--color-warning-light)]',
  info: 'border-[var(--color-primary-border)] bg-[var(--color-primary-light)]',
}
const iconColors = {
  success: 'text-[var(--color-success)]',
  error: 'text-[var(--color-danger)]',
  warning: 'text-[var(--color-warning)]',
  info: 'text-[var(--color-primary)]',
}

export interface AlertProps {
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  children?: ReactNode
  action?: ReactNode
  className?: string
}

export function Alert({ type, title, children, action, className }: AlertProps) {
  const Icon = icons[type]
  return (
    <div className={cn('flex gap-3 p-4 rounded-[var(--radius)] border', styles[type], className)}>
      <Icon size={18} className={cn('mt-0.5 shrink-0', iconColors[type])} />
      <div className="flex-1">
        <p className="text-sm font-medium text-[var(--color-text)]">{title}</p>
        {children && <div className="text-sm text-[var(--color-text-secondary)] mt-1">{children}</div>}
        {action && <div className="mt-3">{action}</div>}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Run tests**

Run: `cd frontend && npx vitest run src/__tests__/ui/Toast.test.tsx`
Expected: 3 tests PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ui/Toast.tsx frontend/src/components/ui/ToastContainer.tsx frontend/src/components/ui/Alert.tsx frontend/src/__tests__/ui/Toast.test.tsx
git commit -m "feat(ui): add Toast, ToastContainer, Alert notification components"
```

---

### Task 11: StepIndicator

**Files:**
- Create: `frontend/src/components/ui/StepIndicator.tsx`
- Test: `frontend/src/__tests__/ui/StepIndicator.test.tsx`

- [ ] **Step 1: Write StepIndicator test**

```typescript
// frontend/src/__tests__/ui/StepIndicator.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { StepIndicator } from '../../components/ui/StepIndicator'

const steps = [
  { id: 'upload', label: 'Upload', status: 'completed' as const },
  { id: 'transcribe', label: 'Transcribe', status: 'active' as const },
  { id: 'translate', label: 'Translate', status: 'pending' as const, optional: true },
  { id: 'export', label: 'Export', status: 'pending' as const },
]

describe('StepIndicator', () => {
  it('renders all visible steps', () => {
    render(<StepIndicator steps={steps} onStepClick={() => {}} />)
    expect(screen.getByText('Upload')).toBeDefined()
    expect(screen.getByText('Transcribe')).toBeDefined()
    expect(screen.getByText('Translate')).toBeDefined()
    expect(screen.getByText('Export')).toBeDefined()
  })

  it('hides hidden steps', () => {
    const stepsWithHidden = [...steps, { id: 'embed', label: 'Embed', status: 'hidden' as const }]
    render(<StepIndicator steps={stepsWithHidden} onStepClick={() => {}} />)
    expect(screen.queryByText('Embed')).toBeNull()
  })

  it('allows clicking completed steps', () => {
    const fn = vi.fn()
    render(<StepIndicator steps={steps} onStepClick={fn} />)
    fireEvent.click(screen.getByText('Upload'))
    expect(fn).toHaveBeenCalledWith('upload')
  })

  it('marks active step with aria-current', () => {
    render(<StepIndicator steps={steps} onStepClick={() => {}} />)
    const active = screen.getByText('Transcribe').closest('[aria-current]')
    expect(active?.getAttribute('aria-current')).toBe('step')
  })
})
```

- [ ] **Step 2: Write StepIndicator component**

```typescript
// frontend/src/components/ui/StepIndicator.tsx
import { Check } from 'lucide-react'
import { cn } from './cn'
import type { StepStatus } from '../../types'

interface Step {
  id: string
  label: string
  status: StepStatus
  optional?: boolean
  hidden?: boolean
}

export interface StepIndicatorProps {
  steps: Step[]
  onStepClick: (stepId: string) => void
}

export function StepIndicator({ steps, onStepClick }: StepIndicatorProps) {
  const visibleSteps = steps.filter(s => s.status !== 'hidden' && !s.hidden)

  return (
    <nav role="navigation" aria-label="Pipeline steps" className="flex items-center gap-1 overflow-x-auto">
      {visibleSteps.map((step, i) => {
        const isClickable = step.status === 'completed' || step.status === 'active'
        return (
          <div key={step.id} className="flex items-center">
            {i > 0 && <div className={cn('w-8 h-px mx-1', step.status === 'completed' ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-border)]')} />}
            <button
              aria-current={step.status === 'active' ? 'step' : undefined}
              onClick={() => isClickable && onStepClick(step.id)}
              disabled={!isClickable}
              className={cn(
                'flex items-center gap-2 px-3 py-2 rounded-[var(--radius-md)] text-sm font-medium transition-colors duration-150 whitespace-nowrap',
                step.status === 'completed' && 'text-[var(--color-primary)] hover:bg-[var(--color-primary-light)] cursor-pointer',
                step.status === 'active' && 'text-[var(--color-primary)] bg-[var(--color-primary-light)] cursor-default',
                step.status === 'pending' && 'text-[var(--color-text-muted)] cursor-not-allowed',
                step.status === 'skipped' && 'text-[var(--color-text-muted)] line-through cursor-not-allowed',
              )}
            >
              {/* Step indicator dot/check */}
              {step.status === 'completed' ? (
                <span className="flex items-center justify-center w-5 h-5 rounded-full bg-[var(--color-primary)] text-white">
                  <Check size={12} strokeWidth={3} />
                </span>
              ) : step.status === 'active' ? (
                <span className="flex items-center justify-center w-5 h-5 rounded-full border-2 border-[var(--color-primary)]">
                  <span className="w-2 h-2 rounded-full bg-[var(--color-primary)] animate-[step-pulse_2s_ease-in-out_infinite]" />
                </span>
              ) : (
                <span className="flex items-center justify-center w-5 h-5 rounded-full border-2 border-[var(--color-border)]" />
              )}
              {step.label}
              {step.optional && step.status === 'pending' && (
                <span className="text-xs text-[var(--color-text-placeholder)]">(optional)</span>
              )}
            </button>
          </div>
        )
      })}
    </nav>
  )
}
```

- [ ] **Step 3: Run tests**

Run: `cd frontend && npx vitest run src/__tests__/ui/StepIndicator.test.tsx`
Expected: 4 tests PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ui/StepIndicator.tsx frontend/src/__tests__/ui/StepIndicator.test.tsx
git commit -m "feat(ui): add StepIndicator with completed/active/pending/hidden states"
```

---

### Task 12: EmptyState

**Files:**
- Create: `frontend/src/components/ui/EmptyState.tsx`

- [ ] **Step 1: Write EmptyState component**

```typescript
// frontend/src/components/ui/EmptyState.tsx
import type { ReactNode } from 'react'
import { cn } from './cn'

export interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 px-6 text-center', className)}>
      {icon && (
        <div className="mb-4 text-[var(--color-text-muted)] animate-[gentle-float_3s_ease-in-out_infinite]">
          {icon}
        </div>
      )}
      <h3 className="text-base font-semibold text-[var(--color-text)]">{title}</h3>
      {description && <p className="mt-1 text-sm text-[var(--color-text-muted)] max-w-sm">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ui/EmptyState.tsx
git commit -m "feat(ui): add EmptyState component with animated icon and action slot"
```

---

### Task 13: Tooltip (Radix-based)

**Files:**
- Rewrite: `frontend/src/components/ui/Tooltip.tsx`

- [ ] **Step 1: Write Tooltip component**

```typescript
// frontend/src/components/ui/Tooltip.tsx
import * as RadixTooltip from '@radix-ui/react-tooltip'
import type { ReactNode } from 'react'

export interface TooltipProps {
  children: ReactNode
  content: string
  side?: 'top' | 'bottom' | 'left' | 'right'
  delayDuration?: number
}

export function TooltipProvider({ children }: { children: ReactNode }) {
  return <RadixTooltip.Provider delayDuration={300}>{children}</RadixTooltip.Provider>
}

export function Tooltip({ children, content, side = 'top', delayDuration = 300 }: TooltipProps) {
  return (
    <RadixTooltip.Root delayDuration={delayDuration}>
      <RadixTooltip.Trigger asChild>{children}</RadixTooltip.Trigger>
      <RadixTooltip.Portal>
        <RadixTooltip.Content
          side={side}
          sideOffset={4}
          className="z-50 px-2.5 py-1.5 text-xs font-medium bg-[var(--color-text)] text-white rounded-[var(--radius-sm)] shadow-[var(--shadow-lg)] animate-[fade-in_150ms_ease]"
        >
          {content}
          <RadixTooltip.Arrow className="fill-[var(--color-text)]" />
        </RadixTooltip.Content>
      </RadixTooltip.Portal>
    </RadixTooltip.Root>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ui/Tooltip.tsx
git commit -m "feat(ui): add Tooltip component based on Radix UI"
```

---

## Phase 1, Stream B: Stores

### Task 14: Toast Store

**Files:**
- Rewrite: `frontend/src/store/toastStore.ts`
- Test: `frontend/src/__tests__/store/toastStore.test.ts`

- [ ] **Step 1: Write toastStore test**

```typescript
// frontend/src/__tests__/store/toastStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { useToastStore } from '../../store/toastStore'

describe('toastStore', () => {
  beforeEach(() => useToastStore.setState({ toasts: [] }))

  it('adds a toast', () => {
    useToastStore.getState().addToast({ type: 'success', title: 'Done' })
    expect(useToastStore.getState().toasts).toHaveLength(1)
    expect(useToastStore.getState().toasts[0].title).toBe('Done')
  })

  it('removes a toast', () => {
    useToastStore.getState().addToast({ type: 'info', title: 'Test' })
    const id = useToastStore.getState().toasts[0].id
    useToastStore.getState().removeToast(id)
    expect(useToastStore.getState().toasts).toHaveLength(0)
  })

  it('generates unique ids', () => {
    useToastStore.getState().addToast({ type: 'success', title: 'A' })
    useToastStore.getState().addToast({ type: 'error', title: 'B' })
    const ids = useToastStore.getState().toasts.map(t => t.id)
    expect(ids[0]).not.toBe(ids[1])
  })
})
```

- [ ] **Step 2: Write toastStore**

```typescript
// frontend/src/store/toastStore.ts
import { create } from 'zustand'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  type: ToastType
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

- [ ] **Step 3: Run tests**

Run: `cd frontend && npx vitest run src/__tests__/store/toastStore.test.ts`
Expected: 3 tests PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/store/toastStore.ts frontend/src/__tests__/store/toastStore.test.ts
git commit -m "feat(store): add toastStore with auto-dismiss and action support"
```

---

### Task 15: Preferences Store

**Files:**
- Rewrite: `frontend/src/store/preferencesStore.ts`
- Test: `frontend/src/__tests__/store/preferencesStore.test.ts`

- [ ] **Step 1: Write and test preferencesStore**

Test:
```typescript
// frontend/src/__tests__/store/preferencesStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { usePreferencesStore } from '../../store/preferencesStore'

describe('preferencesStore', () => {
  beforeEach(() => usePreferencesStore.getState().resetDefaults())

  it('has correct defaults', () => {
    const s = usePreferencesStore.getState()
    expect(s.defaultModel).toBe('medium')
    expect(s.defaultLanguage).toBe('auto')
    expect(s.confirmBeforeTranscribe).toBe(true)
  })

  it('updates a preference', () => {
    usePreferencesStore.getState().updatePreference('defaultModel', 'large')
    expect(usePreferencesStore.getState().defaultModel).toBe('large')
  })

  it('resets to defaults', () => {
    usePreferencesStore.getState().updatePreference('defaultModel', 'tiny')
    usePreferencesStore.getState().resetDefaults()
    expect(usePreferencesStore.getState().defaultModel).toBe('medium')
  })
})
```

Store:
```typescript
// frontend/src/store/preferencesStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface PreferencesState {
  defaultModel: string
  defaultLanguage: string
  defaultFormat: string
  autoCopyOnComplete: boolean
  confirmBeforeTranscribe: boolean
  dismissedSuggestions: string[]
  updatePreference: <K extends keyof Omit<PreferencesState, 'updatePreference' | 'resetDefaults'>>(key: K, value: PreferencesState[K]) => void
  resetDefaults: () => void
}

const defaults = {
  defaultModel: 'medium',
  defaultLanguage: 'auto',
  defaultFormat: 'srt',
  autoCopyOnComplete: false,
  confirmBeforeTranscribe: true,
  dismissedSuggestions: [] as string[],
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      ...defaults,
      updatePreference: (key, value) => set({ [key]: value }),
      resetDefaults: () => set(defaults),
    }),
    { name: 'sg-preferences' }
  )
)
```

- [ ] **Step 2: Run tests**

Run: `cd frontend && npx vitest run src/__tests__/store/preferencesStore.test.ts`
Expected: 3 tests PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/store/preferencesStore.ts frontend/src/__tests__/store/preferencesStore.test.ts
git commit -m "feat(store): add preferencesStore with localStorage persistence"
```

---

### Task 16: Workspace Store

**Files:**
- Create: `frontend/src/store/workspaceStore.ts`
- Test: `frontend/src/__tests__/store/workspaceStore.test.ts`

- [ ] **Step 1: Write workspaceStore test**

```typescript
// frontend/src/__tests__/store/workspaceStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { useWorkspaceStore } from '../../store/workspaceStore'

describe('workspaceStore', () => {
  beforeEach(() => useWorkspaceStore.getState().reset())

  it('initializes with null state', () => {
    const s = useWorkspaceStore.getState()
    expect(s.projectId).toBeNull()
    expect(s.currentStep).toBe('upload')
  })

  it('initializes from upload', () => {
    const file = new File(['test'], 'test.mp4', { type: 'video/mp4' })
    const meta = { filename: 'test.mp4', duration: 60, format: 'H.264', resolution: '1080p', size: 1024, codec: 'aac', isVideo: true }
    useWorkspaceStore.getState().initFromUpload(file, meta)
    const s = useWorkspaceStore.getState()
    expect(s.file).toBe(file)
    expect(s.fileMetadata?.filename).toBe('test.mp4')
    expect(s.currentStep).toBe('transcribe')
    expect(s.stepStatuses.upload).toBe('completed')
  })

  it('completes a step', () => {
    useWorkspaceStore.getState().completeStep('transcribe')
    expect(useWorkspaceStore.getState().stepStatuses.transcribe).toBe('completed')
  })

  it('skips a step', () => {
    useWorkspaceStore.getState().skipStep('translate')
    expect(useWorkspaceStore.getState().stepStatuses.translate).toBe('skipped')
  })

  it('hides embed for audio files', () => {
    const file = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
    const meta = { filename: 'test.mp3', duration: 60, format: 'MP3', resolution: null, size: 1024, codec: 'mp3', isVideo: false }
    useWorkspaceStore.getState().initFromUpload(file, meta)
    expect(useWorkspaceStore.getState().stepStatuses.embed).toBe('hidden')
  })

  it('resets to initial state', () => {
    useWorkspaceStore.getState().setProjectId('task-123')
    useWorkspaceStore.getState().reset()
    expect(useWorkspaceStore.getState().projectId).toBeNull()
  })
})
```

- [ ] **Step 2: Write workspaceStore**

```typescript
// frontend/src/store/workspaceStore.ts
import { create } from 'zustand'
import type { StepName, StepStatus, FileMetadata } from '../types'

interface StepStatuses {
  upload: StepStatus
  transcribe: StepStatus
  translate: StepStatus
  embed: StepStatus
  export: StepStatus
}

interface WorkspaceState {
  projectId: string | null
  file: File | null
  fileMetadata: FileMetadata | null
  currentStep: StepName
  stepStatuses: StepStatuses

  initFromUpload: (file: File, metadata: FileMetadata) => void
  setProjectId: (id: string) => void
  setCurrentStep: (step: StepName) => void
  completeStep: (step: StepName) => void
  skipStep: (step: StepName) => void
  failStep: (step: StepName) => void
  reset: () => void
  restoreFromTask: (taskData: { status: string; step?: StepName }) => void
}

const initialStatuses: StepStatuses = {
  upload: 'pending',
  transcribe: 'pending',
  translate: 'pending',
  embed: 'pending',
  export: 'pending',
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  projectId: null,
  file: null,
  fileMetadata: null,
  currentStep: 'upload',
  stepStatuses: { ...initialStatuses },

  initFromUpload: (file, metadata) => set({
    file,
    fileMetadata: metadata,
    currentStep: 'transcribe',
    stepStatuses: {
      upload: 'completed',
      transcribe: 'pending',
      translate: 'pending',
      embed: metadata.isVideo ? 'pending' : 'hidden',
      export: 'pending',
    },
  }),

  setProjectId: (id) => set({ projectId: id }),

  setCurrentStep: (step) => set((s) => ({
    currentStep: step,
    stepStatuses: {
      ...s.stepStatuses,
      [step]: s.stepStatuses[step] === 'completed' ? 'completed' : 'active',
    },
  })),

  completeStep: (step) => set((s) => ({
    stepStatuses: { ...s.stepStatuses, [step]: 'completed' },
  })),

  skipStep: (step) => set((s) => ({
    stepStatuses: { ...s.stepStatuses, [step]: 'skipped' },
  })),

  failStep: (step) => set((s) => ({
    stepStatuses: { ...s.stepStatuses, [step]: 'failed' },
  })),

  reset: () => set({
    projectId: null,
    file: null,
    fileMetadata: null,
    currentStep: 'upload',
    stepStatuses: { ...initialStatuses },
  }),

  restoreFromTask: (taskData) => {
    if (taskData.status === 'completed' || taskData.status === 'done') {
      set({
        currentStep: 'export',
        stepStatuses: {
          upload: 'completed',
          transcribe: 'completed',
          translate: 'skipped',
          embed: 'skipped',
          export: 'active',
        },
      })
    } else if (taskData.status === 'failed' || taskData.status === 'error') {
      set({
        currentStep: 'transcribe',
        stepStatuses: { ...initialStatuses, upload: 'completed', transcribe: 'failed' },
      })
    } else {
      set({
        currentStep: 'transcribe',
        stepStatuses: { ...initialStatuses, upload: 'completed', transcribe: 'active' },
      })
    }
  },
}))
```

- [ ] **Step 3: Run tests**

Run: `cd frontend && npx vitest run src/__tests__/store/workspaceStore.test.ts`
Expected: 6 tests PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/store/workspaceStore.ts frontend/src/__tests__/store/workspaceStore.test.ts
git commit -m "feat(store): add workspaceStore for step navigation and project identity"
```

---

### Task 17: Transcribe Store

**Files:**
- Create: `frontend/src/store/transcribeStore.ts`
- Test: `frontend/src/__tests__/store/transcribeStore.test.ts`

**Required interface (from spec Section 7):**

```typescript
interface TranscribeState {
  options: TranscribeOptions           // model, language, diarization, wordTimestamps, translateToEnglish, translateTo
  progress: TranscribeProgress | null  // percentage, segmentCount, totalSegments, eta, currentPipelineStep, elapsed, speed
  segments: Segment[]                  // live segments from SSE

  setOptions: (options: Partial<TranscribeOptions>) => void
  updateProgress: (progress: Partial<TranscribeProgress>) => void
  addSegment: (segment: Segment) => void
  setSegments: (segments: Segment[]) => void
  reset: () => void
}
```

- [ ] **Step 1: Write tests** — test setOptions, updateProgress, addSegment, setSegments, reset
- [ ] **Step 2: Write store implementation matching interface above**
- [ ] **Step 3: Run tests, commit**

```bash
git commit -m "feat(store): add transcribeStore for Step 2 state"
```

---

### Task 18: Translate Store

**Files:**
- Create: `frontend/src/store/translateStore.ts`
- Test: `frontend/src/__tests__/store/translateStore.test.ts`

**Required interface (from spec Section 7):**

```typescript
interface TranslateState {
  targetLanguage: string | null
  engine: 'whisper' | 'argos' | null
  progress: TranslateProgress | null   // percentage, batchesCompleted, totalBatches
  translatedSegments: TranslatedSegment[]

  setTargetLanguage: (lang: string) => void
  setEngine: (engine: 'whisper' | 'argos') => void
  updateProgress: (progress: Partial<TranslateProgress>) => void
  setTranslatedSegments: (segments: TranslatedSegment[]) => void
  reset: () => void
}
```

- [ ] **Step 1: Write tests** — test setTargetLanguage, setEngine, updateProgress, setTranslatedSegments, reset
- [ ] **Step 2: Write store implementation**
- [ ] **Step 3: Run tests, commit**

```bash
git commit -m "feat(store): add translateStore for Step 3 state"
```

---

### Task 19: Embed Store

**Files:**
- Create: `frontend/src/store/embedStore.ts`
- Test: `frontend/src/__tests__/store/embedStore.test.ts`

**Required interface (from spec Section 7):**

```typescript
interface EmbedState {
  mode: 'soft' | 'hard' | null
  style: string | null
  customStyle: CustomEmbedStyle | null  // fontSize, color, position, backgroundOpacity
  progress: number | null

  setMode: (mode: 'soft' | 'hard') => void
  setStyle: (style: string) => void
  setCustomStyle: (style: Partial<CustomEmbedStyle>) => void
  updateProgress: (progress: number) => void
  reset: () => void
}
```

- [ ] **Step 1: Write tests** — test setMode, setStyle, setCustomStyle, updateProgress, reset
- [ ] **Step 2: Write store implementation**
- [ ] **Step 3: Run tests, commit**

```bash
git commit -m "feat(store): add embedStore for Step 4 state"
```

---

### Task 20: Export Store

**Files:**
- Create: `frontend/src/store/exportStore.ts`
- Test: `frontend/src/__tests__/store/exportStore.test.ts`

**Required interface (from spec Section 7):**

```typescript
interface ExportState {
  downloadUrls: DownloadUrls           // srt, vtt, json, video, all (all nullable strings)
  timingBreakdown: TimingEntry[]       // step + duration pairs
  totalSegments: number
  detectedLanguage: string | null

  setDownloadUrls: (urls: Partial<DownloadUrls>) => void
  setTimingBreakdown: (breakdown: TimingEntry[]) => void
  setTotalSegments: (count: number) => void
  setDetectedLanguage: (lang: string) => void
  reset: () => void
}
```

- [ ] **Step 1: Write tests** — test setDownloadUrls, setTimingBreakdown, totalSegments, detectedLanguage, reset
- [ ] **Step 2: Write store implementation**
- [ ] **Step 3: Run tests, commit**

```bash
git commit -m "feat(store): add exportStore for Step 5 state"
```

---

### Task 21: UI Store

**Files:**
- Rewrite: `frontend/src/store/uiStore.ts`
- Test: `frontend/src/__tests__/store/uiStore.test.ts`

**Required interface (from spec Section 7):**

```typescript
interface UIState {
  currentPage: string                    // '/', '/project/:id', '/status', etc.
  contextPanelOpen: boolean              // mobile: collapsible
  projectDrawerOpen: boolean             // home: collapsible
  sseConnected: boolean
  sseReconnecting: boolean
  lastEventTime: number | null
  systemHealth: 'healthy' | 'degraded' | 'critical'
  modelPreloadStatus: Record<string, 'loaded' | 'loading' | 'unloaded'>

  setCurrentPage: (page: string) => void
  navigate: (path: string) => void
  toggleContextPanel: () => void
  toggleProjectDrawer: () => void
  setSSEConnected: (connected: boolean) => void
  setReconnecting: (reconnecting: boolean) => void
  setLastEventTime: (time: number) => void
  setSystemHealth: (health: 'healthy' | 'degraded' | 'critical') => void
  setModelPreloadStatus: (status: Record<string, 'loaded' | 'loading' | 'unloaded'>) => void
}
```

- [ ] **Step 1: Write tests** — test all setters, toggles, navigate (dispatches spa-navigate event)
- [ ] **Step 2: Write store implementation**
- [ ] **Step 3: Run tests, commit**

```bash
git commit -m "feat(store): rewrite uiStore for new layout architecture"
```

---

### Task 22: Recent Projects Store

**Files:**
- Create: `frontend/src/store/recentProjectsStore.ts`
- Test: `frontend/src/__tests__/store/recentProjectsStore.test.ts`

**Required interface (from spec Section 7):**

```typescript
interface RecentProjectsState {
  projects: RecentProject[]             // taskId, filename, createdAt, status, duration, lastStep

  addProject: (project: RecentProject) => void
  updateProject: (taskId: string, updates: Partial<RecentProject>) => void
  removeProject: (taskId: string) => void
  pruneStale: (validIds: string[]) => void
}
// Persisted to localStorage key 'sg-recent-projects'. Max 20 entries (oldest pruned on add).
```

- [ ] **Step 1: Write tests** — test add (respects max 20), update, remove, pruneStale, localStorage persistence
- [ ] **Step 2: Write store implementation with `persist` middleware**
- [ ] **Step 3: Run tests, commit**

```bash
git commit -m "feat(store): add recentProjectsStore with localStorage persistence"
```

---

## Phase 1, Stream C: API Client

### Task 23: Update API Client + Types

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/types.ts`

- [ ] **Step 1: Add new API methods to client.ts**

Add to the existing `api` object:
```typescript
// Add to frontend/src/api/client.ts

  // New: post-hoc translation
  translate: (taskId: string, targetLanguage: string, engine: 'whisper' | 'argos') =>
    fetch(`/translate/${taskId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_language: targetLanguage, engine }),
    }).then(r => json<{ task_id: string; message: string }>(r)),

  // New: translation languages
  translationLanguages: () =>
    fetch('/translation/languages').then(r => json<TranslationLanguagesResponse>(r)),
```

- [ ] **Step 2: Update types.ts with any missing types**

Ensure `TranslationLanguagesResponse` is defined. Verify `ModelPreloadStatus` matches backend.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(api): add translate endpoint and update types for redesign"
```

---

## Phase 1, Stream D: Hooks

### Task 24: useSSE Hook (Rewrite)

**Files:**
- Rewrite: `frontend/src/hooks/useSSE.ts`
- Test: `frontend/src/__tests__/hooks/useSSE.test.ts`

The hook must dispatch events to the new split stores (transcribeStore, translateStore, embedStore, exportStore, workspaceStore) instead of the old monolithic taskStore.

- [ ] **Step 1: Write useSSE test** (mock EventSource, verify store dispatches for each event type)

- [ ] **Step 2: Rewrite useSSE hook**

Key changes from current implementation:
- Import `useWorkspaceStore`, `useTranscribeStore`, `useTranslateStore`, `useEmbedStore`, `useExportStore`
- `segment` event → `transcribeStore.addSegment()`
- `progress` event → `transcribeStore.updateProgress()`
- `done` event → `workspaceStore.completeStep('transcribe')`, `exportStore.setDownloadUrls()`
- `embed_progress` → `embedStore.updateProgress()`
- `embed_done` → `workspaceStore.completeStep('embed')`
- Exponential backoff: 1s → 2s → 4s → 8s → 16s → max 30s
- Watchdog: 45s no-event → poll `/progress/{taskId}` → decide reconnect or final state

- [ ] **Step 3: Run tests, commit**

```bash
git commit -m "feat(hooks): rewrite useSSE to dispatch to split stores"
```

---

### Task 25: useHealthStream Hook (Rewrite)

**Files:**
- Rewrite: `frontend/src/hooks/useHealthStream.ts`
- Test: `frontend/src/__tests__/hooks/useHealthStream.test.ts`

- [ ] **Step 1: Write and rewrite** — Same SSE pattern but dispatches to `uiStore` (health, sseConnected, modelPreloadStatus). Keep 2.5s grace period.

- [ ] **Step 2: Run tests, commit**

```bash
git commit -m "feat(hooks): rewrite useHealthStream for new uiStore"
```

---

### Task 26: useFocusTrap Hook

**Files:**
- Keep: `frontend/src/hooks/useFocusTrap.ts` (minor updates if needed)

- [ ] **Step 1: Verify existing hook works, update imports if needed**

- [ ] **Step 2: Commit if changed**

---

### Task 27: useTaskQueue Hook

**Files:**
- Rewrite: `frontend/src/hooks/useTaskQueue.ts`

- [ ] **Step 1: Rewrite** — Poll `/tasks?session_only=true` every 2s, update `recentProjectsStore`

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(hooks): rewrite useTaskQueue for recentProjectsStore"
```

---

## Phase 2, Stream E: Layout Shell

### Task 28: Router (Parameterized Routes)

**Files:**
- Rewrite: `frontend/src/Router.tsx`

- [ ] **Step 1: Rewrite Router with parameterized route support**

```typescript
// frontend/src/Router.tsx
import { useState, useEffect, useMemo } from 'react'
import { HomePage } from './pages/HomePage'
import { WorkspacePage } from './pages/WorkspacePage'
import { StatusPage } from './pages/StatusPage'
import { AboutPage } from './pages/AboutPage'
import { SecurityPage } from './pages/SecurityPage'
import { ContactPage } from './pages/ContactPage'
import { useHealthStream } from './hooks/useHealthStream'
import { useUIStore } from './store/uiStore'

function matchRoute(path: string): { page: string; params: Record<string, string> } {
  // /project/:id
  const projectMatch = path.match(/^\/project\/([^/]+)$/)
  if (projectMatch) return { page: 'workspace', params: { id: projectMatch[1] } }

  const staticRoutes: Record<string, string> = {
    '/': 'home',
    '/status': 'status',
    '/about': 'about',
    '/security': 'security',
    '/contact': 'contact',
  }
  return { page: staticRoutes[path] || 'home', params: {} }
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
    const handleNav = () => setPath(window.location.pathname)
    window.addEventListener('popstate', handleNav)
    window.addEventListener('spa-navigate', handleNav)
    return () => {
      window.removeEventListener('popstate', handleNav)
      window.removeEventListener('spa-navigate', handleNav)
    }
  }, [])

  const route = useMemo(() => matchRoute(path), [path])

  useEffect(() => { setCurrentPage(path) }, [path, setCurrentPage])

  switch (route.page) {
    case 'workspace': return <WorkspacePage projectId={route.params.id} />
    case 'status': return <StatusPage />
    case 'about': return <AboutPage />
    case 'security': return <SecurityPage />
    case 'contact': return <ContactPage />
    default: return <HomePage />
  }
}
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): rewrite Router with parameterized route support for /project/:id"
```

---

### Task 29: AppShell + Header

**Files:**
- Create: `frontend/src/components/layout/AppShell.tsx`
- Create: `frontend/src/components/layout/Header.tsx`

- [ ] **Step 1: Write AppShell**

```typescript
// frontend/src/components/layout/AppShell.tsx
import type { ReactNode } from 'react'
import { Header } from './Header'
import { Footer } from './Footer'
import { ConnectionBanner } from '../system/ConnectionBanner'

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-[var(--color-bg)]">
      <a href="#main-content" className="skip-nav">Skip to main content</a>
      <ConnectionBanner />
      <Header />
      <main id="main-content" className="flex-1 w-full max-w-[1280px] mx-auto px-6 py-6 lg:px-8">
        {children}
      </main>
      <Footer />
    </div>
  )
}
```

- [ ] **Step 2: Write Header**

```typescript
// frontend/src/components/layout/Header.tsx
import { Settings } from 'lucide-react'
import { navigate } from '../../Router'
import { useUIStore } from '../../store/uiStore'
import { IconButton } from '../ui/IconButton'
import { HealthIndicator } from '../system/HealthIndicator'

const navItems = [
  { label: 'Home', path: '/' },
  { label: 'Status', path: '/status' },
  { label: 'About', path: '/about' },
]

export function Header() {
  const currentPage = useUIStore(s => s.currentPage)

  return (
    <header className="sticky top-0 z-40 h-14 bg-[var(--color-surface)] border-b border-[var(--color-border)] flex items-center px-6">
      {/* Logo */}
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 font-bold text-lg text-[var(--color-text)] hover:text-[var(--color-primary)] transition-colors"
      >
        SubForge
      </button>

      {/* Nav */}
      <nav className="flex items-center gap-1 ml-8">
        {navItems.map(item => (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            className={`px-3 py-1.5 text-sm font-medium rounded-[var(--radius-md)] transition-colors ${
              currentPage === item.path
                ? 'text-[var(--color-primary)] bg-[var(--color-primary-light)]'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg)]'
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>

      {/* Right actions */}
      <div className="ml-auto flex items-center gap-2">
        <HealthIndicator />
        <IconButton
          icon={<Settings size={18} />}
          label="Preferences"
          onClick={() => {/* open preferences panel */}}
        />
      </div>
    </header>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(ui): add AppShell and Header layout components"
```

---

### Task 30: StepBar + Workspace Layout

**Files:**
- Create: `frontend/src/components/layout/StepBar.tsx`
- Create: `frontend/src/components/layout/Workspace.tsx`
- Create: `frontend/src/components/layout/MainPanel.tsx`
- Create: `frontend/src/components/layout/ContextPanel.tsx`

- [ ] **Step 1: Write StepBar** — Wraps `StepIndicator` with file info bar and home button, reads from `workspaceStore`

- [ ] **Step 2: Write Workspace** — Renders StepBar + MainPanel (flex-1) + ContextPanel (360px). Responsive: single column on mobile.

- [ ] **Step 3: Write MainPanel and ContextPanel** — Simple container wrappers with appropriate padding and styling.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(ui): add Workspace layout with StepBar, MainPanel, ContextPanel"
```

---

### Task 31: ProjectDrawer

**Files:**
- Create: `frontend/src/components/layout/ProjectDrawer.tsx`

- [ ] **Step 1: Write ProjectDrawer** — Reads from `recentProjectsStore`. Renders project cards. Search filter. Bulk delete. Navigate to `/project/:id` on click.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): add ProjectDrawer with recent projects and search"
```

---

### Task 32: Footer + PageLayout

**Files:**
- Rewrite: `frontend/src/components/layout/Footer.tsx`
- Create: `frontend/src/components/layout/PageLayout.tsx`

- [ ] **Step 1: Write Footer** — Links to About, Status, Security. Copyright.

- [ ] **Step 2: Write PageLayout** — Wrapper for static pages with narrow/wide variants, hero section.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(ui): add Footer and PageLayout for static pages"
```

---

## Phase 2, Stream F: Step Components

### Task 33: UploadZone + FileInfo

**Files:**
- Create: `frontend/src/components/upload/UploadZone.tsx`
- Create: `frontend/src/components/upload/FileInfo.tsx`

- [ ] **Step 1: Write UploadZone** — react-dropzone, drag state with pulse animation, file validation (type, size), XHR upload progress. Props: `onFileAccepted: (file: File, metadata: FileMetadata, taskId: string) => void`, `onError: (error: string) => void`, `uploading?: boolean`, `uploadProgress?: number` (all from spec Section 13, with extended callback signature to include metadata and taskId since UploadZone handles the upload API call internally).

- [ ] **Step 2: Write FileInfo** — Card showing filename, duration, format, resolution, size, codec. Accepts `FileMetadata` directly (raw numbers for duration and size), formats internally using `formatFileSize()` and `formatDuration()` from `types.ts`. **Note:** This deviates from the spec's `FileInfoProps` which uses pre-formatted strings — we use raw numbers for consistency with the store data model.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(ui): add UploadZone with drag-and-drop and FileInfo card"
```

---

### Task 34: ProjectCard

**Files:**
- Create: `frontend/src/components/upload/ProjectCard.tsx`

- [ ] **Step 1: Write ProjectCard** — Shows filename, relative time, status badge, duration. Click navigates to workspace. Hover lift animation.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): add ProjectCard for recent project drawer"
```

---

### Task 35: TranscribeForm + ModelSelector + LanguageSelect + TranscribeOptions

**Files:**
- Create: `frontend/src/components/transcribe/TranscribeForm.tsx`
- Create: `frontend/src/components/transcribe/ModelSelector.tsx`
- Create: `frontend/src/components/transcribe/LanguageSelect.tsx`
- Create: `frontend/src/components/transcribe/TranscribeOptions.tsx`

- [ ] **Step 1: Write ModelSelector** — Radio-style cards for each model. Shows name, description, speed, accuracy. Recommended badge on medium. Loaded/preloading/unloaded status from `uiStore.modelPreloadStatus`. Reads model list from `/system-info` API.

- [ ] **Step 2: Write LanguageSelect** — Select component with auto-detect default. Fetches language list from `/languages` API. Search/filter support.

- [ ] **Step 3: Write TranscribeOptions** — Collapsible "Advanced Options" section. Checkboxes: speaker diarization, word-level timestamps. Toggle: translate after transcription (with language picker).

- [ ] **Step 4: Write TranscribeForm** — Composes ModelSelector + LanguageSelect + TranscribeOptions. "Begin Transcription" button opens ConfirmDialog. On confirm: calls `api.upload()` with FormData, sets `workspaceStore.setProjectId()`, starts SSE via `useSSE`. Reads defaults from `preferencesStore`.

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(ui): add TranscribeForm with ModelSelector, LanguageSelect, TranscribeOptions"
```

---

### Task 36: TranscribeProgress

**Files:**
- Create: `frontend/src/components/transcribe/TranscribeProgress.tsx`

- [ ] **Step 1: Write TranscribeProgress** — Reads from `transcribeStore`. Shows: progress bar (percentage + ETA), pipeline steps (list with checkmarks), liveness indicator (pulsing dot when SSE connected), elapsed time, segment count, speed. Cancel button with ConfirmDialog.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): add TranscribeProgress with live pipeline steps and ETA"
```

---

### Task 37: TranslatePanel

**Files:**
- Create: `frontend/src/components/translate/TranslatePanel.tsx`

- [ ] **Step 1: Write TranslatePanel** — Source language (auto-detected, read-only). Target language dropdown. Engine selector (radio cards: Whisper vs Argos with descriptions). "Begin Translation" button. Progress bar during translation. Reads/writes `translateStore`.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): add TranslatePanel for post-hoc translation"
```

---

### Task 38: EmbedPanel + ModeSelector + StyleOptions

**Files:**
- Create: `frontend/src/components/embed/EmbedPanel.tsx`
- Create: `frontend/src/components/embed/ModeSelector.tsx`
- Create: `frontend/src/components/embed/StyleOptions.tsx`

- [ ] **Step 1: Write ModeSelector** — Radio cards: Soft embed (recommended badge) vs Hard burn. Descriptions for each.

- [ ] **Step 2: Write StyleOptions** — Only shown for hard burn. Preset selector (Default, YouTube White, YouTube Yellow, Cinema, Large Bold, Top). Custom options: font size, color, position, background opacity.

- [ ] **Step 3: Write EmbedPanel** — Composes ModeSelector + StyleOptions. Confirm dialog. Progress bar during embed. Reads/writes `embedStore`. Calls `api.embedQuick()` or `api.combineStart()`.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(ui): add EmbedPanel with ModeSelector and StyleOptions"
```

---

### Task 39: ExportPanel + DownloadButtons + SubtitlePreview + TimingBreakdown

**Files:**
- Create: `frontend/src/components/export/ExportPanel.tsx`
- Create: `frontend/src/components/export/DownloadButtons.tsx`
- Create: `frontend/src/components/export/SubtitlePreview.tsx`
- Create: `frontend/src/components/export/TimingBreakdown.tsx`

- [ ] **Step 1: Write DownloadButtons** — SRT, VTT, JSON buttons showing file sizes. Video download if embedded. "Download All" zip. Uses `api.downloadUrl()` and `api.downloadAllUrl()`.

- [ ] **Step 2: Write SubtitlePreview** — Scrollable list of segments with timecodes. Copy-all button. Uses `formatTimecode()` from types.ts. Segments use `number` (seconds), formatted internally. Props: `segments`, `autoScroll?`, `highlightIndex?` (highlights a specific segment), `onCopyAll?` (per spec Section 13).

- [ ] **Step 3: Write TimingBreakdown** — Collapsible table of pipeline step timings. Uses `Radix.Collapsible`.

- [ ] **Step 4: Write ExportPanel** — Success banner. Composes DownloadButtons + SubtitlePreview (in context panel) + TimingBreakdown. "What's next?" smart suggestions: New Transcription, Re-transcribe, Translate.

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(ui): add ExportPanel with download, preview, timing breakdown"
```

---

## Phase 2, Stream G: System Components

### Task 40: HealthIndicator

**Files:**
- Create: `frontend/src/components/system/HealthIndicator.tsx`

- [ ] **Step 1: Write HealthIndicator** — Colored dot in header (green/amber/red). Tooltip on hover showing CPU%, RAM%, disk. Reads from `uiStore.systemHealth`.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): add HealthIndicator with colored dot and tooltip"
```

---

### Task 41: ConnectionBanner

**Files:**
- Create: `frontend/src/components/system/ConnectionBanner.tsx`

- [ ] **Step 1: Write ConnectionBanner** — Shows when: SSE disconnected (yellow "Reconnecting..."), model loading (blue "Loading model..."), system critical (red banner). Reads from `uiStore`.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): add ConnectionBanner for SSE/model/critical states"
```

---

### Task 42: ErrorBoundary

**Files:**
- Create: `frontend/src/components/system/ErrorBoundary.tsx`

- [ ] **Step 1: Write ErrorBoundary** — React error boundary with fallback UI. "Something went wrong" card with "Reload" button. Styled with new tokens.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): add ErrorBoundary with styled fallback"
```

---

## Phase 3: Integration + Pages

### Task 43: Wire Workspace Flow

**Files:**
- Create: `frontend/src/pages/HomePage.tsx`
- Create: `frontend/src/pages/WorkspacePage.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Write HomePage**

```typescript
// frontend/src/pages/HomePage.tsx
import { AppShell } from '../components/layout/AppShell'
import { UploadZone } from '../components/upload/UploadZone'
import { ProjectDrawer } from '../components/layout/ProjectDrawer'
import { Card } from '../components/ui/Card'
import { navigate } from '../Router'
import { useWorkspaceStore } from '../store/workspaceStore'
import { useRecentProjectsStore } from '../store/recentProjectsStore'
import type { FileMetadata } from '../types'
import { Mic, Globe, Zap } from 'lucide-react'

export function HomePage() {
  const initFromUpload = useWorkspaceStore(s => s.initFromUpload)
  const setProjectId = useWorkspaceStore(s => s.setProjectId)
  const addProject = useRecentProjectsStore(s => s.addProject)

  const handleFileAccepted = async (file: File, metadata: FileMetadata, taskId: string) => {
    initFromUpload(file, metadata)
    setProjectId(taskId)
    addProject({
      taskId,
      filename: metadata.filename,
      createdAt: new Date().toISOString(),
      status: 'processing',
      duration: metadata.duration,
      lastStep: 'transcribe',
    })
    navigate(`/project/${taskId}`)
  }

  return (
    <AppShell>
      <div className="flex gap-6 flex-col lg:flex-row">
        {/* Upload zone */}
        <div className="flex-1">
          <Card shadow padding="lg">
            <UploadZone onFileAccepted={handleFileAccepted} />
          </Card>
        </div>

        {/* Project drawer */}
        <div className="w-full lg:w-80">
          <ProjectDrawer />
        </div>
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8">
        {[
          { icon: Mic, title: 'Accurate', desc: 'AI-powered transcription with multiple model sizes' },
          { icon: Globe, title: '30+ Languages', desc: 'Auto-detect or choose from supported languages' },
          { icon: Zap, title: 'Fast Processing', desc: 'Optimized pipeline with real-time progress' },
        ].map(f => (
          <Card key={f.title} border padding="md">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-[var(--radius)] bg-[var(--color-primary-light)]">
                <f.icon size={20} className="text-[var(--color-primary)]" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[var(--color-text)]">{f.title}</h3>
                <p className="text-sm text-[var(--color-text-muted)] mt-0.5">{f.desc}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </AppShell>
  )
}
```

- [ ] **Step 2: Write WorkspacePage**

```typescript
// frontend/src/pages/WorkspacePage.tsx
import { useEffect } from 'react'
import { AppShell } from '../components/layout/AppShell'
import { Workspace } from '../components/layout/Workspace'
import { useWorkspaceStore } from '../store/workspaceStore'
import { useSSE } from '../hooks/useSSE'
import { api } from '../api/client'
import { Spinner } from '../components/ui/Spinner'

export function WorkspacePage({ projectId }: { projectId: string }) {
  const currentStep = useWorkspaceStore(s => s.currentStep)
  const wsProjectId = useWorkspaceStore(s => s.projectId)
  const setProjectId = useWorkspaceStore(s => s.setProjectId)
  const restoreFromTask = useWorkspaceStore(s => s.restoreFromTask)

  // Session restore: if navigating directly to /project/:id
  useEffect(() => {
    if (wsProjectId === projectId) return // already loaded

    setProjectId(projectId)
    api.progress(projectId).then(data => {
      restoreFromTask(data)
    }).catch(() => {
      restoreFromTask({ status: 'error' })
    })
  }, [projectId, wsProjectId, setProjectId, restoreFromTask])

  // Connect SSE for in-progress tasks
  useSSE(projectId)

  if (!wsProjectId) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-20">
          <Spinner size="lg" />
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <Workspace />
    </AppShell>
  )
}
```

- [ ] **Step 3: Update main.tsx**

Update imports — wrap app with `TooltipProvider`:

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

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(ui): wire HomePage, WorkspacePage, and updated main.tsx entry"
```

---

### Task 44: Static Pages

**Files:**
- Create: `frontend/src/pages/StatusPage.tsx`
- Create: `frontend/src/pages/AboutPage.tsx`
- Create: `frontend/src/pages/SecurityPage.tsx`
- Create: `frontend/src/pages/ContactPage.tsx`

- [ ] **Step 1: Rewrite all static pages** using new `AppShell` + `PageLayout` + new design tokens. Port content from existing pages but apply new styling.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(ui): rewrite static pages (Status, About, Security, Contact)"
```

---

### Task 45: Preferences Panel

**Files:**
- Create: `frontend/src/components/settings/PreferencesPanel.tsx`

- [ ] **Step 1: Write PreferencesPanel** — Dialog with form fields for: default model, default language, default format, auto-copy toggle, confirm-before-transcribe toggle. Reads/writes `preferencesStore`.

- [ ] **Step 2: Wire to Header** settings button.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(ui): add PreferencesPanel dialog with user defaults"
```

---

## Phase 4: Testing + Deploy

### Task 46: Integration Tests

**Files:**
- Create: `frontend/src/__tests__/integration/workspace-flow.test.tsx`
- Create: `frontend/src/__tests__/integration/session-restore.test.tsx`

- [ ] **Step 1: Write workspace flow test** — Upload file → workspace opens → transcribe form visible → mock SSE events → progress updates → completion → export view. End-to-end user journey through stores.

- [ ] **Step 2: Write session restore test** — Navigate to `/project/:id` directly → polls progress API → restores correct step and state.

- [ ] **Step 3: Run tests, commit**

```bash
git commit -m "test(ui): add integration tests for workspace flow and session restore"
```

---

### Task 47: Accessibility Tests

**Files:**
- Create: `frontend/src/__tests__/accessibility.test.tsx`

- [ ] **Step 1: Write accessibility tests** — Focus management in dialogs, skip nav link, ARIA attributes on step bar and progress bar, keyboard navigation, touch targets (44px minimum).

- [ ] **Step 2: Run tests, commit**

```bash
git commit -m "test(ui): add WCAG 2.1 AA accessibility tests"
```

---

### Task 48: Responsive Tests

**Files:**
- Create: `frontend/src/__tests__/responsive.test.tsx`

- [ ] **Step 1: Write responsive tests** — Verify layout changes at breakpoints: mobile (single column, context panel below), tablet (collapsible context), desktop (two columns). Step bar scrollable on mobile.

- [ ] **Step 2: Run tests, commit**

```bash
git commit -m "test(ui): add responsive layout tests for all breakpoints"
```

---

### Task 49: Build + Deploy to newui

**Files:**
- No new files

- [ ] **Step 1: Run full test suite**

Run: `cd frontend && npx vitest run`
Expected: All tests PASS

- [ ] **Step 2: Run lint**

Run: `cd frontend && npx eslint .`
Expected: No errors

- [ ] **Step 3: Build production bundle**

Run: `cd frontend && npx vite build`
Expected: Build succeeds, `frontend/dist/` created

- [ ] **Step 4: Deploy to newui**

Run: `sudo docker compose --profile newui up -d --build --force-recreate`
Expected: Container rebuilds with new frontend

- [ ] **Step 5: Verify health**

Run: `curl -s http://127.0.0.1:8001/health | python3 -m json.tool`
Expected: `{"status": "ok", ...}`

- [ ] **Step 6: Commit any final fixes**

```bash
git commit -m "chore: final build verification for redesign deployment"
```

---

## Cleanup (After Investor Approval)

Once the investor approves on `newui.openlabs.club`:

- [ ] Delete old component files that are no longer imported
- [ ] Delete old store files (`taskStore.ts` if fully replaced)
- [ ] Remove old `App.tsx` (root-level duplicate)
- [ ] Update `docs/lumen/DESIGN_SYSTEM.md` to reflect new design
- [ ] Deploy to production: `sudo docker compose --profile cpu up -d --build --force-recreate`

---

## Summary

| Phase | Tasks | Parallel Streams | Estimated Steps |
|-------|-------|------------------|-----------------|
| Phase 0: Foundation | 1-3c | Sequential | ~20 steps |
| Phase 1: Primitives + Stores + API + Hooks | 4-27 | 4 streams (A/B/C/D) | ~90 steps |
| Phase 2: Layout + Features + System | 28-42 | 3 streams (E/F/G) | ~50 steps |
| Phase 3: Integration + Pages | 43-45 | Sequential | ~15 steps |
| Phase 4: Testing + Deploy | 46-49 | Sequential | ~15 steps |
| **Total** | **49 tasks + 2 sub-tasks** | **Up to 4 parallel** | **~190 steps** |
