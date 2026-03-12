import { useUIStore } from '@/store/uiStore'

export function ConnectionBanner() {
  const { sseConnected, reconnecting, dbOk } = useUIStore()

  const isReconnecting = reconnecting
  const isOffline = !sseConnected && !reconnecting
  const isDbDown = sseConnected && !dbOk

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

  const bg = isReconnecting ? 'var(--color-warning)' : 'var(--color-danger)'
  const label = isReconnecting ? 'Reconnecting…' : 'Offline · retrying…'

  return (
    <div
      className="fixed z-50 top-4 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium text-white shadow-lg"
      style={{ background: bg, boxShadow: 'var(--shadow-lg)' }}
      role="status"
      aria-live="polite"
    >
      <span className="inline-block w-1.5 h-1.5 rounded-full bg-white opacity-80 animate-pulse" />
      {label}
    </div>
  )
}
