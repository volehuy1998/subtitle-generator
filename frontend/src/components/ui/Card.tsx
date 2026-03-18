import { type HTMLAttributes, type ReactNode } from 'react'
import { cn } from './cn'

interface CardHeaderProps {
  title: string
  subtitle?: string
  action?: ReactNode
}

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padding?: 'sm' | 'md' | 'lg' | 'none'
  shadow?: boolean
  border?: boolean
  header?: CardHeaderProps
}

const paddingMap = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
}

export function Card({ className, padding = 'md', shadow = false, border = true, header, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-lg bg-[var(--color-surface)]',
        border && 'border border-[var(--color-border)]',
        shadow && 'shadow-md',
        paddingMap[padding],
        className
      )}
      {...props}
    >
      {header && (
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-[var(--color-text)]">{header.title}</h3>
            {header.subtitle && (
              <p className="text-xs text-[var(--color-text-secondary)] mt-0.5">{header.subtitle}</p>
            )}
          </div>
          {header.action && <div className="ml-4 shrink-0">{header.action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
