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
