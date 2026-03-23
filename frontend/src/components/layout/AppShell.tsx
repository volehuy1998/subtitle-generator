/**
 * AppShell — Drop, See, Refine outer layout wrapper.
 *
 * Provides the full-viewport flex column with sticky Header, scrollable
 * main content area, and Footer. Includes a skip-navigation link for
 * keyboard and screen reader accessibility (WCAG 2.4.1).
 *
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { type ReactNode } from 'react'
import { Header } from './Header'
import { Footer } from './Footer'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen flex flex-col bg-[var(--color-bg)]">
      {/* Skip navigation for accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[var(--color-primary)] focus:text-white focus:rounded-md focus:shadow-lg"
      >
        Skip to main content
      </a>
      <Header />
      <main
        id="main-content"
        className="flex-1 w-full max-w-[1280px] mx-auto px-4 py-6"
      >
        {children}
      </main>
      <Footer />
    </div>
  )
}
