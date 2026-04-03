/**
 * System data store — prefetches static data on app load.
 *
 * Fires parallel requests for /languages, /system-info, /api/capabilities,
 * and /api/model-status so downstream components never wait for cold fetches.
 *
 * — Pixel (Sr. Frontend), Phase 4 Perceived Performance
 */

import { create } from 'zustand'
import { api, cachedFetch } from '@/api/client'
import type { SystemInfo, LanguagesResponse, ModelPreloadStatus } from '@/api/types'

export interface Capabilities {
  max_file_size_mb: number
  supported_formats: string[]
  diarization_available: boolean
  translation_available: boolean
  [key: string]: unknown
}

interface SystemState {
  languages: LanguagesResponse | null
  systemInfo: SystemInfo | null
  capabilities: Capabilities | null
  modelStatus: ModelPreloadStatus | null
  isLoaded: boolean
  error: string | null
}

interface SystemActions {
  prefetch: () => Promise<void>
}

const CACHE_5_MIN = 5 * 60 * 1000

export const useSystemStore = create<SystemState & SystemActions>((set, get) => ({
  languages: null,
  systemInfo: null,
  capabilities: null,
  modelStatus: null,
  isLoaded: false,
  error: null,

  prefetch: async () => {
    if (get().isLoaded) return

    try {
      const [languages, systemInfo, capabilities, modelStatus] = await Promise.all([
        api.languages(),
        api.systemInfo(),
        cachedFetch<Capabilities>('sg_cache_capabilities', () => fetch('/api/capabilities').then(r => r.json()), CACHE_5_MIN),
        api.modelStatus(),
      ])
      set({ languages, systemInfo, capabilities, modelStatus, isLoaded: true, error: null })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Prefetch failed', isLoaded: true })
    }
  },
}))
