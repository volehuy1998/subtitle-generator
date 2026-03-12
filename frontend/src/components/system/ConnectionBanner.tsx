import { useUIStore } from '@/store/uiStore'

export function ConnectionBanner() {
  const { sseConnected, reconnecting } = useUIStore()

  // Show nothing when normally connected
  if (sseConnected && !reconnecting) return null

  const isReconnecting = reconnecting
  const isOffline = !sseConnected && !reconnecting

  // Only show when there's an issue
  if (!isReconnecting && !isOffline) return null

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
