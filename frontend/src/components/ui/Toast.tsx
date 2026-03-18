import { X, CheckCircle2, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { cn } from './cn'
import type { Toast as ToastType } from '../../store/toastStore'

const typeConfig = {
  success: { icon: CheckCircle2, color: 'text-[--color-success]', bg: 'bg-[--color-success-light]' },
  error: { icon: AlertCircle, color: 'text-[--color-danger]', bg: 'bg-[--color-danger-light]' },
  warning: { icon: AlertTriangle, color: 'text-[--color-warning]', bg: 'bg-[--color-warning-light]' },
  info: { icon: Info, color: 'text-[--color-info]', bg: 'bg-[--color-info-light]' },
}

interface ToastProps {
  toast: ToastType
  onDismiss: (id: string) => void
}

export function Toast({ toast, onDismiss }: ToastProps) {
  const { icon: Icon, color } = typeConfig[toast.type]
  return (
    <div
      className={cn(
        'toast-enter flex items-start gap-3 w-80 rounded-lg border border-[--color-border] bg-[--color-surface] p-4 shadow-lg'
      )}
      role="alert"
      aria-live="assertive"
    >
      <Icon className={cn('h-5 w-5 shrink-0 mt-0.5', color)} aria-hidden="true" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-[--color-text]">{toast.title}</p>
        {toast.description && (
          <p className="text-sm text-[--color-text-secondary] mt-0.5">{toast.description}</p>
        )}
        {toast.action && (
          <button
            className="mt-2 text-sm font-medium text-[--color-primary] hover:underline"
            onClick={toast.action.onClick}
          >
            {toast.action.label}
          </button>
        )}
      </div>
      <button
        onClick={() => onDismiss(toast.id)}
        className="shrink-0 p-0.5 rounded text-[--color-text-muted] hover:text-[--color-text] hover:bg-[--color-surface-raised] transition-colors"
        aria-label="Dismiss notification"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}
