import { useEffect, useRef, useCallback } from 'react'
import { useTaskStore } from '@/store/taskStore'
import { useUIStore } from '@/store/uiStore'
import { api } from '@/api/client'

const MIN_RETRY = 1000
const MAX_RETRY = 30000

export function useSSE(taskId: string | null) {
  const esRef = useRef<EventSource | null>(null)
  const retryDelay = useRef(MIN_RETRY)
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const lastEventTime = useRef(0)
  const watchdog = useRef<ReturnType<typeof setInterval> | null>(null)
  const closed = useRef(false)

  const store = useTaskStore()
  const { setSseConnected, setReconnecting } = useUIStore()

  const close = useCallback(() => {
    closed.current = true
    if (retryTimer.current) clearTimeout(retryTimer.current)
    if (watchdog.current) clearInterval(watchdog.current)
    esRef.current?.close()
    esRef.current = null
    setSseConnected(false)
    setReconnecting(false)
  }, [setSseConnected, setReconnecting])

  const connect = useCallback(() => {
    if (!taskId || closed.current) return
    esRef.current?.close()

    const es = new EventSource(`/events/${taskId}`)
    esRef.current = es
    lastEventTime.current = Date.now()

    const onData = () => {
      lastEventTime.current = Date.now()
      retryDelay.current = MIN_RETRY
      setSseConnected(true)
      setReconnecting(false)
    }

    es.addEventListener('state', (e) => {
      onData()
      const data = JSON.parse((e as MessageEvent).data)
      store.applyProgressData(data)
      if (data.status === 'done') store.setComplete(data)
    })

    es.addEventListener('progress', (e) => {
      onData()
      const data = JSON.parse((e as MessageEvent).data)
      store.applyProgressData(data)
      if (data.step !== undefined) store.setStep(data.step)
    })

    es.addEventListener('step_change', (e) => {
      onData()
      const data = JSON.parse((e as MessageEvent).data)
      store.applyProgressData(data)
      if (data.step !== undefined) store.setStep(data.step)
    })

    es.addEventListener('segment', (e) => {
      onData()
      store.addSegment(JSON.parse((e as MessageEvent).data))
    })

    es.addEventListener('warning', (e) => {
      onData()
      const data = JSON.parse((e as MessageEvent).data)
      store.setWarning(data.message ?? data.warning ?? '')
    })

    es.addEventListener('done', (e) => {
      onData()
      store.setComplete(JSON.parse((e as MessageEvent).data))
      localStorage.setItem('sg_currentTaskId', taskId)
      close()
    })

    es.addEventListener('paused', () => { onData(); store.setPaused() })
    es.addEventListener('resumed', () => { onData(); store.setResumed() })

    es.addEventListener('embed_progress', (e) => {
      onData()
      const data = JSON.parse((e as MessageEvent).data)
      store.applyProgressData({ message: data.message ?? 'Embedding…' })
    })

    es.addEventListener('embed_done', (e) => {
      onData()
      const data = JSON.parse((e as MessageEvent).data)
      if (data.download_url) store.setEmbedDownload(data.download_url)
      close()
    })

    es.addEventListener('embed_error', (e) => {
      onData()
      const data = JSON.parse((e as MessageEvent).data)
      store.setError(data.message ?? 'Embedding failed')
      close()
    })

    es.addEventListener('cancelled', () => {
      onData()
      store.setCancelled()
      localStorage.removeItem('sg_currentTaskId')
      close()
    })

    es.addEventListener('critical_abort', (e) => {
      onData()
      const data = JSON.parse((e as MessageEvent).data)
      store.setError(data.message ?? 'Critical system error')
      close()
    })

    es.addEventListener('heartbeat', () => { onData() })

    es.onerror = () => {
      if (closed.current) return
      setSseConnected(false)
      setReconnecting(true)
      es.close()
      // Check if task finished before reconnecting
      api.progress(taskId).then((data) => {
        if (data.status === 'done') { store.setComplete(data); close(); return }
        if (data.status === 'cancelled') { store.setCancelled(); close(); return }
        if (data.status === 'error') { store.setError(data.error ?? 'Task failed'); close(); return }
        retryTimer.current = setTimeout(() => {
          retryDelay.current = Math.min(retryDelay.current * 2, MAX_RETRY)
          connect()
        }, retryDelay.current)
      }).catch(() => {
        retryTimer.current = setTimeout(() => {
          retryDelay.current = Math.min(retryDelay.current * 2, MAX_RETRY)
          connect()
        }, retryDelay.current)
      })
    }

    // Watchdog: if no event for 45s, force reconnect
    if (watchdog.current) clearInterval(watchdog.current)
    watchdog.current = setInterval(() => {
      if (closed.current) return
      if (Date.now() - lastEventTime.current > 45_000) {
        es.close()
        es.onerror?.(new Event('error'))
      }
    }, 5000)
  }, [taskId, close, store, setSseConnected, setReconnecting])

  useEffect(() => {
    if (!taskId) return
    closed.current = false
    connect()
    return () => { closed.current = true; close() }
  }, [taskId]) // eslint-disable-line react-hooks/exhaustive-deps

  return { close }
}
