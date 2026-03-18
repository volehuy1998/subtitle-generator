import { describe, it, expect, beforeEach } from 'vitest'
import { useEditorStore } from '../../store/editorStore'

describe('editorStore', () => {
  beforeEach(() => useEditorStore.getState().reset())

  it('starts in idle phase', () => {
    expect(useEditorStore.getState().phase).toBe('idle')
    expect(useEditorStore.getState().taskId).toBeNull()
  })

  it('sets task ID', () => {
    useEditorStore.getState().setTaskId('task-123')
    expect(useEditorStore.getState().taskId).toBe('task-123')
  })

  it('updates progress', () => {
    useEditorStore.getState().updateProgress({
      percent: 45, segmentCount: 20, estimatedSegments: 50,
      eta: 30, elapsed: 15, speed: 3.2, pipelineStep: 'transcribing', message: 'Transcribing...'
    })
    expect(useEditorStore.getState().progress?.percent).toBe(45)
    expect(useEditorStore.getState().phase).toBe('processing')
  })

  it('adds live segments', () => {
    useEditorStore.getState().addLiveSegment({ index: 0, start: 0, end: 5, text: 'Hello' })
    useEditorStore.getState().addLiveSegment({ index: 1, start: 5, end: 10, text: 'World' })
    expect(useEditorStore.getState().liveSegments).toHaveLength(2)
  })

  it('completes transcription', () => {
    useEditorStore.getState().setComplete({
      segments: [{ index: 0, start: 0, end: 5, text: 'Hello' }],
      language: 'en', modelUsed: 'large',
      timings: { extract: 0.8, transcribe: 45.2 }, isVideo: true
    })
    expect(useEditorStore.getState().phase).toBe('editing')
    expect(useEditorStore.getState().segments).toHaveLength(1)
    expect(useEditorStore.getState().language).toBe('en')
  })

  it('updates a segment', () => {
    useEditorStore.getState().setComplete({
      segments: [{ index: 0, start: 0, end: 5, text: 'Hello' }],
      language: 'en', modelUsed: 'large', timings: {}, isVideo: false
    })
    useEditorStore.getState().updateSegment(0, 'Hello World')
    expect(useEditorStore.getState().segments[0].text).toBe('Hello World')
  })

  it('sets error state', () => {
    useEditorStore.getState().setError('Something failed')
    expect(useEditorStore.getState().phase).toBe('error')
    expect(useEditorStore.getState().errorMessage).toBe('Something failed')
  })

  it('resets to initial state', () => {
    useEditorStore.getState().setTaskId('task-123')
    useEditorStore.getState().reset()
    expect(useEditorStore.getState().taskId).toBeNull()
    expect(useEditorStore.getState().phase).toBe('idle')
  })
})
