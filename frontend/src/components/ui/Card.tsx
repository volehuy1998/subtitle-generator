/**
 * Card — presentational container with variant styling.
 * Supports title/subtitle header, padding sizes, and three visual variants.
 * — Pixel (Sr. Frontend), Sprint L34
 */

import type { CSSProperties, ReactNode } from 'react'
import { cn } from './cn'

type CardVariant = 'default' | 'bordered' | 'elevated'
type CardPadding = 'sm' | 'md' | 'lg'

interface CardProps {
  children: ReactNode
  title?: string
  subtitle?: string
  padding?: CardPadding
  variant?: CardVariant
  className?: string
}

const paddingValues: Record<CardPadding, string> = {
  sm: '12px',
  md: '16px',
  lg: '24px',
}

const variantStyles: Record<CardVariant, CSSProperties> = {
  default: {
    background: 'var(--color-surface)',
    border: 'none',
    boxShadow: 'none',
  },
  bordered: {
    background: 'var(--color-bg)',
    border: '1px solid var(--color-border)',
    boxShadow: 'none',
  },
  elevated: {
    background: 'var(--color-bg)',
    border: 'none',
    boxShadow: 'var(--shadow-md)',
  },
}

export function Card({
  children,
  title,
  subtitle,
  padding = 'md',
  variant = 'default',
  className,
}: CardProps) {
  const style: CSSProperties = {
    ...variantStyles[variant],
    padding: paddingValues[padding],
    borderRadius: 'var(--radius)',
  }

  return (
    <div className={cn('card', className)} style={style}>
      {title && (
        <div style={{ marginBottom: subtitle ? '4px' : '12px' }}>
          <div
            style={{
              fontSize: '16px',
              fontWeight: 600,
              color: 'var(--color-text)',
              lineHeight: 1.4,
            }}
          >
            {title}
          </div>
          {subtitle && (
            <div
              style={{
                fontSize: '13px',
                color: 'var(--color-text-3)',
                lineHeight: 1.4,
                marginTop: '2px',
                marginBottom: '12px',
              }}
            >
              {subtitle}
            </div>
          )}
        </div>
      )}
      {children}
    </div>
  )
}
