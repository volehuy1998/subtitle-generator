import { describe, it, expect, beforeEach } from 'vitest'
import { useTaskStore } from '../taskStore'

// Direct Zustand store access — no React rendering required.
const store = () => useTaskStore.getState()
const reset = () => useTaskStore.getState().reset()

describe('taskStore', () => {
  beforeEach(reset)

  // ── Initial state ──────────────────────────────────────────────────────────

  it('starts with null identity and zero progress', () => {
    const s = store()
    expect(s.taskId).toBeNull()
    expect(s.filename).toBeNull()
    expect(s.status).toBeNull()
    expect(s.percent).toBe(0)
    expect(s.message).toBe('')
    expect(s.isComplete).toBe(false)
    expect(s.error).toBeNull()
    expect(s.liveSegments).toHaveLength(0)
    expect(s.downloadReady).toBe(false)
    expect(s.warning).toBeNull()
  })

  // ── setTaskId ─────────────────────────────────────────────────────────────

  it('setTaskId stores the task id', () => {
    store().setTaskId('abc-123')
    expect(store().taskId).toBe('abc-123')
  })

  // ── applyProgressData ─────────────────────────────────────────────────────

  it('applyProgressData merges partial updates without overwriting unrelated fields', () => {
    store().setTaskId('xyz')
    store().applyProgressData({ status: 'transcribing', percent: 45, message: 'Working…' })
    const s = store()
    expect(s.taskId).toBe('xyz')   // unchanged
    expect(s.status).toBe('transcribing')
    expect(s.percent).toBe(45)
    expect(s.message).toBe('Working…')
  })

  it('applyProgressData can set audio metadata', () => {
    store().applyProgressData({ audioDuration: 120.5, language: 'en', device: 'cpu' })
    expect(store().audioDuration).toBe(120.5)
    expect(store().language).toBe('en')
    expect(store().device).toBe('cpu')
  })

  // ── addSegment ────────────────────────────────────────────────────────────

  it('addSegment appends segments in order', () => {
    store().addSegment({ start: 0, end: 1.5, text: 'Hello world' })
    store().addSegment({ start: 1.5, end: 3.0, text: 'How are you' })
    store().addSegment({ start: 3.0, end: 4.2, text: 'Fine thanks', speaker: 'A' })
    const segs = store().liveSegments
    expect(segs).toHaveLength(3)
    expect(segs[0].text).toBe('Hello world')
    expect(segs[2].speaker).toBe('A')
  })

  // ── setStep ───────────────────────────────────────────────────────────────

  it('setStep updates activeStep', () => {
    expect(store().activeStep).toBe(-1)
    store().setStep(0)
    expect(store().activeStep).toBe(0)
    store().setStep(2)
    expect(store().activeStep).toBe(2)
  })

  // ── setComplete ───────────────────────────────────────────────────────────

  it('setComplete marks the task done and enables download', () => {
    store().setTaskId('t1')
    store().addSegment({ start: 0, end: 1, text: 'Hi' })
    store().setComplete({ segments: 42, totalTimeSec: 12.5, language: 'fr' })
    const s = store()
    expect(s.status).toBe('done')
    expect(s.percent).toBe(100)
    expect(s.isComplete).toBe(true)
    expect(s.downloadReady).toBe(true)
    expect(s.segments).toBe(42)
    expect(s.totalTimeSec).toBe(12.5)
    expect(s.liveSegments).toHaveLength(1) // existing segments preserved
  })

  // ── setCancelled ──────────────────────────────────────────────────────────

  it('setCancelled clears pause state', () => {
    store().setPaused()
    expect(store().isPaused).toBe(true)
    store().setCancelled()
    expect(store().status).toBe('cancelled')
    expect(store().isPaused).toBe(false)
  })

  // ── setError ──────────────────────────────────────────────────────────────

  it('setError stores the error message and sets status', () => {
    store().setError('Model OOM — try a smaller model')
    expect(store().status).toBe('error')
    expect(store().error).toBe('Model OOM — try a smaller model')
  })

  // ── pause / resume ────────────────────────────────────────────────────────

  it('setPaused and setResumed toggle correctly', () => {
    store().setPaused()
    expect(store().isPaused).toBe(true)
    expect(store().status).toBe('paused')

    store().setResumed()
    expect(store().isPaused).toBe(false)
    expect(store().status).toBe('transcribing')
  })

  // ── setWarning ────────────────────────────────────────────────────────────

  it('setWarning stores the warning string', () => {
    store().setWarning('Speaker diarization skipped: insufficient memory')
    expect(store().warning).toBe('Speaker diarization skipped: insufficient memory')
  })

  // ── setEmbedDownload ──────────────────────────────────────────────────────

  it('setEmbedDownload stores the embed download URL', () => {
    store().setEmbedDownload('/embed/download/abc-123')
    expect(store().embedDownloadUrl).toBe('/embed/download/abc-123')
  })

  // ── reset ─────────────────────────────────────────────────────────────────

  it('reset returns every field to initial values', () => {
    store().setTaskId('heavy-state')
    store().applyProgressData({ status: 'transcribing', percent: 75, message: 'Almost done' })
    store().addSegment({ start: 0, end: 1, text: 'Segment' })
    store().setStep(2)
    store().setWarning('some warning')

    store().reset()
    const s = store()
    expect(s.taskId).toBeNull()
    expect(s.status).toBeNull()
    expect(s.percent).toBe(0)
    expect(s.message).toBe('')
    expect(s.activeStep).toBe(-1)
    expect(s.liveSegments).toHaveLength(0)
    expect(s.warning).toBeNull()
    expect(s.isComplete).toBe(false)
    expect(s.downloadReady).toBe(false)
    expect(s.embedDownloadUrl).toBeNull()
  })

  // ── state isolation between tests ─────────────────────────────────────────

  it('each test starts fresh (beforeEach reset verification)', () => {
    // If reset() didn't run, taskId from the "setTaskId" test above would bleed in.
    expect(store().taskId).toBeNull()
    expect(store().liveSegments).toHaveLength(0)
  })
})
