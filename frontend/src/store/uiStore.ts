import { create } from 'zustand'

export type ContextPanelContent = 'info' | 'translate' | 'embed' | 'search'
export type EmbedMode = 'soft' | 'hard'

export interface HealthMetrics {
  cpuPercent: number | null
  memoryPercent: number | null
  diskPercent: number | null
  diskFreeGb: number | null
  activeTasks: number
  lastUpdated: number | null
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type HealthData = any

interface UIState {
  currentPage: string
  contextPanelContent: ContextPanelContent
  sseConnected: boolean
  sseReconnecting: boolean
  healthStreamConnected: boolean
  systemHealth: 'healthy' | 'degraded' | 'critical'
  modelPreloadStatus: Record<string, string>
  healthMetrics: HealthMetrics
  dismissedSuggestions: string[]

  // Legacy fields (used by existing pages on prod-editorial-nav)
  appMode: 'transcribe' | 'embed'
  embedMode: EmbedMode
  healthPanelOpen: boolean
  taskQueueOpen: boolean
  reconnecting: boolean
  dbOk: boolean
  health: HealthData | null

  setCurrentPage: (page: string) => void
  setContextPanel: (content: ContextPanelContent) => void
  setSSEConnected: (connected: boolean) => void
  setSseConnected: (connected: boolean) => void
  setReconnecting: (reconnecting: boolean) => void
  setHealthStreamConnected: (connected: boolean) => void
  setSystemHealth: (health: 'healthy' | 'degraded' | 'critical') => void
  setModelPreloadStatus: (status: Record<string, string>) => void
  setHealthMetrics: (metrics: HealthMetrics) => void
  dismissSuggestion: (id: string) => void
  setAppMode: (mode: 'transcribe' | 'embed') => void
  setEmbedMode: (mode: EmbedMode) => void
  setHealthPanelOpen: (open: boolean) => void
  setTaskQueueOpen: (open: boolean) => void
  setDbOk: (ok: boolean) => void
  setHealth: (health: HealthData) => void
}

export const useUIStore = create<UIState>((set) => ({
  currentPage: '/',
  contextPanelContent: 'info',
  sseConnected: false,
  sseReconnecting: false,
  healthStreamConnected: false,
  systemHealth: 'healthy',
  modelPreloadStatus: {},
  healthMetrics: {
    cpuPercent: null,
    memoryPercent: null,
    diskPercent: null,
    diskFreeGb: null,
    activeTasks: 0,
    lastUpdated: null,
  },
  dismissedSuggestions: [],

  // Legacy fields
  appMode: 'transcribe',
  embedMode: 'soft',
  healthPanelOpen: false,
  taskQueueOpen: false,
  reconnecting: false,
  dbOk: true,
  health: null,

  setCurrentPage: (page) => set({ currentPage: page }),
  setContextPanel: (content) => set({ contextPanelContent: content }),
  setSSEConnected: (connected) => set({ sseConnected: connected }),
  setSseConnected: (connected) => set({ sseConnected: connected }),
  setReconnecting: (reconnecting) => set({ sseReconnecting: reconnecting, reconnecting }),
  setHealthStreamConnected: (connected) => set({ healthStreamConnected: connected }),
  setSystemHealth: (health) => set({ systemHealth: health }),
  setModelPreloadStatus: (status) => set({ modelPreloadStatus: status }),
  setHealthMetrics: (metrics) => set({ healthMetrics: metrics }),
  dismissSuggestion: (id) => set(s => ({
    dismissedSuggestions: [...s.dismissedSuggestions, id],
  })),
  setAppMode: (mode) => set({ appMode: mode }),
  setEmbedMode: (mode) => set({ embedMode: mode }),
  setHealthPanelOpen: (open) => set({ healthPanelOpen: open }),
  setTaskQueueOpen: (open) => set({ taskQueueOpen: open }),
  setDbOk: (ok) => set({ dbOk: ok }),
  setHealth: (health) => set({ health }),
}))
