import { cn } from './cn'

interface DividerProps {
  label?: string
  className?: string
}

export function Divider({ label, className }: DividerProps) {
  if (label) {
    return (
      <div className={cn('flex items-center gap-3', className)} role="separator">
        <div className="flex-1 h-px bg-[var(--color-border)]" />
        <span className="text-xs text-[var(--color-text-muted)] font-medium shrink-0">{label}</span>
        <div className="flex-1 h-px bg-[var(--color-border)]" />
      </div>
    )
  }
  return <hr className={cn('border-0 h-px bg-[var(--color-border)]', className)} />
}
