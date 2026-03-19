# Premium Editorial UI/UX Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform SubForge from a minimal upload tool into a professional power-user workstation with a Premium Editorial design (Stripe/Apple aesthetic), full dark/light theme support, and significantly more user-facing controls and settings.

**Architecture:** Replace the existing "Cool Professional" Lumen design tokens with a new Premium Editorial system — warm neutrals, refined typography (Inter stays but with tighter tracking), stronger visual hierarchy. Add dark mode via `[data-theme="dark"]` CSS overrides. Expand `preferencesStore` to cover all backend capabilities. Add new Settings page and enhance editor with power-user controls. All changes are frontend-only — the backend API already supports everything.

**Tech Stack:** React 19, Tailwind CSS v4 (CSS custom properties), Zustand, Radix UI, CVA, lucide-react, Vitest + React Testing Library

---

## File Structure

### New Files to Create
| File | Responsibility |
|------|---------------|
| `frontend/src/pages/SettingsPage.tsx` | Dedicated settings/preferences page |
| `frontend/src/components/settings/GeneralSettings.tsx` | Default model, language, format, line chars |
| `frontend/src/components/settings/TranscriptionSettings.tsx` | Word timestamps, initial prompt, VAD, beam size |
| `frontend/src/components/settings/AppearanceSettings.tsx` | Theme toggle (light/dark/system) |
| `frontend/src/components/settings/EmbedSettings.tsx` | Default embed mode, custom font/color/size |
| `frontend/src/components/editor/FileMetadataPanel.tsx` | Rich file info (codec, resolution, bitrate, FPS, size) |
| `frontend/src/components/editor/AdvancedUploadOptions.tsx` | Collapsible advanced options on upload |
| `frontend/src/components/editor/BulkEditBar.tsx` | Multi-select + find-replace toolbar |
| `frontend/src/components/editor/CustomEmbedStyler.tsx` | Full font/color/size/position/opacity controls |
| `frontend/src/components/ui/Switch.tsx` | Toggle switch component |
| `frontend/src/components/ui/Slider.tsx` | Range slider component |
| `frontend/src/components/ui/Tabs.tsx` | Tabs component (for settings sections) |
| `frontend/src/components/ui/ColorPicker.tsx` | Hex color input with preview |
| `frontend/src/components/ui/ThemeToggle.tsx` | Light/dark/system toggle button |

### Files to Modify
| File | Changes |
|------|---------|
| `frontend/src/index.css` | New Premium Editorial tokens + `[data-theme="dark"]` overrides |
| `frontend/src/store/preferencesStore.ts` | Expand with model, language, theme, transcription, embed defaults |
| `frontend/src/Router.tsx` | Add `/settings` route |
| `frontend/src/navigation.ts` | Add `settings` route match |
| `frontend/src/components/layout/Header.tsx` | Add Settings nav link + theme toggle |
| `frontend/src/components/layout/Footer.tsx` | Update styling to Premium Editorial |
| `frontend/src/components/layout/AppShell.tsx` | Theme class application |
| `frontend/src/components/ui/Button.tsx` | Update CVA variants for new color system |
| `frontend/src/components/ui/Card.tsx` | Update for new shadow/border system |
| `frontend/src/components/ui/Input.tsx` | Update focus ring colors |
| `frontend/src/components/ui/Select.tsx` | Update for new design tokens |
| `frontend/src/components/ui/Badge.tsx` | Update colors |
| `frontend/src/components/ui/Dialog.tsx` | Update backdrop and styling |
| `frontend/src/components/landing/UploadZone.tsx` | Add collapsible advanced options panel |
| `frontend/src/components/editor/EditorToolbar.tsx` | Add bulk edit, file metadata toggle, keyboard shortcut hint |
| `frontend/src/components/editor/ContextPanel.tsx` | Add file metadata tab, enhance info density, integrate FileMetadataPanel |
| `frontend/src/components/editor/EmbedPanel.tsx` | Replace preset-only UI with full custom styler |
| `frontend/src/components/editor/RetranscribeDialog.tsx` | Add word_timestamps, initial_prompt, num_speakers |
| `frontend/src/components/editor/SegmentList.tsx` | Multi-select support |
| `frontend/src/components/editor/SegmentRow.tsx` | Checkbox for multi-select |
| `frontend/src/components/editor/DownloadMenu.tsx` | Use preferences as defaults |
| `frontend/src/pages/StatusPage.tsx` | Real health dashboard with live metrics |
| `frontend/src/pages/LandingPage.tsx` | Advanced upload options integration |
| `frontend/src/pages/EditorPage.tsx` | Wire new panels and bulk edit |

---

## Task 1: Premium Editorial Design Tokens (Light)

**Files:**
- Modify: `frontend/src/index.css:1-95`

Replace the "Cool Professional" color palette with Premium Editorial warm neutrals.

- [ ] **Step 1: Back up current token values**

Note current values for reference. No code change.

- [ ] **Step 2: Replace `:root` color palette**

In `frontend/src/index.css`, replace the `:root` color palette section (from `--color-bg` through `--color-info-light`) with:

```css
  :root {
    /* Premium Editorial — Warm neutrals, refined accents */
    --color-bg: #FAFAF9;
    --color-surface: #FFFFFF;
    --color-surface-raised: #F5F5F4;
    --color-surface-sunken: #F0EFED;
    --color-border: #E7E5E4;
    --color-border-strong: #A8A29E;
    --color-border-focus: #18181B;

    --color-text: #18181B;
    --color-text-secondary: #52525B;
    --color-text-muted: #A1A1AA;
    --color-text-inverse: #FAFAF9;

    /* Accent — muted indigo (Stripe-inspired) */
    --color-primary: #4F46E5;
    --color-primary-hover: #4338CA;
    --color-primary-light: #EEF2FF;
    --color-primary-ring: rgba(79, 70, 229, 0.24);

    --color-success: #059669;
    --color-success-light: #ECFDF5;
    --color-warning: #D97706;
    --color-warning-light: #FFFBEB;
    --color-danger: #DC2626;
    --color-danger-light: #FEF2F2;
    --color-info: #0891B2;
    --color-info-light: #ECFEFF;
```

- [ ] **Step 3: Update typography tokens**

