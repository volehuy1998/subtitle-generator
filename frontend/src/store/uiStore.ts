import { create } from 'zustand'

export type ContextPanelContent = 'info' | 'translate' | 'embed' | 'search'

interface UIState {
  currentPage: string
  contextPanelContent: ContextPanelContent
  sseConnected: boolean
  sseReconnecting: boolean
  healthStreamConnected: boolean
  systemHealth: 'healthy' | 'degraded' | 'critical'
  modelPreloadStatus: Record<string, string>
  dismissedSuggestions: string[]

  setCurrentPage: (page: string) => void
  setContextPanel: (content: ContextPanelContent) => void
  setSSEConnected: (connected: boolean) => void
  setReconnecting: (reconnecting: boolean) => void
  setHealthStreamConnected: (connected: boolean) => void
  setSystemHealth: (health: 'healthy' | 'degraded' | 'critical') => void
  setModelPreloadStatus: (status: Record<string, string>) => void
  dismissSuggestion: (id: string) => void
}

export const useUIStore = create<UIState>((set) => ({
  currentPage: '/',
  contextPanelContent: 'info',
  sseConnected: false,
  sseReconnecting: false,
  healthStreamConnected: false,
  systemHealth: 'healthy',
  modelPreloadStatus: {},
  dismissedSuggestions: [],

  setCurrentPage: (page) => set({ currentPage: page }),
  setContextPanel: (content) => set({ contextPanelContent: content }),
  setSSEConnected: (connected) => set({ sseConnected: connected }),
  setReconnecting: (reconnecting) => set({ sseReconnecting: reconnecting }),
  setHealthStreamConnected: (connected) => set({ healthStreamConnected: connected }),
  setSystemHealth: (health) => set({ systemHealth: health }),
  setModelPreloadStatus: (status) => set({ modelPreloadStatus: status }),
  dismissSuggestion: (id) => set(s => ({
    dismissedSuggestions: [...s.dismissedSuggestions, id],
  })),
}))
