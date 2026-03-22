import type { EmbedMode } from '@/store/uiStore'

interface Props {
  value: EmbedMode
  onChange: (mode: EmbedMode) => void
}

const MODES: Array<{ value: EmbedMode; label: string; description: string }> = [
  {
    value: 'soft',
    label: 'Soft Mux',
    description: 'Subtitles as selectable track',
  },
  {
    value: 'hard',
    label: 'Hard Burn',
    description: 'Burned into video pixels',
  },
]

export function ModeSelector({ value, onChange }: Props) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {MODES.map((mode) => {
        const isActive = value === mode.value
        return (
          <button
            key={mode.value}
            type="button"
            onClick={() => onChange(mode.value)}
            className="flex items-start gap-2.5 p-3 rounded-lg border text-left transition-all"
            style={{
              background: isActive ? 'var(--color-primary-light)' : 'var(--color-surface)',
              borderColor: isActive ? 'var(--color-primary)' : 'var(--color-border)',
              cursor: 'pointer',
            }}
          >
            {/* Radio dot */}
            <div
              className="flex-shrink-0 w-4 h-4 rounded-full border-2 flex items-center justify-center mt-0.5"
              style={{
                borderColor: isActive ? 'var(--color-primary)' : 'var(--color-border-2)',
                background: 'transparent',
              }}
            >
              {isActive && (
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ background: 'var(--color-primary)' }}
                />
              )}
            </div>

            <div className="flex flex-col gap-0.5 min-w-0">
              <span
                className="text-xs font-semibold whitespace-nowrap"
                style={{ color: isActive ? 'var(--color-primary)' : 'var(--color-text)' }}
              >
                {mode.label}
              </span>
              <span
                className="text-xs leading-tight"
                style={{ color: 'var(--color-text-3)' }}
              >
                {mode.description}
              </span>
            </div>
          </button>
        )
      })}
    </div>
  )
}
