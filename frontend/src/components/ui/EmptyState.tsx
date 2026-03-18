import { type ReactNode } from 'react'
import { cn } from './cn'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      {icon && (
        <div className="mb-4 text-[--color-text-muted] animate-fade-in">
          {icon}
        </div>
      )}
      <h3 className="text-sm font-semibold text-[--color-text]">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-[--color-text-secondary] max-w-sm">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
