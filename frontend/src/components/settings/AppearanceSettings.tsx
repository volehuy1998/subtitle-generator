/**
 * AppearanceSettings — Theme selection (light / dark / system).
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { usePreferencesStore } from '../../store/preferencesStore'
import { cn } from '../ui/cn'
import { Sun, Moon, Monitor } from 'lucide-react'

const themes = [
  { id: 'light' as const, label: 'Light', icon: Sun },
  { id: 'dark' as const, label: 'Dark', icon: Moon },
  { id: 'system' as const, label: 'System', icon: Monitor },
]

export function AppearanceSettings() {
  const { theme, setPreference } = usePreferencesStore()

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h3 className="text-sm font-semibold text-[var(--color-text)] mb-1">Appearance</h3>
        <p className="text-xs text-[var(--color-text-muted)]">
          Choose how SubForge looks to you.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {themes.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setPreference('theme', id)}
            className={cn(
              'flex flex-col items-center gap-2 rounded-lg border p-4 transition-colors',
              theme === id
                ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5 text-[var(--color-primary)]'
                : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[var(--color-border-strong)] hover:text-[var(--color-text)]'
            )}
          >
            <Icon className="h-6 w-6" />
            <span className="text-sm font-medium">{label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
