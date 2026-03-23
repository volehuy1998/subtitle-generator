import { describe, it, expect, beforeEach } from 'vitest'
import { useUIStore } from '../uiStore'

const store = () => useUIStore.getState()
const resetStore = () =>
  useUIStore.setState({
    appMode: 'transcribe',
    embedMode: 'soft',
    healthPanelOpen: false,
    taskQueueOpen: false,
    sseConnected: false,
    reconnecting: false,
    dbOk: true,
  })

describe('uiStore', () => {
  beforeEach(resetStore)

  // ── Initial state ──────────────────────────────────────────────────────────

  it('starts with sensible defaults', () => {
    const s = store()
    expect(s.appMode).toBe('transcribe')
    expect(s.embedMode).toBe('soft')
    expect(s.healthPanelOpen).toBe(false)
    expect(s.taskQueueOpen).toBe(false)
    expect(s.sseConnected).toBe(false)
    expect(s.reconnecting).toBe(false)
    expect(s.dbOk).toBe(true)
  })

  // ── appMode ───────────────────────────────────────────────────────────────

  it('setAppMode switches between transcribe and embed', () => {
    store().setAppMode('embed')
    expect(store().appMode).toBe('embed')
    store().setAppMode('transcribe')
    expect(store().appMode).toBe('transcribe')
  })

  // ── embedMode ─────────────────────────────────────────────────────────────

  it('setEmbedMode switches between soft and hard', () => {
    store().setEmbedMode('hard')
    expect(store().embedMode).toBe('hard')
    store().setEmbedMode('soft')
    expect(store().embedMode).toBe('soft')
  })

  // ── healthPanelOpen ───────────────────────────────────────────────────────

  it('setHealthPanelOpen toggles the health panel', () => {
    store().setHealthPanelOpen(true)
    expect(store().healthPanelOpen).toBe(true)
    store().setHealthPanelOpen(false)
    expect(store().healthPanelOpen).toBe(false)
  })

  // ── taskQueueOpen ─────────────────────────────────────────────────────────

  it('setTaskQueueOpen toggles the task queue drawer', () => {
    store().setTaskQueueOpen(true)
    expect(store().taskQueueOpen).toBe(true)
    store().setTaskQueueOpen(false)
    expect(store().taskQueueOpen).toBe(false)
  })

  // ── SSE connection state ──────────────────────────────────────────────────

  it('connection sequence: disconnected → reconnecting → connected', () => {
    // Simulate disconnect
    store().setSseConnected(false)
    store().setReconnecting(true)
    expect(store().sseConnected).toBe(false)
    expect(store().reconnecting).toBe(true)

    // Simulate successful reconnect
    store().setSseConnected(true)
    store().setReconnecting(false)
    expect(store().sseConnected).toBe(true)
    expect(store().reconnecting).toBe(false)
  })

  it('sseConnected and reconnecting are independent fields', () => {
    store().setSseConnected(true)
    store().setReconnecting(true) // can be reconnecting while still "connected" during transition
    expect(store().sseConnected).toBe(true)
    expect(store().reconnecting).toBe(true)
  })

  // ── dbOk ──────────────────────────────────────────────────────────────────

  it('setDbOk reflects database connectivity changes', () => {
    store().setDbOk(false)
    expect(store().dbOk).toBe(false)
    store().setDbOk(true)
    expect(store().dbOk).toBe(true)
  })

})
