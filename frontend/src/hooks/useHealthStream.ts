import { useEffect, useRef, useState } from 'react'
import type { HealthStatus } from '@/api/types'
import { useUIStore } from '@/store/uiStore'

export function useHealthStream() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const esRef = useRef<EventSource | null>(null)
  const { setSseConnected, setReconnecting, setDbOk } = useUIStore()

  useEffect(() => {
    const connect = () => {
      const es = new EventSource('/health/stream')
      esRef.current = es
      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data) as HealthStatus
          setHealth(data)
          setSseConnected(true)
          setReconnecting(false)
          setDbOk(data.db_ok !== false)
        } catch { /* ignore */ }
      }
      es.onerror = () => {
        es.close()
        setSseConnected(false)
        setReconnecting(true)
        setTimeout(connect, 5000)
      }
    }
    connect()
    return () => esRef.current?.close()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return health
}
