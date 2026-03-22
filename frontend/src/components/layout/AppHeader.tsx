/**
 * Phase Lumen — Redesigned header (Sprint L8).
 *
 * White background, subtle bottom border. Logo left, nav center, health dot right.
 * Active page underlined in brand color. GPU badge removed per spec.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { useState, useEffect } from 'react'
import { useUIStore } from '@/store/uiStore'
import { useTheme } from '@/hooks/useTheme'
import { PreferencesPanel } from '@/components/settings/PreferencesPanel'
import type { Theme } from '@/hooks/useTheme'
import type { HealthStatus } from '@/api/types'

/** Sun icon — shown in dark mode (click to go light) — Pixel (Sr. Frontend), Sprint L30 */
function SunIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="5"/>
      <line x1="12" y1="1" x2="12" y2="3"/>
      <line x1="12" y1="21" x2="12" y2="23"/>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
      <line x1="1" y1="12" x2="3" y2="12"/>
      <line x1="21" y1="12" x2="23" y2="12"/>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
    </svg>
  )
}

/** Moon icon — shown in light mode (click to go dark) — Pixel (Sr. Frontend), Sprint L30 */
function MoonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  )
}

/** Monitor icon — shown in system mode — Pixel (Sr. Frontend), Sprint L30 */
function MonitorIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
      <line x1="8" y1="21" x2="16" y2="21"/>
      <line x1="12" y1="17" x2="12" y2="21"/>
    </svg>
  )
}

function ThemeIcon({ theme }: { theme: Theme }) {
  if (theme === 'dark') return <SunIcon />
  if (theme === 'light') return <MoonIcon />
  return <MonitorIcon />
}

const themeLabels: Record<Theme, string> = {
  system: 'System theme',
  dark: 'Dark mode (click for light)',
  light: 'Light mode (click for system)',
}

function HealthDot({ status }: { status: HealthStatus['status'] | null }) {
  if (status === 'ok' || status === 'healthy') return (
    <span
      className="inline-block w-2 h-2 rounded-full"
      style={{ background: 'var(--color-success)' }}
    />
  )
  if (status === 'degraded' || status === 'warning') return (
    <span
      className="inline-block w-2 h-2 rounded-full"
      style={{ background: 'var(--color-warning)' }}
    />
  )
  if (status === 'error' || status === 'critical') return (
    <span
      className="inline-block w-2 h-2 rounded-full animate-pulse"
      style={{ background: 'var(--color-danger)' }}
    />
  )
  // null = loading
  return (
    <span
      className="inline-block w-2 h-2 rounded-full animate-pulse"
      style={{ background: 'var(--color-border-2)' }}
    />
  )
}

/** Gear icon for settings — Pixel (Sr. Frontend), Sprint L47 */
function GearIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="3"/>
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
    </svg>
  )
}