Replace the typography section (from `--font-sans` through `--leading-relaxed`) with tighter tracking and refined weights:

```css
    /* Typography — Premium Editorial */
    --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
    --font-display: 'Inter', system-ui, -apple-system, sans-serif;

    --text-xs: 0.75rem;
    --text-sm: 0.875rem;
    --text-base: 1rem;
    --text-lg: 1.125rem;
    --text-xl: 1.25rem;
    --text-2xl: 1.5rem;
    --text-3xl: 1.875rem;

    --font-normal: 400;
    --font-medium: 500;
    --font-semibold: 600;
    --font-bold: 700;

    --leading-tight: 1.2;
    --leading-normal: 1.5;
    --leading-relaxed: 1.65;

    --tracking-tight: -0.025em;
    --tracking-normal: -0.011em;
    --tracking-wide: 0.025em;
```

- [ ] **Step 4: Update shadow tokens for softer, warmer feel**

Replace the shadows section (from `--shadow-sm` through `--shadow-focus`):

```css
    /* Shadows — warm, layered */
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 3px 0 rgba(0, 0, 0, 0.04);
    --shadow-md: 0 2px 4px -1px rgba(0, 0, 0, 0.04), 0 4px 8px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 4px 8px -2px rgba(0, 0, 0, 0.06), 0 10px 20px -2px rgba(0, 0, 0, 0.08);
    --shadow-xl: 0 8px 16px -4px rgba(0, 0, 0, 0.08), 0 20px 40px -4px rgba(0, 0, 0, 0.1);
    --shadow-focus: 0 0 0 3px var(--color-primary-ring);
```

- [ ] **Step 5: Update heading styles for editorial feel**

Replace the heading styles section (`h1, h2, h3, h4, h5, h6` through the individual size rules):

```css
  h1, h2, h3, h4, h5, h6 {
    margin: 0;
    font-weight: var(--font-semibold);
    line-height: var(--leading-tight);
    letter-spacing: var(--tracking-tight);
    color: var(--color-text);
  }

  h1 { font-size: var(--text-3xl); font-weight: var(--font-bold); }
  h2 { font-size: var(--text-2xl); }
  h3 { font-size: var(--text-xl); }
  h4, h5, h6 { font-size: var(--text-lg); }
```

- [ ] **Step 6: Verify app renders with new tokens**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/index.css
git commit -m "style(ui): replace Lumen tokens with Premium Editorial light theme"
```

---

## Task 2: Dark Mode Tokens

**Files:**
- Modify: `frontend/src/index.css` (add after `:root` block, inside `@layer base`)

- [ ] **Step 1: Add `[data-theme="dark"]` override block**

Add after the `:root { ... }` closing brace, before `*, *::before, *::after`. We use a single `[data-theme="dark"]` selector — NO `@media (prefers-color-scheme: dark)` duplication. System dark preference is handled by the `useTheme` hook (Task 12) which explicitly sets `data-theme="dark"` when the OS prefers dark.

```css
  [data-theme="dark"] {
    --color-bg: #0C0A09;
    --color-surface: #1C1917;
    --color-surface-raised: #292524;
    --color-surface-sunken: #0C0A09;
    --color-border: #44403C;
    --color-border-strong: #78716C;
    --color-border-focus: #E7E5E4;

    --color-text: #FAFAF9;
    --color-text-secondary: #D6D3D1;
    --color-text-muted: #78716C;
    --color-text-inverse: #18181B;

    --color-primary: #818CF8;
    --color-primary-hover: #A5B4FC;
    --color-primary-light: rgba(129, 140, 248, 0.12);
    --color-primary-ring: rgba(129, 140, 248, 0.3);

    --color-success: #34D399;
    --color-success-light: rgba(52, 211, 153, 0.12);
    --color-warning: #FBBF24;
    --color-warning-light: rgba(251, 191, 36, 0.12);
    --color-danger: #F87171;
    --color-danger-light: rgba(248, 113, 113, 0.12);
    --color-info: #22D3EE;
    --color-info-light: rgba(34, 211, 238, 0.12);

    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.2);
    --shadow-md: 0 2px 4px -1px rgba(0, 0, 0, 0.3), 0 4px 8px -1px rgba(0, 0, 0, 0.2);
    --shadow-lg: 0 4px 8px -2px rgba(0, 0, 0, 0.4), 0 10px 20px -2px rgba(0, 0, 0, 0.3);
    --shadow-xl: 0 8px 16px -4px rgba(0, 0, 0, 0.5), 0 20px 40px -4px rgba(0, 0, 0, 0.4);

    color-scheme: dark;
  }
```

- [ ] **Step 2: Update scrollbar styling for dark mode**

After the existing scrollbar styles (line ~186), add:

```css
  [data-theme="dark"] *::-webkit-scrollbar-thumb {
    background-color: var(--color-border-strong);
  }
```

- [ ] **Step 3: Verify both themes render**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/index.css
git commit -m "style(ui): add dark mode tokens with system preference fallback"
```

---

## Task 3: Theme Toggle Component

**Files:**
- Create: `frontend/src/components/ui/ThemeToggle.tsx`
- Modify: `frontend/src/components/layout/Header.tsx`

- [ ] **Step 1: Create ThemeToggle component**

```tsx
// frontend/src/components/ui/ThemeToggle.tsx
import { Sun, Moon, Monitor } from 'lucide-react'
import { useTheme, type Theme } from '../../hooks/useTheme'

const icons: Record<Theme, typeof Sun> = { light: Sun, dark: Moon, system: Monitor }
const labels: Record<Theme, string> = { light: 'Light', dark: 'Dark', system: 'System' }

export function ThemeToggle() {
  const { theme, cycleTheme } = useTheme()
  const Icon = icons[theme]

  return (
    <button
      onClick={cycleTheme}
      className="inline-flex items-center justify-center h-8 w-8 rounded-md text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition-colors"
      aria-label={`Theme: ${labels[theme]}. Click to switch.`}
      title={`Theme: ${labels[theme]}`}
    >
      <Icon className="h-4 w-4" />
    </button>
  )
}
```

- [ ] **Step 2: Add ThemeToggle to Header**

