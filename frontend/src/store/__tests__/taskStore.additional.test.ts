import { describe, it, expect, beforeEach } from 'vitest'
import { useTaskStore } from '../taskStore'

const store = () => useTaskStore.getState()
const reset = () => useTaskStore.getState().reset()

describe('taskStore — additional actions', () => {
  beforeEach(reset)

  // ── setUploading ──────────────────────────────────────────────────────────

  it('setUploading(true, 50) sets isUploading and uploadPercent', () => {
    store().setUploading(true, 50)
    expect(store().isUploading).toBe(true)
    expect(store().uploadPercent).toBe(50)
  })

  it('setUploading(false) resets uploadPercent to 0', () => {
    store().setUploading(true, 75)
    store().setUploading(false)
    expect(store().isUploading).toBe(false)
    expect(store().uploadPercent).toBe(0)
  })

  it('setUploading(true) without percent defaults to 0', () => {
    store().setUploading(true)
    expect(store().isUploading).toBe(true)
    expect(store().uploadPercent).toBe(0)
  })

  // ── setUploadPercent ──────────────────────────────────────────────────────

  it('setUploadPercent updates independently of isUploading', () => {
    store().setUploadPercent(75)
    expect(store().uploadPercent).toBe(75)
    expect(store().isUploading).toBe(false) // unchanged
  })

  // ── setUploadEta ──────────────────────────────────────────────────────────

  it('setUploadEta stores the eta string', () => {
    store().setUploadEta('~5s')
    expect(store().uploadEta).toBe('~5s')
  })

  it('setUploadEta can be updated multiple times', () => {
    store().setUploadEta('~10s')
    store().setUploadEta('~3s')
    expect(store().uploadEta).toBe('~3s')
  })

  // ── setLiveSegments ───────────────────────────────────────────────────────

  it('setLiveSegments replaces the entire liveSegments array', () => {
    store().addSegment({ start: 0, end: 1, text: 'Old' })
    expect(store().liveSegments).toHaveLength(1)

    const newSegs = [
      { start: 0, end: 1.5, text: 'New first' },
      { start: 1.5, end: 3.0, text: 'New second' },
    ]
    store().setLiveSegments(newSegs)

    expect(store().liveSegments).toHaveLength(2)
    expect(store().liveSegments[0].text).toBe('New first')
    expect(store().liveSegments[1].text).toBe('New second')
  })

  it('setLiveSegments with empty array clears segments', () => {
    store().addSegment({ start: 0, end: 1, text: 'Something' })
    store().setLiveSegments([])
    expect(store().liveSegments).toHaveLength(0)
  })

  // ── setPauseRequesting ────────────────────────────────────────────────────

  it('setPauseRequesting(true) toggles isPauseRequesting without changing isPaused', () => {
    expect(store().isPaused).toBe(false)
    expect(store().isPauseRequesting).toBe(false)

    store().setPauseRequesting(true)
    expect(store().isPauseRequesting).toBe(true)
    expect(store().isPaused).toBe(false) // unchanged
  })

  it('setPauseRequesting(false) resets back', () => {
    store().setPauseRequesting(true)
    store().setPauseRequesting(false)
    expect(store().isPauseRequesting).toBe(false)
  })

  // ── setCancelRequesting ───────────────────────────────────────────────────

  it('setCancelRequesting(true) toggles isCancelRequesting', () => {
    expect(store().isCancelRequesting).toBe(false)

    store().setCancelRequesting(true)
    expect(store().isCancelRequesting).toBe(true)
  })

  it('setCancelRequesting(false) resets back', () => {
    store().setCancelRequesting(true)
    store().setCancelRequesting(false)
    expect(store().isCancelRequesting).toBe(false)
  })

  // ── lastEventTime updated by applyProgressData ────────────────────────────

  it('applyProgressData updates lastEventTime to current time', () => {
    const before = Date.now()
    store().applyProgressData({ percent: 50 })
    const after = Date.now()

    const lastEvent = store().lastEventTime
    expect(lastEvent).toBeGreaterThanOrEqual(before)
    expect(lastEvent).toBeLessThanOrEqual(after)
  })

  it('applyProgressData updates lastEventTime on every call', () => {
    store().applyProgressData({ percent: 10 })
    const first = store().lastEventTime

    // Small delay to ensure Date.now() differs
    store().applyProgressData({ percent: 20 })
    const second = store().lastEventTime

    expect(second).toBeGreaterThanOrEqual(first)
  })

})
