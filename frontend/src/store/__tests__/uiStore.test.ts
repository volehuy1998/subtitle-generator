import { describe, it, expect, beforeEach } from 'vitest'
import { useUIStore } from '../uiStore'

const store = () => useUIStore.getState()
const resetStore = () =>
  useUIStore.setState({
    currentPage: '/',
    contextPanelContent: 'info',
    sseConnected: false,
    sseReconnecting: false,
    systemHealth: 'healthy',
    modelPreloadStatus: {},
    dismissedSuggestions: [],
  })

describe('uiStore', () => {
  beforeEach(resetStore)

  // ── Initial state ──────────────────────────────────────────────────────────

  it('starts with sensible defaults', () => {
    const s = store()
    expect(s.currentPage).toBe('/')
    expect(s.contextPanelContent).toBe('info')
    expect(s.sseConnected).toBe(false)
    expect(s.sseReconnecting).toBe(false)
    expect(s.systemHealth).toBe('healthy')
  })

  // ── currentPage ───────────────────────────────────────────────────────────

  it('setCurrentPage updates the page', () => {
    store().setCurrentPage('/editor/123')
    expect(store().currentPage).toBe('/editor/123')
    store().setCurrentPage('/')
    expect(store().currentPage).toBe('/')
  })

  // ── contextPanelContent ───────────────────────────────────────────────────

  it('setContextPanel switches between panels', () => {
    store().setContextPanel('translate')
    expect(store().contextPanelContent).toBe('translate')
    store().setContextPanel('embed')
    expect(store().contextPanelContent).toBe('embed')
  })

  // ── SSE connection state ──────────────────────────────────────────────────

  it('connection sequence: disconnected → reconnecting → connected', () => {
    // Simulate disconnect
    store().setSSEConnected(false)
    store().setReconnecting(true)
    expect(store().sseConnected).toBe(false)
    expect(store().sseReconnecting).toBe(true)

    // Simulate successful reconnect
    store().setSSEConnected(true)
    store().setReconnecting(false)
    expect(store().sseConnected).toBe(true)
    expect(store().sseReconnecting).toBe(false)
  })

  it('sseConnected and sseReconnecting are independent fields', () => {
    store().setSSEConnected(true)
    store().setReconnecting(true)
    expect(store().sseConnected).toBe(true)
    expect(store().sseReconnecting).toBe(true)
  })

  // ── systemHealth ──────────────────────────────────────────────────────────

  it('setSystemHealth reflects health status changes', () => {
    store().setSystemHealth('degraded')
    expect(store().systemHealth).toBe('degraded')
    store().setSystemHealth('critical')
    expect(store().systemHealth).toBe('critical')
    store().setSystemHealth('healthy')
    expect(store().systemHealth).toBe('healthy')
  })

  // ── dismissedSuggestions ──────────────────────────────────────────────────

  it('dismissSuggestion accumulates dismissed IDs', () => {
    store().dismissSuggestion('hint-translate')
    store().dismissSuggestion('hint-embed')
    expect(store().dismissedSuggestions).toHaveLength(2)
    expect(store().dismissedSuggestions).toContain('hint-translate')
  })

  // ── state isolation ───────────────────────────────────────────────────────

  it('each test starts with fresh defaults (beforeEach verification)', () => {
    expect(store().currentPage).toBe('/')
    expect(store().sseConnected).toBe(false)
    expect(store().systemHealth).toBe('healthy')
  })
})
