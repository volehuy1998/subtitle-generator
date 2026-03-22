/**
 * User preferences store — persisted to localStorage.
 *
 * — Pixel (Sr. Frontend), Sprint L47
 */

import { create } from 'zustand'

export interface Preferences {
  defaultModel: string
  defaultFormat: string
  defaultLanguage: string
  autoCopy: boolean
}

interface PreferencesActions {
  setPreference: <K extends keyof Preferences>(key: K, value: Preferences[K]) => void
  resetPreferences: () => void
}

const STORAGE_KEY = 'sg_preferences'

const defaults: Preferences = {
  defaultModel: 'base',
  defaultFormat: 'srt',
  defaultLanguage: 'auto',
  autoCopy: false,
}

function loadPreferences(): Preferences {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaults
    const parsed = JSON.parse(raw) as Partial<Preferences>
    return { ...defaults, ...parsed }
  } catch {
    return defaults
  }
}

function savePreferences(prefs: Preferences) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs))
  } catch {
    // localStorage may be full or unavailable
  }
}

export const usePreferencesStore = create<Preferences & PreferencesActions>((set) => ({
  ...loadPreferences(),

  setPreference: (key, value) => set((s) => {
    const next = { ...s, [key]: value }
    savePreferences({
      defaultModel: next.defaultModel,
      defaultFormat: next.defaultFormat,
      defaultLanguage: next.defaultLanguage,
      autoCopy: next.autoCopy,
    })
    return next
  }),

  resetPreferences: () => {
    savePreferences(defaults)
    set(defaults)
  },
}))
