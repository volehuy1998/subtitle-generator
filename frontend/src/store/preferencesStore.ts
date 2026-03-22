import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface PreferencesState {
  // General
  preferredFormat: 'srt' | 'vtt' | 'json'
  maxLineChars: number
  defaultModel: 'tiny' | 'base' | 'small' | 'medium' | 'large' | 'auto'
  defaultLanguage: string

  // Transcription
  wordTimestamps: boolean
  initialPrompt: string
  diarizeByDefault: boolean
  numSpeakers: number | null

  // Embed
  defaultEmbedMode: 'soft' | 'hard'
  defaultEmbedPreset: string
  customFontName: string
  customFontSize: number
  customFontColor: string
  customBold: boolean
  customPosition: 'top' | 'center' | 'bottom'
  customBackgroundOpacity: number

  // Appearance
  theme: 'light' | 'dark' | 'system'

  // Legacy fields (used by existing components on prod-editorial-nav)
  defaultFormat: 'srt' | 'vtt' | 'json'
  autoCopy: boolean

  // Actions
  setPreference: <K extends keyof PreferencesState>(key: K, value: PreferencesState[K]) => void
  setPreferredFormat: (format: 'srt' | 'vtt' | 'json') => void
  setMaxLineChars: (chars: number) => void
  reset: () => void
  resetPreferences: () => void
}

const defaults = {
  preferredFormat: 'srt' as const,
  maxLineChars: 42,
  defaultModel: 'auto' as const,
  defaultLanguage: 'auto',

  wordTimestamps: false,
  initialPrompt: '',
  diarizeByDefault: false,
  numSpeakers: null,

  defaultEmbedMode: 'soft' as const,
  defaultEmbedPreset: 'default',
  customFontName: 'Arial',
  customFontSize: 24,
  customFontColor: '#FFFFFF',
  customBold: false,
  customPosition: 'bottom' as const,
  customBackgroundOpacity: 0.5,

  theme: 'system' as const,

  // Legacy
  defaultFormat: 'srt' as const,
  autoCopy: false,
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      ...defaults,
      setPreference: (key, value) =>
        set({ [key]: value } as Partial<PreferencesState>),
      setPreferredFormat: (format) => set({ preferredFormat: format }),
      setMaxLineChars: (chars) => set({ maxLineChars: chars }),
      reset: () => set(defaults),
      resetPreferences: () => set(defaults),
    }),
    { name: 'sg-preferences' }
  )
)
