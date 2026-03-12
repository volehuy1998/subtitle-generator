import { useEffect, useRef } from 'react'
import type { HealthStatus } from '@/api/types'
import { useUIStore } from '@/store/uiStore'

// Grace period before the offline banner appears.
// Short reconnects (e.g. during server-side keep-alive rotation) are silently
// absorbed — only sustained outages are surfaced to the user.
const OFFLINE_GRACE_MS = 2500

export function useHealthStream(): HealthStatus | null {
  const { health, setSseConnected, setReconnecting, setDbOk, setHealth } = useUIStore()
  const esRef = useRef<EventSource | null>(null)
  const offlineTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const clearOfflineTimer = () => {
      if (offlineTimer.current) {
        clearTimeout(offlineTimer.current)
        offlineTimer.current = null
      }
    }

    const connect = () => {
      const es = new EventSource('/health/stream')
      esRef.current = es

      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data) as HealthStatus
          clearOfflineTimer()
          setHealth(data)
          setSseConnected(true)
          setReconnecting(false)
          setDbOk(data.db_ok !== false)
        } catch { /* ignore parse errors */ }
      }

      es.onerror = () => {
        es.close()
        // Start grace period — only mark offline after sustained disconnection
        if (!offlineTimer.current) {
          offlineTimer.current = setTimeout(() => {
            setSseConnected(false)
            setReconnecting(true)
          }, OFFLINE_GRACE_MS)
        }
        setTimeout(connect, 5000)
      }
    }

    connect()
    return () => {
      clearOfflineTimer()
      esRef.current?.close()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return health
}