In `frontend/src/components/layout/Header.tsx`, import `ThemeToggle` and add it to the nav area before `HealthIndicator`:

```tsx
import { ThemeToggle } from '../ui/ThemeToggle'

// In the nav, after the map loop, before <HealthIndicator />:
<ThemeToggle />
```

- [ ] **Step 3: Add Settings link to Header nav**

In `Header.tsx`, add Settings to the nav links array:

```tsx
{[
  { href: '/status', label: 'Status' },
  { href: '/settings', label: 'Settings' },
  { href: '/about', label: 'About' },
].map(({ href, label }) => (
```

- [ ] **Step 4: Verify theme toggles work**

Run: `cd frontend && npm run dev` — click theme button, verify light/dark/system cycling.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/ThemeToggle.tsx frontend/src/components/layout/Header.tsx
git commit -m "feat(ui): add theme toggle (light/dark/system) to header"
```

---

## Task 4: Expanded Preferences Store

**Files:**
- Modify: `frontend/src/store/preferencesStore.ts`

- [ ] **Step 1: Expand interface and defaults**

Replace entire file:

```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface PreferencesState {
  // General
  preferredFormat: 'srt' | 'vtt' | 'json'
  maxLineChars: number
  defaultModel: 'tiny' | 'base' | 'small' | 'medium' | 'large' | 'auto'
  defaultLanguage: string

  // Transcription
  wordTimestamps: boolean
  initialPrompt: string
  diarizeByDefault: boolean
  numSpeakers: number | null

  // Embed
  defaultEmbedMode: 'soft' | 'hard'
  defaultEmbedPreset: string
  customFontName: string
  customFontSize: number
  customFontColor: string
  customBold: boolean
  customPosition: 'top' | 'center' | 'bottom'
  customBackgroundOpacity: number

  // Appearance
  theme: 'light' | 'dark' | 'system'

  // Actions — generic setter + backward-compatible named setters
  setPreference: <K extends keyof PreferencesState>(key: K, value: PreferencesState[K]) => void
  setPreferredFormat: (format: 'srt' | 'vtt' | 'json') => void
  setMaxLineChars: (chars: number) => void
  reset: () => void
}

const defaults: Omit<PreferencesState, 'setPreference' | 'reset'> = {
  preferredFormat: 'srt',
  maxLineChars: 42,
  defaultModel: 'auto',
  defaultLanguage: 'auto',

  wordTimestamps: false,
  initialPrompt: '',
  diarizeByDefault: false,
  numSpeakers: null,

  defaultEmbedMode: 'soft',
  defaultEmbedPreset: 'default',
  customFontName: 'Arial',
  customFontSize: 24,
  customFontColor: '#FFFFFF',
  customBold: false,
  customPosition: 'bottom',
  customBackgroundOpacity: 0.5,

  theme: 'system',
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      ...defaults,
      setPreference: (key, value) => set({ [key]: value }),
      setPreferredFormat: (format) => set({ preferredFormat: format }),
      setMaxLineChars: (chars) => set({ maxLineChars: chars }),
      reset: () => set(defaults),
    }),
    { name: 'sg-preferences' }
  )
)
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/store/preferencesStore.ts
git commit -m "feat(store): expand preferences with model, language, transcription, embed, theme defaults"
```

---

## Task 5: Wire Theme Preference to useTheme Hook (MUST run before Task 6)

> **Moved from original Task 12 to avoid state desync.** The ThemeToggle (Task 3) and AppearanceSettings (Task 6) both need to read/write from the same source — `preferencesStore.theme`. This task must complete before creating Settings page components that write to the theme preference.

**Files:**
- Modify: `frontend/src/hooks/useTheme.ts`

- [ ] **Step 1: Sync useTheme with preferencesStore and handle system dark preference**

Replace the entire `useTheme.ts` file. Key changes:
- Read/write from `preferencesStore` instead of raw localStorage
- For `system` mode, detect OS preference and explicitly set `data-theme="dark"` or `data-theme="light"` — this eliminates the need for `@media (prefers-color-scheme: dark)` CSS duplication
- Export `Theme` type for consumers (e.g., `ThemeToggle.tsx`)

```typescript
import { useEffect } from 'react'
import { usePreferencesStore } from '../store/preferencesStore'

export type Theme = 'light' | 'dark' | 'system'

export function useTheme() {
  const theme = usePreferencesStore((s) => s.theme)
  const setPreference = usePreferencesStore((s) => s.setPreference)

  useEffect(() => {
    const root = document.documentElement

    const applyTheme = () => {
      if (theme === 'dark') {
        root.setAttribute('data-theme', 'dark')
      } else if (theme === 'light') {
        root.setAttribute('data-theme', 'light')
      } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        root.setAttribute('data-theme', prefersDark ? 'dark' : 'light')
      }
    }

    applyTheme()

    if (theme === 'system') {
      const mql = window.matchMedia('(prefers-color-scheme: dark)')
      const handler = () => applyTheme()
      mql.addEventListener('change', handler)
      return () => mql.removeEventListener('change', handler)
    }
  }, [theme])

  const setTheme = (t: Theme) => setPreference('theme', t)
  const cycleTheme = () => {
    setPreference('theme',
      theme === 'system' ? 'dark' :
      theme === 'dark' ? 'light' : 'system'
    )
  }

  return { theme, setTheme, cycleTheme }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useTheme.ts
git commit -m "feat(ui): sync theme toggle with preferences store (persisted) and handle system dark"
```

---

## Task 6: New UI Primitives (Switch, Slider, ColorPicker, Tabs)

> Note: Task 5 (previously Task 12) was moved here to sync theme state before Settings page creation.

**Files:**
- Create: `frontend/src/components/ui/Switch.tsx`
- Create: `frontend/src/components/ui/Slider.tsx`
- Create: `frontend/src/components/ui/ColorPicker.tsx`
- Create: `frontend/src/components/ui/Tabs.tsx`

- [ ] **Step 1: Create Switch component**

```tsx
// frontend/src/components/ui/Switch.tsx
import { cn } from './cn'

interface SwitchProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label?: string
  description?: string
  disabled?: boolean
  id?: string
}

