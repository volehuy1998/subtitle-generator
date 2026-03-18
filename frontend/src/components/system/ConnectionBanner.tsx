/**
 * ConnectionBanner — full-width banner rendered above the Header in AppShell.
 *
 * Priority order (highest first):
 *   1. Red   — system critical (uploads paused)
 *   2. Yellow — SSE disconnected & reconnecting
 *   3. Blue   — model loading
 *
 * Returns null when no banner should show.
 *
 * — Pixel (Sr. Frontend Engineer), Task 36
 */

import { useUIStore } from '../../store/uiStore'

export function ConnectionBanner() {
  const systemHealth = useUIStore((s) => s.systemHealth)
  const sseReconnecting = useUIStore((s) => s.sseReconnecting)
  const modelPreloadStatus = useUIStore((s) => s.modelPreloadStatus)

  const isCritical = systemHealth === 'critical'
  const isReconnecting = sseReconnecting
  const isModelLoading = Object.values(modelPreloadStatus).some((v) => v === 'loading')

  if (isCritical) {
    return (
      <div
        role="alert"
        aria-live="assertive"
        className="w-full px-4 py-2 text-center text-sm font-medium text-white"
        style={{ background: 'var(--color-danger, #ef4444)' }}
      >
        System critical: uploads paused
      </div>
    )
  }

  if (isReconnecting) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="w-full px-4 py-2 text-center text-sm font-medium text-white"
        style={{ background: 'var(--color-warning, #f59e0b)' }}
      >
        Reconnecting to server...
      </div>
    )
  }

  if (isModelLoading) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="w-full px-4 py-2 text-center text-sm font-medium text-white"
        style={{ background: 'var(--color-primary, #6366f1)' }}
      >
        Loading AI model...
      </div>
    )
  }

  return null
}
