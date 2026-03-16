/**
 * Badge — reusable badge/tag component with variant coloring.
 * Pure presentational, no state or side effects.
 * — Pixel (Sr. Frontend), Sprint L25
 */

import type { ReactNode } from 'react'

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info'

interface BadgeProps {
  children: ReactNode
  variant?: BadgeVariant
  size?: 'sm' | 'md'
  dot?: boolean
}

const variantStyles: Record<BadgeVariant, { bg: string; text: string }> = {
  default: { bg: 'var(--color-surface-2)', text: 'var(--color-text-2)' },
  success: { bg: 'var(--color-success-light)', text: 'var(--color-success)' },
  warning: { bg: 'var(--color-warning-light)', text: 'var(--color-warning)' },
  danger: { bg: 'var(--color-danger-light)', text: 'var(--color-danger)' },
  info: { bg: 'var(--color-primary-light)', text: 'var(--color-primary)' },
}

const sizeStyles: Record<'sm' | 'md', { fontSize: string; padding: string }> = {
  sm: { fontSize: '10px', padding: '2px 6px' },
  md: { fontSize: '12px', padding: '3px 8px' },
}

export function Badge({ children, variant = 'default', size = 'md', dot = false }: BadgeProps) {
  const colors = variantStyles[variant]
  const sizing = sizeStyles[size]

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: dot ? '5px' : undefined,
        backgroundColor: colors.bg,
        color: colors.text,
        fontSize: sizing.fontSize,
        padding: sizing.padding,
        borderRadius: '9999px',
        fontWeight: 500,
        lineHeight: 1.4,
        whiteSpace: 'nowrap',
      }}
    >
      {dot && (
        <span
          style={{
            width: size === 'sm' ? '5px' : '6px',
            height: size === 'sm' ? '5px' : '6px',
            borderRadius: '50%',
            backgroundColor: colors.text,
            flexShrink: 0,
          }}
        />
      )}
      {children}
    </span>
  )
}
