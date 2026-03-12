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
            className="flex items-center gap-2 px-2 py-1.5 rounded-lg border"
            style={{
              background: 'var(--color-surface)',
              borderColor: 'var(--color-border)',
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
              style={{ color: 'var(--color-text)', fontSize: '11px' }}
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
            className="flex items-center gap-2 px-2 py-1.5 rounded-lg border"
            style={{
              background: 'var(--color-surface)',
              borderColor: 'var(--color-border)',
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
              style={{ color: 'var(--color-text)', fontSize: '11px' }}
            >
              {size}px
            </span>
          </div>
        </div>
      </div>

      {/* Preview strip */}
      <div
        className="flex items-end justify-center px-4 py-3 rounded-lg overflow-hidden"
        style={{
          background: '#111827',
          minHeight: '56px',
        }}
      >
        <span
          style={{
            color: color,
            fontSize: `${Math.min(size, 28)}px`,
            fontFamily: 'sans-serif',
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
    </div>
  )
}
