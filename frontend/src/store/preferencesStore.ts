import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface PreferencesState {
  preferredFormat: 'srt' | 'vtt' | 'json'
  maxLineChars: number

  setPreferredFormat: (format: 'srt' | 'vtt' | 'json') => void
  setMaxLineChars: (chars: number) => void
  reset: () => void
}

const defaults = {
  preferredFormat: 'srt' as const,
  maxLineChars: 42,
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      ...defaults,
      setPreferredFormat: (format) => set({ preferredFormat: format }),
      setMaxLineChars: (chars) => set({ maxLineChars: chars }),
      reset: () => set(defaults),
    }),
    { name: 'sg-preferences' }
  )
)
