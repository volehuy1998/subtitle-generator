/**
 * PageLayout — Drop, See, Refine wrapper for static content pages.
 *
 * Provides a constrained max-width column with a heading + optional
 * subtitle above the page content. Used by About, Contact, Security,
 * and Status pages.
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { type ReactNode } from 'react'
import { cn } from '../ui/cn'

interface PageLayoutProps {
  title: string
  subtitle?: string
  children: ReactNode
  className?: string
}

export function PageLayout({ title, subtitle, children, className }: PageLayoutProps) {
  return (
    <div className={cn('max-w-2xl mx-auto', className)}>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[var(--color-text)]">{title}</h1>
        {subtitle && (
          <p className="mt-2 text-[var(--color-text-secondary)]">{subtitle}</p>
        )}
      </div>
      {children}
    </div>
  )
}
