# Phase Lumen — Design System

> **Version:** 2.0 · **Owner:** Pixel (Sr. Frontend Engineer) · **Reference:** Microsoft 365, Claude AI, Google Workspace

---

## Color Palette

### Core Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-bg` | `#FFFFFF` | Page background |
| `--color-surface` | `#F8FAFC` | Card/panel backgrounds |
| `--color-surface-2` | `#F1F5F9` | Elevated surfaces, hover states |
| `--color-border` | `#E2E8F0` | Subtle borders |
| `--color-border-2` | `#CBD5E1` | Emphasis borders |
| `--color-text` | `#0F172A` | Primary text (slate-900) |
| `--color-text-2` | `#475569` | Secondary text (slate-600) |
| `--color-text-3` | `#94A3B8` | Muted text (slate-400) |

### Brand Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-primary` | `#6366F1` | Primary actions (indigo-500) |
| `--color-primary-hover` | `#4F46E5` | Hover state (indigo-600) |
| `--color-primary-light` | `rgba(99,102,241,0.08)` | Primary tint backgrounds |
| `--color-primary-border` | `rgba(99,102,241,0.20)` | Primary tint borders |

### Status Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-success` | `#10B981` | Success states (emerald-500) |
| `--color-success-light` | `rgba(16,185,129,0.08)` | Success backgrounds |
| `--color-warning` | `#F59E0B` | Warnings (amber-500) |
| `--color-warning-light` | `rgba(245,158,11,0.08)` | Warning backgrounds |
| `--color-danger` | `#EF4444` | Errors (red-500) |
| `--color-danger-light` | `rgba(239,68,68,0.08)` | Error backgrounds |

### Design Principles

1. **White backgrounds** — clean, professional, enterprise-grade
2. **Subtle gray for depth** — surface colors create hierarchy without heaviness
3. **Indigo as brand** — distinctive but professional (used by Linear, Vercel, Stripe)
4. **No dark mode** — Phase Lumen is explicitly light-only per investor direction
5. **Shadows for depth** — light, soft shadows instead of heavy borders

---

## Typography

| Element | Font | Weight | Size | Color |
|---------|------|--------|------|-------|
| H1 | Inter | 700 | 32px | slate-900 |
| H2 | Inter | 600 | 24px | slate-900 |
| H3 | Inter | 600 | 20px | slate-900 |
| Body | Inter | 400 | 16px | slate-600 |
| Small | Inter | 400 | 14px | slate-500 |
| Caption | Inter | 500 | 12px | slate-400 |
| Mono | JetBrains Mono | 400 | 14px | slate-700 |

**Font loading:**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

---

## Spacing

Base unit: 4px (`0.25rem`)

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Tight inline spacing |
| sm | 8px | Component padding |
| md | 16px | Section spacing |
| lg | 24px | Card padding |
| xl | 32px | Section gaps |
| 2xl | 48px | Page-level spacing |

---

## Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgb(0 0 0 / 0.05)` | Buttons, inputs |
| `--shadow-md` | `0 4px 6px rgb(0 0 0 / 0.07), 0 2px 4px rgb(0 0 0 / 0.06)` | Cards, panels |
| `--shadow-lg` | `0 10px 15px rgb(0 0 0 / 0.10), 0 4px 6px rgb(0 0 0 / 0.05)` | Modals, dropdowns |

---

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-xs` | 4px | Small elements (tags, badges) |
| `--radius-sm` | 6px | Buttons, inputs |
| `--radius` | 8px | Cards |
| `--radius-lg` | 12px | Panels, modals |
| `--radius-xl` | 16px | Hero sections |

---

## Component Patterns

### Buttons

| Type | Background | Text | Border | Shadow |
|------|-----------|------|--------|--------|
| Primary | indigo-500 | white | none | shadow-sm |
| Secondary | white | slate-700 | slate-200 | shadow-sm |
| Ghost | transparent | slate-600 | none | none |
| Danger | red-500 | white | none | shadow-sm |

### Cards

```css
background: var(--color-surface);
border: 1px solid var(--color-border);
border-radius: var(--radius);
box-shadow: var(--shadow-md);
padding: 24px;
```

### Inputs

```css
background: white;
border: 1px solid var(--color-border);
border-radius: var(--radius-sm);
padding: 10px 14px;
font-size: 16px;
color: var(--color-text);
transition: border-color 0.15s;
/* Focus state: */
border-color: var(--color-primary);
box-shadow: 0 0 0 3px var(--color-primary-light);
```

---

## Component Library

All reusable UI components live in `frontend/src/components/ui/`. Each component follows the design tokens defined above and supports consistent sizing, spacing, and color usage.

| Component | File | Description |
|-----------|------|-------------|
| **Badge** | `Badge.tsx` | Status labels and tags with color variants (success, warning, danger, neutral). Uses `--radius-xs` for compact pill shape. |
| **Button** | `Button.tsx` | Primary, secondary, ghost, and danger variants. Supports disabled state, loading spinner, and icon slots. |
| **Card** | `Card.tsx` | Container with surface background, border, and shadow. Supports header, body, and footer slots. |
| **Dialog** | `Dialog.tsx` | Modal overlay with backdrop, title, body, and action buttons. Confirmation dialogs use this as base. |
| **Icon** | `Icon.tsx` | SVG icon wrapper with consistent sizing (sm/md/lg) and color inheritance from parent text color. |
| **Input** | `Input.tsx` | Text input with label, placeholder, error state, and focus ring. Integrates with form validation. |
| **Select** | `Select.tsx` | Dropdown select with custom styling matching Input. Supports option groups and disabled state. |
| **Skeleton** | `Skeleton.tsx` | Loading placeholder with pulse animation. Available as line, circle, and rectangle variants. |
| **StatusIndicator** | `StatusIndicator.tsx` | Colored dot indicator for health/connection status (healthy, warning, critical, unknown). |
| **ToastContainer** | `ToastContainer.tsx` | Notification toast system with auto-dismiss. Supports success, error, warning, and info types. |
| **Tooltip** | `Tooltip.tsx` | Hover-triggered tooltip with configurable placement (top, bottom, left, right). |

**Utility:**

| File | Description |
|------|-------------|
| `cn.ts` | Class name merge utility (combines Tailwind classes with conflict resolution). |

---

## Dark Mode Color Tokens

While Phase Lumen is light-first by design, dark mode tokens are defined for future use and for components that render in dark contexts (e.g., code blocks, terminal output).

| Token | Light Value | Dark Value | Usage |
|-------|-------------|------------|-------|
| `--color-bg` | `#FFFFFF` | `#0F172A` | Page background |
| `--color-surface` | `#F8FAFC` | `#1E293B` | Card/panel backgrounds |
| `--color-surface-2` | `#F1F5F9` | `#334155` | Elevated surfaces |
| `--color-border` | `#E2E8F0` | `#334155` | Subtle borders |
| `--color-border-2` | `#CBD5E1` | `#475569` | Emphasis borders |
| `--color-text` | `#0F172A` | `#F8FAFC` | Primary text |
| `--color-text-2` | `#475569` | `#CBD5E1` | Secondary text |
| `--color-text-3` | `#94A3B8` | `#64748B` | Muted text |

Dark mode is toggled via a `data-theme="dark"` attribute on the root `<html>` element. All design tokens resolve through CSS custom properties, so switching themes requires no component changes.
