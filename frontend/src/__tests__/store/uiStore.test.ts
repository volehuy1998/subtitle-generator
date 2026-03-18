import { describe, it, expect, beforeEach } from 'vitest'
import { useUIStore } from '../../store/uiStore'

describe('uiStore', () => {
  beforeEach(() => {
    useUIStore.setState({
      currentPage: '/',
      contextPanelContent: 'info',
      sseConnected: false,
      sseReconnecting: false,
      systemHealth: 'healthy',
      modelPreloadStatus: {},
      dismissedSuggestions: [],
    })
  })

  it('sets current page', () => {
    useUIStore.getState().setCurrentPage('/editor/123')
    expect(useUIStore.getState().currentPage).toBe('/editor/123')
  })

  it('sets context panel content', () => {
    useUIStore.getState().setContextPanel('translate')
    expect(useUIStore.getState().contextPanelContent).toBe('translate')
  })

  it('sets SSE connected state', () => {
    useUIStore.getState().setSSEConnected(true)
    expect(useUIStore.getState().sseConnected).toBe(true)
  })

  it('sets system health', () => {
    useUIStore.getState().setSystemHealth('degraded')
    expect(useUIStore.getState().systemHealth).toBe('degraded')
  })

  it('dismisses suggestions', () => {
    useUIStore.getState().dismissSuggestion('hint-translate')
    useUIStore.getState().dismissSuggestion('hint-embed')
    expect(useUIStore.getState().dismissedSuggestions).toHaveLength(2)
    expect(useUIStore.getState().dismissedSuggestions).toContain('hint-translate')
  })
})
