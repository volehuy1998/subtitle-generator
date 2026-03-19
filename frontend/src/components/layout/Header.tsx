/**
 * Header — Drop, See, Refine sticky top navigation bar.
 *
 * Sticky 56px bar with SubForge logo (left) and nav links (right).
 * Active page link is highlighted using the primary brand colour.
 * HealthIndicator placeholder will be added in Task 36.
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { navigate } from '../../navigation'
import { useUIStore } from '../../store/uiStore'
import { HealthIndicator } from '../system/HealthIndicator'
import { ThemeToggle } from '../ui/ThemeToggle'

export function Header() {
  const currentPage = useUIStore((s) => s.currentPage)

  return (
    <header data-testid="app-header" className="sticky top-0 z-40 h-14 bg-[var(--color-surface)] border-b border-[var(--color-border)] shadow-sm">
      <div className="h-full max-w-[1280px] mx-auto px-4 flex items-center justify-between">
        {/* Logo */}
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 font-semibold text-[var(--color-text)] hover:text-[var(--color-primary)] transition-colors"
          aria-label="SubForge home"
        >
          <svg viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5 text-[var(--color-primary)]">
            <path d="M14.5 2.5c0 1.5-1.5 3-3.5 4s-4 1.5-5.5 1.5c0-1.5 1.5-3 3.5-4S13 2.5 14.5 2.5z"/>
            <path d="M4 8C2.5 9.5 2 11 2 12s.5 2.5 2 4c1 1 2 1.5 3 1.5V15c-.5 0-1-.3-2-1.2C3.5 12.5 3 11.5 3 11s.5-1.5 1.5-2.8L4 8z"/>
            <rect x="7" y="14" width="10" height="2" rx="1"/>
            <rect x="5" y="17" width="14" height="2" rx="1"/>
            <rect x="9" y="20" width="6" height="2" rx="1"/>
          </svg>
          <span>SubForge</span>
        </button>

        {/* Nav */}
        <nav className="flex items-center gap-1" aria-label="Main navigation">
          {[
            { href: '/status', label: 'Status' },
            { href: '/settings', label: 'Settings' },
            { href: '/about', label: 'About' },
          ].map(({ href, label }) => (
            <button
              key={href}
              onClick={() => navigate(href)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                currentPage === href
                  ? 'text-[var(--color-primary)] bg-[var(--color-primary-light)] font-medium'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]'
              }`}
            >
              {label}
            </button>
          ))}
          <ThemeToggle />
          <HealthIndicator />
        </nav>
      </div>
    </header>
  )
}
