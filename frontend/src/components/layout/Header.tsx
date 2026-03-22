/**
 * Header — Editorial sticky navigation bar.
 *
 * Backport of the Premium Editorial header to the Lumen production build.
 * Sticky 56px bar with SubForge logo (left), nav pills (center-right),
 * gear icon (PreferencesPanel), and health indicator dot.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { useState, useEffect } from 'react'
import { navigate } from '../../navigation'
import { useUIStore } from '@/store/uiStore'
import { PreferencesPanel } from '@/components/settings/PreferencesPanel'
import type { HealthStatus } from '@/api/types'

function GearIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="3"/>
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
    </svg>
  )
}

function HealthDot({ status }: { status: HealthStatus['status'] | null }) {
  const bg =
    status === 'ok' || status === 'healthy' ? 'var(--color-success)' :
    status === 'degraded' || status === 'warning' ? 'var(--color-warning)' :
    status === 'error' || status === 'critical' ? 'var(--color-danger)' :
    'var(--color-border-2)'

  const label =
    status === 'ok' || status === 'healthy' ? 'Healthy' :
    status === 'degraded' || status === 'warning' ? 'Degraded' :
    status === 'error' || status === 'critical' ? 'Error' :
    'Connecting'

  return (
    <span
      className={`inline-block w-2 h-2 rounded-full flex-shrink-0 ${status === null || status === 'error' || status === 'critical' ? 'animate-pulse' : ''}`}
      style={{ background: bg }}
      title={label}
      role="img"
      aria-label={`System status: ${label}`}
    />
  )
}

export function Header() {
  const { healthPanelOpen, setHealthPanelOpen, health } = useUIStore()
  const [prefsOpen, setPrefsOpen] = useState(false)

  // Track current path for active nav highlighting (same pattern as old AppHeader)
  const [currentPath, setCurrentPath] = useState(
    typeof window !== 'undefined' ? window.location.pathname : '/'
  )
  useEffect(() => {
    const onNav = () => setCurrentPath(window.location.pathname)
    window.addEventListener('spa-navigate', onNav)
    window.addEventListener('popstate', onNav)
    return () => {
      window.removeEventListener('spa-navigate', onNav)
      window.removeEventListener('popstate', onNav)
    }
  }, [])

  const navLinks = [
    { href: '/status', label: 'Status' },
    { href: '/about', label: 'About' },
  ]

  return (
    <header
      data-testid="app-header"
      className="sticky top-0 z-40 h-14 bg-[var(--color-surface)] border-b border-[var(--color-border)] shadow-sm"
    >
      <div className="h-full max-w-[1280px] mx-auto px-4 flex items-center justify-between">
        {/* Logo */}
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 font-semibold text-[var(--color-text)] hover:text-[var(--color-primary)] transition-colors"
          aria-label="SubForge home"
        >
          <svg viewBox="0 0 48 46" fill="none" className="h-5 w-5" aria-hidden="true">
            <path d="M25.946 44.938c-.664.845-2.021.375-2.021-.698V33.937a2.26 2.26 0 0 0-2.262-2.262H10.287c-.92 0-1.456-1.04-.92-1.788l7.48-10.471c1.07-1.497 0-3.578-1.842-3.578H1.237c-.92 0-1.456-1.04-.92-1.788L10.013.474c.214-.297.556-.474.92-.474h28.894c.92 0 1.456 1.04.92 1.788l-7.48 10.471c-1.07 1.498 0 3.579 1.842 3.579h11.377c.943 0 1.473 1.088.89 1.83L25.947 44.94z" fill="var(--color-primary)"/>
          </svg>
          <span>SubForge</span>
        </button>

        {/* Nav */}
        <nav className="flex items-center gap-1" aria-label="Main navigation">
          {navLinks.map(({ href, label }) => (
            <button
              key={href}
              onClick={() => navigate(href)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                currentPath === href
                  ? 'text-[var(--color-primary)] bg-[var(--color-primary-light)] font-medium'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]'
              }`}
            >
              {label}
            </button>
          ))}

          {/* Gear icon — opens PreferencesPanel */}
          <button
            type="button"
            onClick={() => setPrefsOpen(true)}
            aria-label="Open preferences"
            title="Preferences"
            className="flex items-center justify-center h-8 w-8 rounded-md text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition-colors"
          >
            <GearIcon />
          </button>

          {/* Health dot — click toggles HealthPanel */}
          <button
            type="button"
            onClick={() => setHealthPanelOpen(!healthPanelOpen)}
            className={`flex items-center justify-center h-8 w-8 rounded-md transition-colors ${
              healthPanelOpen ? 'bg-[var(--color-surface-raised)]' : 'hover:bg-[var(--color-surface-raised)]'
            }`}
            aria-label="Toggle health panel"
          >
            <HealthDot status={health?.status ?? null} />
          </button>
        </nav>
      </div>

      {/* Preferences panel */}
      <PreferencesPanel open={prefsOpen} onClose={() => setPrefsOpen(false)} />
    </header>
  )
}
