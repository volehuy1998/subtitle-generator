import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from './cn'

const iconButtonVariants = cva(
  'inline-flex items-center justify-center rounded-md transition-colors focus-ring disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        primary: 'bg-[--color-primary] text-white hover:bg-[--color-primary-hover]',
        secondary: 'bg-[--color-surface] text-[--color-text-secondary] border border-[--color-border] hover:bg-[--color-surface-raised] hover:text-[--color-text]',
        ghost: 'text-[--color-text-secondary] hover:bg-[--color-surface-raised] hover:text-[--color-text]',
        danger: 'text-[--color-danger] hover:bg-[--color-danger-light]',
        success: 'text-[--color-success] hover:bg-[--color-success-light]',
      },
      size: {
        sm: 'h-7 w-7',
        md: 'h-9 w-9',
        lg: 'h-11 w-11',
      },
    },
    defaultVariants: {
      variant: 'ghost',
      size: 'md',
    },
  }
)

export interface IconButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof iconButtonVariants> {
  icon: ReactNode
  'aria-label': string
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, variant, size, icon, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(iconButtonVariants({ variant, size }), className)}
        {...props}
      >
        {icon}
      </button>
    )
  }
)

IconButton.displayName = 'IconButton'
