import { CheckCircle2, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { type ReactNode } from 'react'
import { cn } from './cn'

const typeConfig = {
  success: { icon: CheckCircle2, color: 'text-[--color-success]', bg: 'bg-[--color-success-light]', border: 'border-[--color-success]' },
  error: { icon: AlertCircle, color: 'text-[--color-danger]', bg: 'bg-[--color-danger-light]', border: 'border-[--color-danger]' },
  warning: { icon: AlertTriangle, color: 'text-[--color-warning]', bg: 'bg-[--color-warning-light]', border: 'border-[--color-warning]' },
  info: { icon: Info, color: 'text-[--color-info]', bg: 'bg-[--color-info-light]', border: 'border-[--color-info]' },
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
        {title && <p className="text-sm font-medium text-[--color-text]">{title}</p>}
        {children && <div className="text-sm text-[--color-text-secondary] mt-1">{children}</div>}
        {action && <div className="mt-3">{action}</div>}
      </div>
    </div>
  )
}
