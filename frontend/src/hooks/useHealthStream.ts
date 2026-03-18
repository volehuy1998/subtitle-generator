import { useEffect, useRef } from 'react'
import { useUIStore } from '../store/uiStore'

const GRACE_PERIOD_MS = 2500

export function useHealthStream() {
  const setSSEConnected = useUIStore(s => s.setSSEConnected)
  const setSystemHealth = useUIStore(s => s.setSystemHealth)
  const setModelPreloadStatus = useUIStore(s => s.setModelPreloadStatus)
  const gracePeriodRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const es = new EventSource('/health/stream')

    es.onopen = () => {
      if (gracePeriodRef.current) clearTimeout(gracePeriodRef.current)
      setSSEConnected(true)
    }

    es.onerror = () => {
      if (gracePeriodRef.current) clearTimeout(gracePeriodRef.current)
      gracePeriodRef.current = setTimeout(() => {
        setSSEConnected(false)
      }, GRACE_PERIOD_MS)
    }

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.system_critical) {
          setSystemHealth('critical')
        } else if (data.disk_percent > 90 || data.cpu_percent > 95) {
          setSystemHealth('degraded')
        } else {
          setSystemHealth('healthy')
        }
        if (data.models) {
          setModelPreloadStatus(data.models)
        }
      } catch {
        // Ignore parse errors
      }
    }

    return () => {
      es.close()
      if (gracePeriodRef.current) clearTimeout(gracePeriodRef.current)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
}
