import { create } from 'zustand'

export type AppMode = 'transcribe' | 'embed'
export type EmbedMode = 'soft' | 'hard'

interface UIState {
  appMode: AppMode
  embedMode: EmbedMode
  healthPanelOpen: boolean
  taskQueueOpen: boolean
  sseConnected: boolean
  reconnecting: boolean
  dbOk: boolean
}

interface UIActions {
  setAppMode: (mode: AppMode) => void
  setEmbedMode: (mode: EmbedMode) => void
  setHealthPanelOpen: (open: boolean) => void
  setTaskQueueOpen: (open: boolean) => void
  setSseConnected: (connected: boolean) => void
  setReconnecting: (reconnecting: boolean) => void
  setDbOk: (ok: boolean) => void
}

export const useUIStore = create<UIState & UIActions>((set) => ({
  appMode: 'transcribe',
  embedMode: 'soft',
  healthPanelOpen: false,
  taskQueueOpen: false,
  sseConnected: false,
  reconnecting: false,
  dbOk: true,

  setAppMode: (mode) => set({ appMode: mode }),
  setEmbedMode: (mode) => set({ embedMode: mode }),
  setHealthPanelOpen: (open) => set({ healthPanelOpen: open }),
  setTaskQueueOpen: (open) => set({ taskQueueOpen: open }),
  setSseConnected: (connected) => set({ sseConnected: connected }),
  setReconnecting: (reconnecting) => set({ reconnecting }),
  setDbOk: (ok) => set({ dbOk: ok }),
}))