export function Switch({ checked, onChange, label, description, disabled, id }: SwitchProps) {
  const switchId = id || `switch-${label?.toLowerCase().replace(/\s+/g, '-')}`
  return (
    <div className="flex items-start justify-between gap-4">
      {(label || description) && (
        <div className="flex-1 min-w-0">
          {label && (
            <label htmlFor={switchId} className="text-sm font-medium text-[var(--color-text)] cursor-pointer">
              {label}
            </label>
          )}
          {description && (
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{description}</p>
          )}
        </div>
      )}
      <button
        id={switchId}
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors focus-ring',
          checked ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-border-strong)]',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <span
          className={cn(
            'pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow-sm transition-transform mt-0.5',
            checked ? 'translate-x-[18px] ml-0' : 'translate-x-0.5'
          )}
        />
      </button>
    </div>
  )
}
```

- [ ] **Step 2: Create Slider component**

```tsx
// frontend/src/components/ui/Slider.tsx
interface SliderProps {
  value: number
  onChange: (value: number) => void
  min: number
  max: number
  step?: number
  label?: string
  unit?: string
  disabled?: boolean
}

export function Slider({ value, onChange, min, max, step = 1, label, unit, disabled }: SliderProps) {
  return (
    <div className="space-y-1.5">
      {label && (
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-[var(--color-text)]">{label}</label>
          <span className="text-xs font-mono text-[var(--color-text-muted)]">
            {value}{unit}
          </span>
        </div>
      )}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        disabled={disabled}
        className="w-full h-1.5 rounded-full appearance-none bg-[var(--color-border)] accent-[var(--color-primary)] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
      />
    </div>
  )
}
```

- [ ] **Step 3: Create ColorPicker component**

```tsx
// frontend/src/components/ui/ColorPicker.tsx
interface ColorPickerProps {
  value: string
  onChange: (color: string) => void
  label?: string
}

