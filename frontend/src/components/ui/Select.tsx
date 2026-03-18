import { forwardRef, useId, type SelectHTMLAttributes } from 'react'
import { cn } from './cn'

interface SelectOption {
  value: string
  label: string
}

interface SelectGroup {
  label: string
  options: SelectOption[]
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  helperText?: string
  options?: SelectOption[]
  groups?: SelectGroup[]
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, helperText, options, groups, id: externalId, ...props }, ref) => {
    const internalId = useId()
    const id = externalId ?? internalId
    const errorId = `${id}-error`

    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={id} className="text-sm font-medium text-[var(--color-text)]">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={id}
          className={cn(
            'w-full h-9 px-3 text-sm rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] focus:outline-none focus:border-[var(--color-border-focus)] focus:ring-1 focus:ring-[var(--color-border-focus)] transition-colors',
            error && 'border-[var(--color-danger)]',
            className
          )}
          aria-describedby={error ? errorId : undefined}
          aria-invalid={error ? 'true' : undefined}
          {...props}
        >
          {options?.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          {groups?.map(g => (
            <optgroup key={g.label} label={g.label}>
              {g.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </optgroup>
          ))}
        </select>
        {error && <p id={errorId} className="text-xs text-[var(--color-danger)]">{error}</p>}
        {helperText && !error && <p className="text-xs text-[var(--color-text-muted)]">{helperText}</p>}
      </div>
    )
  }
)

Select.displayName = 'Select'