export function AppHeader() {
  const { healthPanelOpen, setHealthPanelOpen, health } = useUIStore()
  const { theme, cycleTheme } = useTheme()
  const [prefsOpen, setPrefsOpen] = useState(false)

  // Re-render on SPA navigation so active link underline stays correct
  const [currentPath, setCurrentPath] = useState(typeof window !== 'undefined' ? window.location.pathname : '/')
  useEffect(() => {
    const onNav = () => setCurrentPath(window.location.pathname)
    window.addEventListener('spa-navigate', onNav)
    window.addEventListener('popstate', onNav)
    return () => {
      window.removeEventListener('spa-navigate', onNav)
      window.removeEventListener('popstate', onNav)
    }
  }, [])

  const isOk = health?.status === 'ok' || health?.status === 'healthy'
  const isWarn = health?.status === 'degraded' || health?.status === 'warning'
  const isCrit = health?.status === 'error' || health?.status === 'critical'

  const statusLabel =
    health === null ? 'Connecting' :
    isOk ? 'Healthy' :
    isWarn ? 'Degraded' :
    isCrit ? 'Error' :
    'Unknown'

  const labelColor =
    isOk ? 'var(--color-success)' :
    isWarn ? 'var(--color-warning)' :
    isCrit ? 'var(--color-danger)' :
    'var(--color-text-3)'

  const navLinks = [
    { href: '/', label: 'App' },
    { href: '/status', label: 'Status' },
    { href: '/about', label: 'About' },
  ]

  return (
    <header
      className="sticky top-0 z-40 flex items-center px-3 sm:px-6"
      style={{
        height: '52px',
        background: 'var(--color-bg)',
        borderBottom: '1px solid var(--color-border)',
      }}
    >
      {/* Logo + Wordmark — left */}
      <a
        href="/"
        onClick={(e) => { e.preventDefault(); if (window.location.pathname !== '/') { history.pushState(null, '', '/'); window.dispatchEvent(new Event('spa-navigate')) } }}
        className="flex items-center gap-2 flex-shrink-0"
        style={{ textDecoration: 'none', cursor: 'pointer' }}
      >
        <svg width="20" height="20" viewBox="0 0 48 46" fill="none" aria-hidden="true">
          <path d="M25.946 44.938c-.664.845-2.021.375-2.021-.698V33.937a2.26 2.26 0 0 0-2.262-2.262H10.287c-.92 0-1.456-1.04-.92-1.788l7.48-10.471c1.07-1.497 0-3.578-1.842-3.578H1.237c-.92 0-1.456-1.04-.92-1.788L10.013.474c.214-.297.556-.474.92-.474h28.894c.92 0 1.456 1.04.92 1.788l-7.48 10.471c-1.07 1.498 0 3.579 1.842 3.579h11.377c.943 0 1.473 1.088.89 1.83L25.947 44.94z" fill="var(--color-primary)"/>
        </svg>
        <span
          className="font-bold tracking-tight font-display"
          style={{
            fontSize: '15px',
            color: 'var(--color-text)',
            letterSpacing: '-0.3px',
            fontFamily: 'var(--font-family-display)',
            fontWeight: 700,
          }}
        >
          SubForge
        </span>
      </a>

      {/* Spacer — pushes nav to center */}
      <div className="flex-1" />

      {/* Nav links — center, visible at all breakpoints */}
      <nav className="flex items-center gap-0.5 sm:gap-1">
        {navLinks.map(({ href, label }) => {
          const isActive = currentPath === href
          return (
            <a
              key={href}
              href={href}
              onClick={(e) => {
                e.preventDefault()
                if (window.location.pathname === href) return
                history.pushState(null, '', href)
                window.dispatchEvent(new Event('spa-navigate'))
              }}
              className="relative px-2 sm:px-3 py-1.5 text-xs sm:text-sm font-medium transition-colors"
              style={{
                color: isActive ? 'var(--color-primary)' : 'var(--color-text-2)',
                textDecoration: 'none',
                fontWeight: isActive ? 600 : 500,
                cursor: 'pointer',
              }}
              onMouseEnter={e => {
                if (!isActive) e.currentTarget.style.color = 'var(--color-text)'
              }}
              onMouseLeave={e => {
                if (!isActive) e.currentTarget.style.color = 'var(--color-text-2)'
              }}
            >
              {label}
              {/* Active underline — brand color */}
              {isActive && (
                <span
                  style={{
                    position: 'absolute',
                    bottom: '-1px',
                    left: '8px',
                    right: '8px',
                    height: '2px',
                    borderRadius: '1px',
                    background: 'var(--color-primary)',
                  }}
                />
              )}
            </a>
          )
        })}
      </nav>

      {/* Spacer — pushes health to right */}
      <div className="flex-1" />

      {/* Settings button — Pixel (Sr. Frontend), Sprint L47 */}
      <button
        type="button"
        onClick={() => setPrefsOpen(true)}
        aria-label="Open preferences"
        title="Preferences"
        className="flex items-center justify-center rounded-lg transition-colors"
        style={{
          width: '32px',
          height: '32px',
          color: 'var(--color-text-2)',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
        }}
        onMouseEnter={e => { e.currentTarget.style.background = 'var(--color-surface-2)'; e.currentTarget.style.color = 'var(--color-text)' }}
        onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--color-text-2)' }}
      >
        <GearIcon />
      </button>

      {/* Theme toggle — Pixel (Sr. Frontend), Sprint L30 */}
      <button
        type="button"
        onClick={cycleTheme}
        aria-label={themeLabels[theme]}
        title={themeLabels[theme]}
        className="flex items-center justify-center rounded-lg transition-colors"
        style={{
          width: '32px',
          height: '32px',
          color: 'var(--color-text-2)',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          marginRight: '4px',
        }}
        onMouseEnter={e => { e.currentTarget.style.background = 'var(--color-surface-2)'; e.currentTarget.style.color = 'var(--color-text)' }}
        onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--color-text-2)' }}
      >
        <ThemeIcon theme={theme} />
      </button>

      {/* Health indicator — simplified dot + label, right */}
      <button
        type="button"
        data-health-toggle
        onClick={() => setHealthPanelOpen(!healthPanelOpen)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors"
        style={{
          background: healthPanelOpen ? 'var(--color-surface-2)' : 'transparent',
          border: 'none',
          cursor: 'pointer',
        }}
      >
        <HealthDot status={health?.status ?? null} />
        <span
          className="hidden sm:inline text-xs font-medium"
          style={{ color: labelColor }}
        >
          {statusLabel}
        </span>
      </button>

      {/* Preferences panel — Pixel (Sr. Frontend), Sprint L47 */}
      <PreferencesPanel open={prefsOpen} onClose={() => setPrefsOpen(false)} />
    </header>
  )
}
