import { forwardRef, useId, type InputHTMLAttributes } from 'react'
import { cn } from './cn'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: React.ReactNode
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, leftIcon, id: externalId, ...props }, ref) => {
    const internalId = useId()
    const id = externalId ?? internalId
    const errorId = `${id}-error`
    const helperId = `${id}-helper`

    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={id} className="text-sm font-medium text-[var(--color-text)]">
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]">
              {leftIcon}
            </span>
          )}
          <input
            ref={ref}
            id={id}
            className={cn(
              'w-full h-9 px-3 text-sm rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-border-focus)] focus:ring-1 focus:ring-[var(--color-border-focus)] transition-colors',
              leftIcon && 'pl-9',
              error && 'border-[var(--color-danger)] focus:border-[var(--color-danger)] focus:ring-[var(--color-danger)]',
              className
            )}
            aria-describedby={cn(error ? errorId : undefined, helperText ? helperId : undefined) || undefined}
            aria-invalid={error ? 'true' : undefined}
            {...props}
          />
        </div>
        {error && (
          <p id={errorId} className="text-xs text-[var(--color-danger)]">{error}</p>
        )}
        {helperText && !error && (
          <p id={helperId} className="text-xs text-[var(--color-text-muted)]">{helperText}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'
