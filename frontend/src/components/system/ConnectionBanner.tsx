/**
 * ConnectionBanner — shows connection status when SSE is disconnected.
 * Enhanced with auto-reconnect countdown and manual reconnect button.
 *
 * — Pixel (Sr. Frontend), Sprint L52
 */

import { useEffect, useState, useRef } from 'react'
import { useUIStore } from '@/store/uiStore'

const RECONNECT_INTERVAL = 5

export function ConnectionBanner() {
  const { sseConnected, reconnecting, dbOk } = useUIStore()
  const [countdown, setCountdown] = useState(RECONNECT_INTERVAL)
  const [flashSuccess, setFlashSuccess] = useState(false)
  const wasDisconnected = useRef(false)

  const isReconnecting = reconnecting
  const isOffline = !sseConnected && !reconnecting
  const isDbDown = sseConnected && !dbOk

  // Track reconnection to show success flash
  useEffect(() => {
    if (!sseConnected) {
      wasDisconnected.current = true
    } else if (wasDisconnected.current) {
      wasDisconnected.current = false
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setFlashSuccess(true)
      const timer = setTimeout(() => setFlashSuccess(false), 2000)
      return () => clearTimeout(timer)
    }
  }, [sseConnected])

  // Countdown timer when disconnected
  useEffect(() => {
    if (sseConnected && !isDbDown) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setCountdown(RECONNECT_INTERVAL)
      return
    }
    if (isDbDown) return

    setCountdown(RECONNECT_INTERVAL)
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) return RECONNECT_INTERVAL
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(interval)
  }, [sseConnected, isDbDown])

  // Reconnect now — force page to re-establish SSE by triggering a health check
  const handleReconnectNow = () => {
    setCountdown(RECONNECT_INTERVAL)
    // Force a fresh EventSource connection by fetching health endpoint
    fetch('/health/stream').catch(() => {})
    // Reload the page as a reliable reconnect mechanism
    window.location.reload()
  }

  // Success flash on reconnect
  if (flashSuccess) {
    return (
      <div
        className="fixed z-50 top-4 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium text-white shadow-lg animate-fade-in"
        style={{ background: 'var(--color-success)', boxShadow: 'var(--shadow-lg)' }}
        role="status"
        aria-live="polite"
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
          <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.5" fill="none" />
          <path d="M3.5 6l2 2 3-3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Reconnected
      </div>
    )
  }

  // Nothing to show
  if (!isReconnecting && !isOffline && !isDbDown) return null

  // DB down takes priority — most actionable
  if (isDbDown) {
    return (
      <div
        className="fixed z-50 top-4 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium text-white shadow-lg"
        style={{ background: 'var(--color-danger)', boxShadow: 'var(--shadow-lg)' }}
        role="alert"
        aria-live="assertive"
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
          <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.5" />
          <path d="M6 3.5v3M6 8.5v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        Database unavailable — uploads disabled
      </div>
    )
  }

  return (
    <div
      className="fixed z-50 top-4 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium text-white shadow-lg"
      style={{ background: 'var(--color-warning)', boxShadow: 'var(--shadow-lg)' }}
      role="status"
      aria-live="polite"
    >
      <span className="inline-block w-1.5 h-1.5 rounded-full bg-white opacity-80 animate-pulse" />
      <span>Reconnecting in {countdown}s...</span>
      <button
        type="button"
        onClick={handleReconnectNow}
        className="ml-1 px-2 py-0.5 rounded-full text-xs font-semibold transition-colors"
        style={{
          background: 'rgba(255,255,255,0.25)',
          border: 'none',
          color: 'white',
          cursor: 'pointer',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.4)' }}
        onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.25)' }}
      >
        Reconnect Now
      </button>
    </div>
  )
}
