/**
 * ThemeToggle — cycles through light / dark / system themes.
 *
 * Compact 32px icon button that shows the current theme mode.
 * Clicking cycles: system -> dark -> light -> system.
 *
 * — Pixel (Sr. Frontend Engineer), Task 3
 */

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
