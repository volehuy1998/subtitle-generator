import { useEffect, useRef } from 'react'
import { useUIStore } from '../store/uiStore'

const GRACE_PERIOD_MS = 2500

export function useHealthStream() {
  const setHealthStreamConnected = useUIStore(s => s.setHealthStreamConnected)
  const setSystemHealth = useUIStore(s => s.setSystemHealth)
  const setModelPreloadStatus = useUIStore(s => s.setModelPreloadStatus)
  const setHealthMetrics = useUIStore(s => s.setHealthMetrics)
  const setHealth = useUIStore(s => s.setHealth)
  const gracePeriodRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const es = new EventSource('/health/stream')

    es.onopen = () => {
      if (gracePeriodRef.current) clearTimeout(gracePeriodRef.current)
      setHealthStreamConnected(true)
    }

    es.onerror = () => {
      if (gracePeriodRef.current) clearTimeout(gracePeriodRef.current)
      gracePeriodRef.current = setTimeout(() => {
        setHealthStreamConnected(false)
      }, GRACE_PERIOD_MS)
    }

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setHealth(data)
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
        setHealthMetrics({
          cpuPercent: data.cpu_percent ?? null,
          memoryPercent: data.memory_percent ?? null,
          diskPercent: data.disk_percent ?? null,
          diskFreeGb: data.disk_free_gb ?? null,
          activeTasks: data.active_tasks ?? 0,
          lastUpdated: Date.now(),
        })
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
