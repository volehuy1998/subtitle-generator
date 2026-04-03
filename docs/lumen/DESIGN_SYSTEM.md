# Phase Lumen — Design System

**Version:** 2.0 | **Owner:** Pixel | **References:** Microsoft 365, Claude AI, Google Workspace

## Design Principles

1. **White backgrounds** — clean, professional, enterprise-grade
2. **Subtle gray for depth** — surface colors create hierarchy
3. **Indigo as brand** — distinctive but professional
4. **Light-only** — no dark mode per investor direction
5. **Soft shadows** — depth through shadows, not heavy borders

## Colors

### Core

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-bg` | `#FFFFFF` | Page background |
| `--color-surface` | `#F8FAFC` | Card/panel backgrounds |
| `--color-surface-2` | `#F1F5F9` | Elevated surfaces, hover |
| `--color-border` | `#E2E8F0` | Subtle borders |
| `--color-text` | `#0F172A` | Primary text |
| `--color-text-2` | `#475569` | Secondary text |
| `--color-text-3` | `#94A3B8` | Muted text |

### Brand

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-primary` | `#6366F1` | Primary actions |
| `--color-primary-hover` | `#4F46E5` | Hover state |
| `--color-primary-light` | `rgba(99,102,241,0.08)` | Tint backgrounds |

### Status

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-success` | `#10B981` | Success |
| `--color-warning` | `#F59E0B` | Warnings |
| `--color-danger` | `#EF4444` | Errors |

## Typography

| Element | Font | Weight | Size |
|---------|------|--------|------|
| H1 | Inter | 700 | 32px |
| H2 | Inter | 600 | 24px |
| H3 | Inter | 600 | 20px |
| Body | Inter | 400 | 16px |
| Small | Inter | 400 | 14px |
| Mono | JetBrains Mono | 400 | 14px |

## Spacing

Base unit: 4px. Scale: xs(4) sm(8) md(16) lg(24) xl(32) 2xl(48).

## Shadows

| Token | Value |
|-------|-------|
| `--shadow-sm` | `0 1px 2px rgb(0 0 0 / 0.05)` |
| `--shadow-md` | `0 4px 6px rgb(0 0 0 / 0.07)` |
| `--shadow-lg` | `0 10px 15px rgb(0 0 0 / 0.10)` |

## Border Radius

xs(4px) sm(6px) default(8px) lg(12px) xl(16px)

## Components

### Buttons
Primary (indigo-500/white), Secondary (white/slate-700), Ghost (transparent/slate-600), Danger (red-500/white). All use `--shadow-sm`.

### Cards
`background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 8px; box-shadow: var(--shadow-md); padding: 24px;`

### Inputs
White background, border on focus transitions to `--color-primary` with `0 0 0 3px var(--color-primary-light)` ring.

## Component Library

All in `frontend/src/components/ui/`:

| Component | Description |
|-----------|-------------|
| Badge | Status labels with color variants |
| Button | Primary/secondary/ghost/danger variants |
| Card | Surface container with header/body/footer |
| Dialog | Modal overlay with actions |
| Icon | SVG wrapper with consistent sizing |
| Input | Text input with label and error state |
| Select | Styled dropdown matching Input |
| Skeleton | Loading placeholder with pulse |
| StatusIndicator | Health dot (healthy/warning/critical) |
| ToastContainer | Notification toasts with auto-dismiss |
| Tooltip | Hover tooltip with placement options |
| cn.ts | Tailwind class merge utility |
