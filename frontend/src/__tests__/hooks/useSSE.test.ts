import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useSSE } from '../../hooks/useSSE'
import { useEditorStore } from '../../store/editorStore'
import { useUIStore } from '../../store/uiStore'

// Mock EventSource
class MockEventSource {
  static instances: MockEventSource[] = []
  url: string
  onopen: ((e: Event) => void) | null = null
  onerror: ((e: Event) => void) | null = null
  private listeners: Record<string, ((e: MessageEvent) => void)[]> = {}
  readyState = 0

  constructor(url: string) {
    this.url = url
    MockEventSource.instances.push(this)
  }

  addEventListener(type: string, fn: (e: MessageEvent) => void) {
    if (!this.listeners[type]) this.listeners[type] = []
    this.listeners[type].push(fn)
  }

  emit(type: string, data: unknown) {
    const event = { type, data: JSON.stringify(data) } as MessageEvent
    this.listeners[type]?.forEach(fn => fn(event))
  }

  close() { this.readyState = 2 }
}

describe('useSSE', () => {
  beforeEach(() => {
    MockEventSource.instances = []
    vi.stubGlobal('EventSource', MockEventSource)
    useEditorStore.getState().reset()
    useUIStore.setState({ sseConnected: false, sseReconnecting: false })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('does nothing when taskId is null', () => {
    renderHook(() => useSSE(null))
    expect(MockEventSource.instances).toHaveLength(0)
  })

  it('creates EventSource for taskId', () => {
    renderHook(() => useSSE('task-123'))
    expect(MockEventSource.instances).toHaveLength(1)
    expect(MockEventSource.instances[0].url).toBe('/events/task-123')
  })

  it('dispatches progress event to editorStore', () => {
    const { rerender } = renderHook(() => useSSE('task-123'))
    const es = MockEventSource.instances[0]
    es.onopen?.(new Event('open'))
    es.emit('progress', { percent: 50, segmentCount: 10, estimatedSegments: 20, eta: 30, elapsed: 5, speed: 2, pipelineStep: 'transcribing', message: 'Running...' })
    expect(useEditorStore.getState().progress?.percent).toBe(50)
    rerender()
  })

  it('dispatches segment event', () => {
    renderHook(() => useSSE('task-123'))
    const es = MockEventSource.instances[0]
    es.onopen?.(new Event('open'))
    es.emit('segment', { index: 0, start: 0, end: 5, text: 'Hello' })
    expect(useEditorStore.getState().liveSegments).toHaveLength(1)
  })

  it('transitions to editing on done event', () => {
    renderHook(() => useSSE('task-123'))
    const es = MockEventSource.instances[0]
    es.onopen?.(new Event('open'))
    es.emit('done', { segments: [{ index: 0, start: 0, end: 5, text: 'Hi' }], language: 'en', model: 'large', step_timings: {}, is_video: false })
    expect(useEditorStore.getState().phase).toBe('editing')
  })

  it('sets error phase on error event', () => {
    renderHook(() => useSSE('task-123'))
    const es = MockEventSource.instances[0]
    es.onopen?.(new Event('open'))
    es.emit('error', { error: 'Pipeline failed' })
    expect(useEditorStore.getState().phase).toBe('error')
  })
})
