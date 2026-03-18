import { useEffect, useRef } from 'react'
import { useEditorStore } from '../store/editorStore'
import { useUIStore } from '../store/uiStore'
import { useRecentProjectsStore } from '../store/recentProjectsStore'

const BASE_DELAY = 1000
const MAX_DELAY = 30000
const WATCHDOG_TIMEOUT = 45000

export function useSSE(taskId: string | null) {
  const updateProgress = useEditorStore(s => s.updateProgress)
  const addLiveSegment = useEditorStore(s => s.addLiveSegment)
  const setComplete = useEditorStore(s => s.setComplete)
  const setError = useEditorStore(s => s.setError)
  const setSSEConnected = useUIStore(s => s.setSSEConnected)
  const setReconnecting = useUIStore(s => s.setReconnecting)
  const updateProject = useRecentProjectsStore(s => s.updateProject)

  const esRef = useRef<EventSource | null>(null)
  const watchdogRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const retryCountRef = useRef(0)

  useEffect(() => {
    if (!taskId) return

    let cancelled = false

    const resetWatchdog = () => {
      if (watchdogRef.current) clearTimeout(watchdogRef.current)
      watchdogRef.current = setTimeout(() => {
        // Watchdog fired — poll for final state
        fetch(`/progress/${taskId}`)
          .then(r => r.json())
          .then(data => {
            if (data.status === 'done') {
              setComplete({
                segments: data.segments || [],
                language: data.language || null,
                modelUsed: data.model || null,
                timings: data.step_timings || {},
                isVideo: data.is_video ?? false,
              })
            } else if (data.status === 'error') {
              setError(data.error || 'Task failed')
            }
          })
          .catch(() => {}) // Keep SSE running if poll fails
      }, WATCHDOG_TIMEOUT)
    }

    const connect = (delay: number) => {
      if (cancelled) return

      if (delay > 0) {
        setReconnecting(true)
        setTimeout(() => {
          if (!cancelled) connect(0)
        }, delay)
        return
      }

      const es = new EventSource(`/events/${taskId}`)
      esRef.current = es
      retryCountRef.current++

      es.onopen = () => {
        setSSEConnected(true)
        setReconnecting(false)
        retryCountRef.current = 0
        resetWatchdog()
      }

      es.onerror = () => {
        es.close()
        esRef.current = null
        setSSEConnected(false)
        const delay = Math.min(BASE_DELAY * Math.pow(2, retryCountRef.current - 1), MAX_DELAY)
        connect(delay)
      }

      const handleEvent = (event: MessageEvent) => {
        resetWatchdog()
        try {
          const data = JSON.parse(event.data)
          switch (event.type) {
            case 'progress':
              updateProgress(data)
              break
            case 'segment':
              addLiveSegment(data)
              break
            case 'step_change':
              updateProgress(data)
              break
            case 'done':
              setComplete({
                segments: data.segments || [],
                language: data.language || null,
                modelUsed: data.model || null,
                timings: data.step_timings || {},
                isVideo: data.is_video ?? false,
              })
              updateProject(taskId, { status: 'completed', duration: data.duration ?? null })
              es.close()
              esRef.current = null
              setSSEConnected(false)
              if (watchdogRef.current) clearTimeout(watchdogRef.current)
              break
            case 'error':
              setError(data.error || data.message || 'Task failed')
              updateProject(taskId, { status: 'failed' })
              es.close()
              esRef.current = null
              setSSEConnected(false)
              if (watchdogRef.current) clearTimeout(watchdogRef.current)
              break
            case 'cancelled':
              setError('Cancelled')
              es.close()
              esRef.current = null
              setSSEConnected(false)
              if (watchdogRef.current) clearTimeout(watchdogRef.current)
              break
            // embed_progress/embed_done/embed_error/translate_progress/translate_done
            // handled by component-local state — we don't dispatch these to global store
          }
        } catch {
          // Malformed event data — ignore
        }
      }

      es.addEventListener('progress', handleEvent)
      es.addEventListener('segment', handleEvent)
      es.addEventListener('step_change', handleEvent)
      es.addEventListener('done', handleEvent)
      es.addEventListener('error', handleEvent)
      es.addEventListener('cancelled', handleEvent)
    }

    connect(0)

    return () => {
      cancelled = true
      if (esRef.current) {
        esRef.current.close()
        esRef.current = null
      }
      if (watchdogRef.current) clearTimeout(watchdogRef.current)
      setSSEConnected(false)
    }
  }, [taskId]) // eslint-disable-line react-hooks/exhaustive-deps
}
