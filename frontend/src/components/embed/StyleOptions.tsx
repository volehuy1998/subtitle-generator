/**
 * Phase Lumen — Subtitle style options for hard burn embedding.
 *
 * Color picker, font size slider, and a dark-background preview strip
 * that simulates how subtitles will appear over video content.
 *
 * — Prism (UI/UX Engineer) — Sprint L8
 */

interface Props {
  color: string
  size: number
  onChange: (color: string, size: number) => void
}

export function StyleOptions({ color, size, onChange }: Props) {
  return (
    <div className="flex flex-col gap-3">
      {/* Controls grid */}
      <div className="grid grid-cols-2 gap-3">
        {/* Color picker */}
        <div className="flex flex-col gap-1.5">
          <label
            className="text-xs font-medium"
            style={{ color: 'var(--color-text-2)' }}
          >
            Text Color
          </label>
          <div
            className="flex items-center gap-2.5 px-3 py-2 rounded-lg"
            style={{
              background: 'var(--color-bg)',
              border: '1px solid var(--color-border)',
            }}
          >
            <input
              type="color"
              value={color}
              onChange={(e) => onChange(e.target.value, size)}
              className="w-6 h-6 rounded cursor-pointer border-0"
              style={{ padding: 0, background: 'none' }}
            />
            <span
              className="text-xs font-mono"
              style={{ color: 'var(--color-text)', fontSize: '12px' }}
            >
              {color.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Size slider */}
        <div className="flex flex-col gap-1.5">
          <label
            className="text-xs font-medium"
            style={{ color: 'var(--color-text-2)' }}
          >
            Font Size
          </label>
          <div
            className="flex items-center gap-2.5 px-3 py-2 rounded-lg"
            style={{
              background: 'var(--color-bg)',
              border: '1px solid var(--color-border)',
            }}
          >
            <input
              type="range"
              min={12}
              max={56}
              step={2}
              value={size}
              onChange={(e) => onChange(color, Number(e.target.value))}
              className="flex-1 h-1 rounded-full appearance-none cursor-pointer"
              style={{ accentColor: 'var(--color-primary)' }}
            />
            <span
              className="text-xs font-mono tabular-nums flex-shrink-0 w-8 text-right"
              style={{ color: 'var(--color-text)', fontSize: '12px' }}
            >
              {size}px
            </span>
          </div>
        </div>
      </div>

      {/* Preview strip — dark background simulates video content for accurate
          subtitle color preview on light-themed UI — Prism (UI/UX Engineer) */}
      <div
        className="flex items-end justify-center px-4 py-4 rounded-lg overflow-hidden"
        style={{
          background: '#1E293B',
          minHeight: '64px',
          border: '1px solid var(--color-border)',
        }}
      >
        <span
          style={{
            color: color,
            fontSize: `${Math.min(size, 28)}px`,
            fontFamily: 'var(--font-family-sans)',
            fontWeight: 500,
            textShadow: '0 1px 4px rgba(0,0,0,0.8)',
            lineHeight: 1.3,
            textAlign: 'center',
            display: 'block',
          }}
        >
          Sample subtitle text
        </span>
      </div>
      <p className="text-xs" style={{ color: 'var(--color-text-3)', margin: 0 }}>
        Preview shows how subtitles will appear over video content
      </p>
    </div>
  )
}
