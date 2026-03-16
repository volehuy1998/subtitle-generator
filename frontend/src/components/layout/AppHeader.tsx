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
import type { HealthStatus } from '@/api/types'

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

export function AppHeader() {
  const { healthPanelOpen, setHealthPanelOpen, health } = useUIStore()

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
      className="sticky top-0 z-40 flex items-center px-6"
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

      {/* Nav links — center */}
      <nav className="hidden sm:flex items-center gap-1">
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
              className="relative px-3 py-1.5 text-sm font-medium transition-colors"
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
                    left: '12px',
                    right: '12px',
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
          className="text-xs font-medium"
          style={{ color: labelColor }}
        >
          {statusLabel}
        </span>
      </button>
    </header>
  )
}
