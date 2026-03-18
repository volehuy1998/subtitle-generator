import { CheckCircle2, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { type ReactNode } from 'react'
import { cn } from './cn'

const typeConfig = {
  success: { icon: CheckCircle2, color: 'text-[var(--color-success)]', bg: 'bg-[var(--color-success-light)]', border: 'border-[var(--color-success)]' },
  error: { icon: AlertCircle, color: 'text-[var(--color-danger)]', bg: 'bg-[var(--color-danger-light)]', border: 'border-[var(--color-danger)]' },
  warning: { icon: AlertTriangle, color: 'text-[var(--color-warning)]', bg: 'bg-[var(--color-warning-light)]', border: 'border-[var(--color-warning)]' },
  info: { icon: Info, color: 'text-[var(--color-info)]', bg: 'bg-[var(--color-info-light)]', border: 'border-[var(--color-info)]' },
}

interface AlertProps {
  type?: 'success' | 'error' | 'warning' | 'info'
  title?: string
  action?: ReactNode
  children?: ReactNode
  className?: string
}

export function Alert({ type = 'info', title, action, children, className }: AlertProps) {
  const { icon: Icon, color, bg, border } = typeConfig[type]
  return (
    <div
      role="alert"
      className={cn(
        'rounded-lg border p-4 flex items-start gap-3',
        bg, border, className
      )}
    >
      <Icon className={cn('h-5 w-5 shrink-0 mt-0.5', color)} aria-hidden="true" />
      <div className="flex-1 min-w-0">
        {title && <p className="text-sm font-medium text-[var(--color-text)]">{title}</p>}
        {children && <div className="text-sm text-[var(--color-text-secondary)] mt-1">{children}</div>}
        {action && <div className="mt-3">{action}</div>}
      </div>
    </div>
  )
}
