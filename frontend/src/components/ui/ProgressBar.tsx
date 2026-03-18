import { cn } from './cn'

interface ProgressBarProps {
  value?: number        // 0-100; if undefined → indeterminate
  label?: string
  showPercent?: boolean
  className?: string
}

export function ProgressBar({ value, label, showPercent = false, className }: ProgressBarProps) {
  const isIndeterminate = value === undefined

  return (
    <div className={cn('w-full', className)}>
      {(label || showPercent) && (
        <div className="flex justify-between items-center mb-1">
          {label && <span className="text-xs font-medium text-[--color-text-secondary]">{label}</span>}
          {showPercent && !isIndeterminate && (
            <span className="text-xs text-[--color-text-muted]">{Math.round(value!)}%</span>
          )}
        </div>
      )}
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={isIndeterminate ? undefined : value}
        aria-label={label}
        className="h-1.5 w-full rounded-full bg-[--color-surface-raised] overflow-hidden"
      >
        {isIndeterminate ? (
          <div className="h-full w-1/3 rounded-full bg-[--color-primary] animate-[indeterminate_1.5s_ease-in-out_infinite]" />
        ) : (
          <div
            className="h-full rounded-full bg-[--color-primary] transition-[width] duration-300 ease-out"
            style={{ width: `${Math.min(100, Math.max(0, value!))}%` }}
          />
        )}
      </div>
    </div>
  )
}
