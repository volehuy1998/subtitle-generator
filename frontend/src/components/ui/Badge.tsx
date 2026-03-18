import { cva, type VariantProps } from 'class-variance-authority'
import { type ReactNode } from 'react'
import { cn } from './cn'

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
  {
    variants: {
      variant: {
        default: 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] border border-[var(--color-border)]',
        success: 'bg-[var(--color-success-light)] text-[var(--color-success)]',
        warning: 'bg-[var(--color-warning-light)] text-[var(--color-warning)]',
        danger: 'bg-[var(--color-danger-light)] text-[var(--color-danger)]',
        info: 'bg-[var(--color-info-light)] text-[var(--color-info)]',
      },
    },
    defaultVariants: { variant: 'default' },
  }
)

interface BadgeProps extends VariantProps<typeof badgeVariants> {
  children: ReactNode
  dot?: boolean
  className?: string
}

export function Badge({ variant, children, dot = false, className }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)}>
      {dot && (
        <span className="h-1.5 w-1.5 rounded-full bg-current shrink-0" aria-hidden="true" />
      )}
      {children}
    </span>
  )
}
