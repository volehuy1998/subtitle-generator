import { cva, type VariantProps } from 'class-variance-authority'
import { type ReactNode } from 'react'
import { cn } from './cn'

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
  {
    variants: {
      variant: {
        default: 'bg-[--color-surface-raised] text-[--color-text-secondary] border border-[--color-border]',
        success: 'bg-[--color-success-light] text-[--color-success]',
        warning: 'bg-[--color-warning-light] text-[--color-warning]',
        danger: 'bg-[--color-danger-light] text-[--color-danger]',
        info: 'bg-[--color-info-light] text-[--color-info]',
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
