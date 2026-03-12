import { useEffect, useRef, useState } from 'react'
import type { HealthStatus } from '@/api/types'

export function useHealthStream() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    const connect = () => {
      const es = new EventSource('/health/stream')
      esRef.current = es
      es.onmessage = (e) => {
        try { setHealth(JSON.parse(e.data) as HealthStatus) } catch { /* ignore */ }
      }
      es.onerror = () => {
        es.close()
        setTimeout(connect, 5000)
      }
    }
    connect()
    return () => esRef.current?.close()
  }, [])

  return health
}