export function ColorPicker({ value, onChange, label }: ColorPickerProps) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label className="text-sm font-medium text-[var(--color-text)]">{label}</label>
      )}
      <div className="flex items-center gap-2">
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="h-8 w-8 rounded-md border border-[var(--color-border)] cursor-pointer p-0.5"
        />
        <input
          type="text"
          value={value.toUpperCase()}
          onChange={(e) => {
            const v = e.target.value
            if (/^#[0-9A-Fa-f]{0,6}$/.test(v)) onChange(v)
          }}
          className="h-8 w-24 px-2 text-xs font-mono bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md"
          placeholder="#FFFFFF"
          maxLength={7}
        />
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create Tabs component**

```tsx
// frontend/src/components/ui/Tabs.tsx
import type { ReactNode } from 'react'
import { cn } from './cn'

interface Tab {
  id: string
  label: string
  icon?: ReactNode
}

interface TabsProps {
  tabs: Tab[]
  activeTab: string
  onChange: (id: string) => void
}

export function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="flex border-b border-[var(--color-border)]" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={activeTab === tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            'flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px',
            activeTab === tab.id
              ? 'border-[var(--color-primary)] text-[var(--color-primary)]'
              : 'border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-border)]'
          )}
        >
          {tab.icon}
          {tab.label}
        </button>
      ))}
    </div>
  )
}
```

- [ ] **Step 5: Verify build**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ui/Switch.tsx frontend/src/components/ui/Slider.tsx frontend/src/components/ui/ColorPicker.tsx frontend/src/components/ui/Tabs.tsx
git commit -m "feat(ui): add Switch, Slider, ColorPicker, Tabs primitives"
```

---

## Task 7: Settings Page

**Files:**
- Create: `frontend/src/pages/SettingsPage.tsx`
- Create: `frontend/src/components/settings/GeneralSettings.tsx`
- Create: `frontend/src/components/settings/TranscriptionSettings.tsx`
- Create: `frontend/src/components/settings/AppearanceSettings.tsx`
- Create: `frontend/src/components/settings/EmbedSettings.tsx`
- Modify: `frontend/src/Router.tsx`
- Modify: `frontend/src/navigation.ts`

- [ ] **Step 1: Add settings route to navigation.ts**

In `frontend/src/navigation.ts`, add `'/settings': 'settings'` to the routes object:

```typescript
const routes: Record<string, string> = {
  '/': 'landing',
  '/status': 'status',
  '/settings': 'settings',
  '/about': 'about',
  '/security': 'security',
  '/contact': 'contact',
}
```

- [ ] **Step 2: Add settings route to Router.tsx**

Import and add case:

```tsx
import { SettingsPage } from './pages/SettingsPage'

// In switch:
case 'settings':
  return <SettingsPage />
```

- [ ] **Step 3: Create GeneralSettings component**

```tsx
// frontend/src/components/settings/GeneralSettings.tsx
import { usePreferencesStore } from '../../store/preferencesStore'
import { Select } from '../ui/Select'
import { Slider } from '../ui/Slider'

const MODEL_OPTIONS = [
  { value: 'auto', label: 'Auto (recommended)' },
  { value: 'tiny', label: 'Tiny — fastest, lower accuracy' },
  { value: 'base', label: 'Base — fast, good accuracy' },
  { value: 'small', label: 'Small — balanced' },
  { value: 'medium', label: 'Medium — slower, high accuracy' },
  { value: 'large', label: 'Large — slowest, best accuracy' },
]

const FORMAT_OPTIONS = [
  { value: 'srt', label: 'SRT (SubRip)' },
  { value: 'vtt', label: 'VTT (WebVTT)' },
  { value: 'json', label: 'JSON (raw segments)' },
]

export function GeneralSettings() {
  const { defaultModel, defaultLanguage, preferredFormat, maxLineChars, setPreference } = usePreferencesStore()

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-base font-semibold text-[var(--color-text)] mb-4">General</h3>
        <div className="space-y-4">
          <Select
            label="Default model"
            value={defaultModel}
            onChange={(e) => setPreference('defaultModel', e.target.value as any)}
            options={MODEL_OPTIONS}
          />
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[var(--color-text)]">Default language</label>
            <input
              type="text"
              value={defaultLanguage}
              onChange={(e) => setPreference('defaultLanguage', e.target.value)}
              placeholder="auto (detect automatically)"
              className="w-full h-9 px-3 text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md"
            />
            <p className="text-xs text-[var(--color-text-muted)]">ISO 639-1 code (e.g., en, es, fr) or "auto"</p>
          </div>
          <Select
            label="Default download format"
            value={preferredFormat}
            onChange={(e) => setPreference('preferredFormat', e.target.value as any)}
            options={FORMAT_OPTIONS}
          />
          <Slider
            label="Max line characters"
            value={maxLineChars}
            onChange={(v) => setPreference('maxLineChars', v)}
            min={20}
            max={120}
            unit=" chars"
          />
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create TranscriptionSettings component**

```tsx
// frontend/src/components/settings/TranscriptionSettings.tsx
import { usePreferencesStore } from '../../store/preferencesStore'
import { Switch } from '../ui/Switch'
import { Slider } from '../ui/Slider'

export function TranscriptionSettings() {
  const { wordTimestamps, initialPrompt, diarizeByDefault, numSpeakers, setPreference } = usePreferencesStore()

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-base font-semibold text-[var(--color-text)] mb-4">Transcription</h3>
        <div className="space-y-5">
          <Switch
            checked={wordTimestamps}
            onChange={(v) => setPreference('wordTimestamps', v)}
            label="Word-level timestamps"
            description="Capture exact timing for each word (increases output detail)"
          />
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[var(--color-text)]">Initial prompt</label>
            <textarea
              value={initialPrompt}
              onChange={(e) => setPreference('initialPrompt', e.target.value.slice(0, 500))}
              placeholder="Domain-specific vocabulary to improve accuracy (e.g., technical terms, names)"
              rows={3}
              className="w-full px-3 py-2 text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md resize-none"
              maxLength={500}
            />
            <p className="text-xs text-[var(--color-text-muted)]">{initialPrompt.length}/500 characters</p>
          </div>
          <Switch
            checked={diarizeByDefault}
            onChange={(v) => setPreference('diarizeByDefault', v)}
            label="Speaker diarization by default"
            description="Identify and label different speakers automatically"
          />
          {diarizeByDefault && (
            <Slider
              label="Expected speakers"
              value={numSpeakers ?? 2}
              onChange={(v) => setPreference('numSpeakers', v)}
              min={1}
              max={10}
              unit=""
            />
          )}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Create AppearanceSettings component**

```tsx
// frontend/src/components/settings/AppearanceSettings.tsx
import { usePreferencesStore } from '../../store/preferencesStore'
import { Sun, Moon, Monitor } from 'lucide-react'
import { cn } from '../ui/cn'

const themes = [
  { value: 'light' as const, label: 'Light', icon: Sun },
  { value: 'dark' as const, label: 'Dark', icon: Moon },
  { value: 'system' as const, label: 'System', icon: Monitor },
]

export function AppearanceSettings() {
  const { theme, setPreference } = usePreferencesStore()

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-base font-semibold text-[var(--color-text)] mb-4">Appearance</h3>
        <div className="grid grid-cols-3 gap-3">
          {themes.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              onClick={() => setPreference('theme', value)}
              className={cn(
                'flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all',
                theme === value
                  ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
                  : 'border-[var(--color-border)] hover:border-[var(--color-border-strong)]'
              )}
            >
              <Icon className="h-5 w-5" />
              <span className="text-sm font-medium">{label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Create EmbedSettings component**

```tsx
// frontend/src/components/settings/EmbedSettings.tsx
import { usePreferencesStore } from '../../store/preferencesStore'
import { Select } from '../ui/Select'
import { Slider } from '../ui/Slider'
import { Switch } from '../ui/Switch'
import { ColorPicker } from '../ui/ColorPicker'
import { cn } from '../ui/cn'

const PRESET_OPTIONS = [
  { value: 'default', label: 'Default (white, 24pt)' },
  { value: 'youtube_white', label: 'YouTube White' },
  { value: 'youtube_yellow', label: 'YouTube Yellow' },
  { value: 'cinema', label: 'Cinema (28pt, no bg)' },
  { value: 'large_bold', label: 'Large Bold (36pt)' },
  { value: 'top', label: 'Top Position' },
]

const POSITION_OPTIONS = [
  { value: 'top', label: 'Top' },
  { value: 'center', label: 'Center' },
  { value: 'bottom', label: 'Bottom' },
]

export function EmbedSettings() {
  const prefs = usePreferencesStore()

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-base font-semibold text-[var(--color-text)] mb-4">Subtitle Embedding</h3>
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-3">
            {(['soft', 'hard'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => prefs.setPreference('defaultEmbedMode', mode)}
                className={cn(
                  'p-3 rounded-lg border-2 text-sm font-medium transition-all text-center',
                  prefs.defaultEmbedMode === mode
                    ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
                    : 'border-[var(--color-border)] hover:border-[var(--color-border-strong)]'
                )}
              >
                {mode === 'soft' ? 'Soft (fast, selectable)' : 'Hard Burn (styled, permanent)'}
              </button>
            ))}
          </div>
          <Select
            label="Style preset"
            value={prefs.defaultEmbedPreset}
            onChange={(e) => prefs.setPreference('defaultEmbedPreset', e.target.value)}
            options={PRESET_OPTIONS}
          />
          <div className="border-t border-[var(--color-border)] pt-4">
            <p className="text-sm font-medium text-[var(--color-text)] mb-3">Custom overrides (hard burn only)</p>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-[var(--color-text)]">Font name</label>
                <input
                  type="text"
                  value={prefs.customFontName}
                  onChange={(e) => prefs.setPreference('customFontName', e.target.value)}
                  className="w-full h-9 px-3 text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md"
                  placeholder="Arial"
                />
              </div>
              <Slider
                label="Font size"
                value={prefs.customFontSize}
                onChange={(v) => prefs.setPreference('customFontSize', v)}
                min={8}
                max={72}
                unit="pt"
              />
              <ColorPicker
                label="Font color"
                value={prefs.customFontColor}
                onChange={(v) => prefs.setPreference('customFontColor', v)}
              />
              <Switch
                checked={prefs.customBold}
                onChange={(v) => prefs.setPreference('customBold', v)}
                label="Bold"
              />
              <Select
                label="Position"
                value={prefs.customPosition}
                onChange={(e) => prefs.setPreference('customPosition', e.target.value as any)}
                options={POSITION_OPTIONS}
              />
              <Slider
                label="Background opacity"
                value={prefs.customBackgroundOpacity}
                onChange={(v) => prefs.setPreference('customBackgroundOpacity', v)}
                min={0}
                max={1}
                step={0.1}
                unit=""
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 7: Create SettingsPage**

```tsx
// frontend/src/pages/SettingsPage.tsx
import { useState } from 'react'
import { Tabs } from '../components/ui/Tabs'
import { GeneralSettings } from '../components/settings/GeneralSettings'
import { TranscriptionSettings } from '../components/settings/TranscriptionSettings'
import { AppearanceSettings } from '../components/settings/AppearanceSettings'
import { EmbedSettings } from '../components/settings/EmbedSettings'
import { usePreferencesStore } from '../store/preferencesStore'
import { Settings, Mic, Palette, Subtitles } from 'lucide-react'

const tabs = [
  { id: 'general', label: 'General', icon: <Settings className="h-4 w-4" /> },
  { id: 'transcription', label: 'Transcription', icon: <Mic className="h-4 w-4" /> },
  { id: 'embed', label: 'Embedding', icon: <Subtitles className="h-4 w-4" /> },
  { id: 'appearance', label: 'Appearance', icon: <Palette className="h-4 w-4" /> },
]

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general')
  const reset = usePreferencesStore((s) => s.reset)

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text)]" style={{ letterSpacing: 'var(--tracking-tight)' }}>Settings</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-1">Configure your SubForge experience</p>
        </div>
        <button
          onClick={reset}
          className="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors"
        >
          Reset all
        </button>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      <div className="mt-6">
        {activeTab === 'general' && <GeneralSettings />}
        {activeTab === 'transcription' && <TranscriptionSettings />}
        {activeTab === 'embed' && <EmbedSettings />}
        {activeTab === 'appearance' && <AppearanceSettings />}
      </div>
    </div>
  )
}
```

- [ ] **Step 8: Verify build and routing**

Run: `cd frontend && npm run build`
Expected: Build succeeds, navigating to /settings shows the page.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/pages/SettingsPage.tsx frontend/src/components/settings/ frontend/src/Router.tsx frontend/src/navigation.ts
git commit -m "feat(ui): add Settings page with general, transcription, embed, appearance tabs"
```

---

## Task 8: Advanced Upload Options

**Files:**
- Create: `frontend/src/components/editor/AdvancedUploadOptions.tsx`
- Modify: `frontend/src/components/landing/UploadZone.tsx`

- [ ] **Step 1: Create AdvancedUploadOptions collapsible panel**

```tsx
// frontend/src/components/editor/AdvancedUploadOptions.tsx
import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { usePreferencesStore } from '../../store/preferencesStore'
import { Select } from '../ui/Select'
import { Switch } from '../ui/Switch'
import { cn } from '../ui/cn'

const MODEL_OPTIONS = [
  { value: 'auto', label: 'Auto' },
  { value: 'tiny', label: 'Tiny' },
  { value: 'base', label: 'Base' },
  { value: 'small', label: 'Small' },
  { value: 'medium', label: 'Medium' },
  { value: 'large', label: 'Large' },
]

interface UploadOptions {
  model: string
  language: string
  diarize: boolean
  numSpeakers: number | null
  wordTimestamps: boolean
  initialPrompt: string
  translateToEnglish: boolean
}

interface Props {
  options: UploadOptions
  onChange: (options: UploadOptions) => void
}

export function AdvancedUploadOptions({ options, onChange }: Props) {
  const [expanded, setExpanded] = useState(false)

  const update = <K extends keyof UploadOptions>(key: K, value: UploadOptions[K]) =>
    onChange({ ...options, ...{ [key]: value } })

  return (
    <div className="mt-4 border border-[var(--color-border)] rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-raised)] transition-colors"
      >
        <span>Advanced options</span>
        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>
      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-[var(--color-border)]">
          <div className="pt-3 grid grid-cols-2 gap-4">
            <Select
              label="Model"
              value={options.model}
              onChange={(e) => update('model', e.target.value)}
              options={MODEL_OPTIONS}
            />
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-[var(--color-text)]">Language</label>
              <input
                type="text"
                value={options.language}
                onChange={(e) => update('language', e.target.value)}
                className="w-full h-9 px-3 text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md"
                placeholder="auto"
              />
            </div>
          </div>
          <Switch
            checked={options.diarize}
            onChange={(v) => update('diarize', v)}
            label="Speaker diarization"
            description="Identify and label speakers"
          />
          <Switch
            checked={options.wordTimestamps}
            onChange={(v) => update('wordTimestamps', v)}
            label="Word timestamps"
            description="Precise timing per word"
          />
          <Switch
            checked={options.translateToEnglish}
            onChange={(v) => update('translateToEnglish', v)}
            label="Translate to English"
            description="Use Whisper's built-in translation"
          />
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[var(--color-text)]">Initial prompt</label>
            <input
              type="text"
              value={options.initialPrompt}
              onChange={(e) => update('initialPrompt', e.target.value.slice(0, 500))}
              className="w-full h-9 px-3 text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md"
              placeholder="Domain vocabulary, names, terms..."
            />
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Integrate into UploadZone**

In `frontend/src/components/landing/UploadZone.tsx`, import `AdvancedUploadOptions` and render it below the drop zone. Wire the options state to the upload form data. The specifics depend on the existing upload handler — the options object should be passed alongside the file in the upload request as additional form fields.

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/editor/AdvancedUploadOptions.tsx frontend/src/components/landing/UploadZone.tsx
git commit -m "feat(ui): add collapsible advanced upload options (model, language, diarize, word timestamps, prompt)"
```

---

## Task 9: Enhanced Editor — File Metadata & Rich Info Panel

**Files:**
- Create: `frontend/src/components/editor/FileMetadataPanel.tsx`
- Modify: `frontend/src/components/editor/ContextPanel.tsx` (contains the info tab — there is no separate InfoPanel.tsx)

- [ ] **Step 1: Create FileMetadataPanel**

```tsx
// frontend/src/components/editor/FileMetadataPanel.tsx
//
// FileMetadata interface (from types.ts):
//   { filename: string, duration: number, format: string,
//     resolution: string | null, size: number, codec: string, isVideo: boolean }
//
// Note: duration is seconds (number), size is bytes (number) — format for display.

import { useEditorStore } from '../../store/editorStore'
import { formatFileSize, formatDuration } from '../../types'

function MetadataRow({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value == null || value === '') return null
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-xs text-[var(--color-text-muted)]">{label}</span>
      <span className="text-xs font-mono text-[var(--color-text)]">{value}</span>
    </div>
  )
}

export function FileMetadataPanel() {
  const meta = useEditorStore((s) => s.fileMetadata)

  if (!meta) return null

  return (
    <div className="space-y-1 divide-y divide-[var(--color-border)]">
      <div className="pb-2">
        <h4 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-2">File</h4>
        <MetadataRow label="Name" value={meta.filename} />
        <MetadataRow label="Size" value={formatFileSize(meta.size)} />
        <MetadataRow label="Format" value={meta.format} />
        <MetadataRow label="Duration" value={formatDuration(meta.duration)} />
      </div>
      {meta.isVideo && (
        <div className="pt-2">
          <h4 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-2">Video</h4>
          <MetadataRow label="Resolution" value={meta.resolution} />
          <MetadataRow label="Codec" value={meta.codec} />
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Integrate into ContextPanel**

In `frontend/src/components/editor/ContextPanel.tsx`, import `FileMetadataPanel` and render it inside the info tab content (the `contextPanelContent === 'info'` branch), replacing the sparse metadata display with the richer component.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/editor/FileMetadataPanel.tsx frontend/src/components/editor/ContextPanel.tsx
git commit -m "feat(ui): add rich file metadata panel (codec, resolution, size, format)"
```

---

## Task 10: Enhanced Editor — Custom Embed Styler

**Files:**
- Create: `frontend/src/components/editor/CustomEmbedStyler.tsx`
- Modify: `frontend/src/components/editor/EmbedPanel.tsx`

- [ ] **Step 1: Create CustomEmbedStyler**

```tsx
// frontend/src/components/editor/CustomEmbedStyler.tsx
import { Slider } from '../ui/Slider'
import { ColorPicker } from '../ui/ColorPicker'
import { Switch } from '../ui/Switch'
import { Select } from '../ui/Select'

interface EmbedStyle {
  fontName: string
  fontSize: number
  fontColor: string
  bold: boolean
  position: 'top' | 'center' | 'bottom'
  backgroundOpacity: number
}

const POSITION_OPTIONS = [
  { value: 'top', label: 'Top' },
  { value: 'center', label: 'Center' },
  { value: 'bottom', label: 'Bottom' },
]

interface Props {
  style: EmbedStyle
  onChange: (style: EmbedStyle) => void
}

export function CustomEmbedStyler({ style, onChange }: Props) {
  const update = <K extends keyof EmbedStyle>(key: K, value: EmbedStyle[K]) =>
    onChange({ ...style, [key]: value })

  return (
    <div className="space-y-4 pt-3 border-t border-[var(--color-border)]">
      <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide">Custom Style</p>
      <div className="space-y-1.5">
        <label className="text-sm font-medium text-[var(--color-text)]">Font</label>
        <input
          type="text"
          value={style.fontName}
          onChange={(e) => update('fontName', e.target.value)}
          className="w-full h-9 px-3 text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md"
        />
      </div>
      <Slider label="Size" value={style.fontSize} onChange={(v) => update('fontSize', v)} min={8} max={72} unit="pt" />
      <ColorPicker label="Color" value={style.fontColor} onChange={(v) => update('fontColor', v)} />
      <Switch checked={style.bold} onChange={(v) => update('bold', v)} label="Bold" />
      <Select
        label="Position"
        value={style.position}
        onChange={(e) => update('position', e.target.value as any)}
        options={POSITION_OPTIONS}
      />
      <Slider label="Background opacity" value={style.backgroundOpacity} onChange={(v) => update('backgroundOpacity', v)} min={0} max={1} step={0.1} />
    </div>
  )
}
```

- [ ] **Step 2: Integrate into EmbedPanel**

In `frontend/src/components/editor/EmbedPanel.tsx`, when `mode === 'hard'`, show `CustomEmbedStyler` below the preset selector. Send custom style params alongside the embed request.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/editor/CustomEmbedStyler.tsx frontend/src/components/editor/EmbedPanel.tsx
git commit -m "feat(ui): add full custom embed styler (font, color, size, position, opacity)"
```

---

## Task 11: Enhanced Editor — Retranscribe Dialog with Advanced Options

**Files:**
- Modify: `frontend/src/components/editor/RetranscribeDialog.tsx`

- [ ] **Step 1: Add word_timestamps, initial_prompt, num_speakers fields**

In the existing `RetranscribeDialog.tsx`, add these controls alongside the existing model/language/diarize fields:

- `word_timestamps` — Switch toggle
- `initial_prompt` — Text input (max 500 chars)
- `num_speakers` — Number input (only shown when diarize is checked)

Wire these to the retranscribe API call's form data.

- [ ] **Step 2: Verify dialog renders**

Run: `cd frontend && npm run build`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/editor/RetranscribeDialog.tsx
git commit -m "feat(ui): add word timestamps, initial prompt, speaker count to retranscribe dialog"
```

---

## Task 12: Enhanced Status Page

**Files:**
- Modify: `frontend/src/pages/StatusPage.tsx`

- [ ] **Step 1: Enhance StatusPage with live health data**

Replace the stub with a real dashboard that consumes the health stream SSE data from `useUIStore`:

- System health status (healthy/degraded/critical) with colored indicator
- Model preload status table (model name → status)
- SSE connection status
- Component status cards (Transcription Engine, Web App, Database, File Storage)

Use the existing `useUIStore` selectors: `systemHealth`, `modelPreloadStatus`, `sseConnected`.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/StatusPage.tsx
git commit -m "feat(ui): enhance status page with live health dashboard and model status"
```

---

## Task 13: Update All UI Components for New Design Tokens

**Files:**
- Modify: `frontend/src/components/ui/Button.tsx`
- Modify: `frontend/src/components/ui/Card.tsx`
- Modify: `frontend/src/components/ui/Input.tsx`
- Modify: `frontend/src/components/ui/Badge.tsx`
- Modify: `frontend/src/components/ui/Dialog.tsx`
- Modify: `frontend/src/components/layout/Footer.tsx`

- [ ] **Step 1: Update Button — add letter-spacing and refined hover states**

In `Button.tsx`, add `tracking-[-0.011em]` to the base CVA class and ensure all variants reference CSS variables (they already do — verify).

- [ ] **Step 2: Update Card — use new shadow-sm default**

In `Card.tsx`, set `shadow` default to `true` (subtle editorial lift) and add `border-[var(--color-border)]` which adapts to dark mode.

- [ ] **Step 3: Update Dialog — ensure backdrop works in dark mode**

In `Dialog.tsx`, verify overlay uses `rgba` or a CSS variable that adapts.

- [ ] **Step 4: Update Footer — refined typography**

In `Footer.tsx`, use `text-[var(--color-text-muted)]` and add `tracking-wide` to copyright text.

- [ ] **Step 5: Build and visual check**

Run: `cd frontend && npm run build`

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ui/ frontend/src/components/layout/Footer.tsx
git commit -m "style(ui): refine all primitives for Premium Editorial tokens and dark mode"
```

---

## Task 14: Update Existing Tests & Add New Tests

**Files:**
- Modify: `frontend/src/store/__tests__/preferencesStore.test.ts`
- Modify: `frontend/src/__tests__/store/preferencesStore.test.ts`
- Create: `frontend/src/components/ui/__tests__/Switch.test.tsx`
- Create: `frontend/src/components/ui/__tests__/Slider.test.tsx`
- Create: `frontend/src/components/ui/__tests__/Tabs.test.tsx`
- Create: `frontend/src/components/ui/__tests__/ColorPicker.test.tsx`
- Create: `frontend/src/components/ui/__tests__/ThemeToggle.test.tsx`
- Create: `frontend/src/__tests__/pages/SettingsPage.test.tsx`

- [ ] **Step 1: Update preferencesStore tests**

Update both `frontend/src/store/__tests__/preferencesStore.test.ts` and `frontend/src/__tests__/store/preferencesStore.test.ts` to:
- Keep existing `setPreferredFormat` and `setMaxLineChars` tests (backward compat)
- Add tests for `setPreference('defaultModel', 'large')`, `setPreference('theme', 'dark')`, etc.
- Test `reset()` returns all new fields to defaults

- [ ] **Step 2: Run existing tests to identify breakages**

```bash
cd frontend && npm test -- --run
```

Fix any failing tests by updating expected class names or props.

- [ ] **Step 3: Add Switch test**

```tsx
// frontend/src/components/ui/__tests__/Switch.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { Switch } from '../Switch'

test('renders with label and toggles', () => {
  const onChange = vi.fn()
  render(<Switch checked={false} onChange={onChange} label="Enable feature" />)
  expect(screen.getByRole('switch')).toHaveAttribute('aria-checked', 'false')
  fireEvent.click(screen.getByRole('switch'))
  expect(onChange).toHaveBeenCalledWith(true)
})
```

- [ ] **Step 4: Add Slider test**

Test that value changes fire onChange with the number value.

- [ ] **Step 5: Add Tabs test**

Test that clicking a tab fires onChange with the correct tab id, and the active tab gets the selected aria attribute.

- [ ] **Step 6: Add ColorPicker test**

Test hex input validation (rejects non-hex strings) and color input binding.

- [ ] **Step 7: Add ThemeToggle test**

Test that clicking cycles through system → dark → light → system.

- [ ] **Step 8: Add SettingsPage test**

Render `SettingsPage`, verify 4 tabs are present, click each tab and verify the correct content renders.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/__tests__/ frontend/src/store/__tests__/ frontend/src/components/ui/__tests__/
git commit -m "test(ui): update and add tests for Premium Editorial redesign, new primitives, settings"
```

---

## Task 15: Final Build Verification & Lint

**Files:** None (verification only)

- [ ] **Step 1: Run TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```
Expected: 0 errors.

- [ ] **Step 2: Run ESLint**

```bash
cd frontend && npx eslint src/
```
Expected: 0 errors (warnings OK).

- [ ] **Step 3: Run all frontend tests**

```bash
cd frontend && npm test -- --run
```
Expected: All pass.

- [ ] **Step 4: Run production build**

```bash
cd frontend && npm run build
```
Expected: Build succeeds, dist/ generated.

- [ ] **Step 5: Run backend tests (regression check)**

```bash
cd /home/claude-user/subtitle-generator && python -m pytest tests/ -x --tb=short -q
```
Expected: All 3,667+ tests pass.

- [ ] **Step 6: Run ruff lint**

```bash
ruff check . && ruff format --check --diff .
```
Expected: Clean.

---

## Summary

| Task | What | Files Changed |
|------|------|--------------|
| 1 | Premium Editorial light tokens | index.css |
| 2 | Dark mode tokens | index.css |
| 3 | Theme toggle component | ThemeToggle.tsx, Header.tsx |
| 4 | Expanded preferences store | preferencesStore.ts |
| 5 | Theme ↔ preferences sync | useTheme.ts |
| 6 | New UI primitives | Switch, Slider, ColorPicker, Tabs |
| 7 | Settings page (4 tabs) | SettingsPage + 4 settings components, Router, navigation |
| 8 | Advanced upload options | AdvancedUploadOptions.tsx, UploadZone.tsx |
| 9 | Rich file metadata panel | FileMetadataPanel.tsx, ContextPanel.tsx |
| 10 | Custom embed styler | CustomEmbedStyler.tsx, EmbedPanel.tsx |
| 11 | Enhanced retranscribe dialog | RetranscribeDialog.tsx |
| 12 | Live status dashboard | StatusPage.tsx |
| 13 | Component styling updates | Button, Card, Dialog, Footer, etc. |
| 14 | Tests (new primitives + settings + existing updates) | 8+ test files |
| 15 | Final verification | Build, lint, test |

**Total new files:** ~14
**Total modified files:** ~20
**Estimated commits:** 15
