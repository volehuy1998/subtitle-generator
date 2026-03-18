import { describe, it, expect, beforeEach } from 'vitest'
import { usePreferencesStore } from '../../store/preferencesStore'

describe('preferencesStore', () => {
  beforeEach(() => usePreferencesStore.getState().reset())

  it('starts with defaults', () => {
    expect(usePreferencesStore.getState().preferredFormat).toBe('srt')
    expect(usePreferencesStore.getState().maxLineChars).toBe(42)
  })

  it('updates preferred format', () => {
    usePreferencesStore.getState().setPreferredFormat('vtt')
    expect(usePreferencesStore.getState().preferredFormat).toBe('vtt')
  })

  it('updates maxLineChars', () => {
    usePreferencesStore.getState().setMaxLineChars(60)
    expect(usePreferencesStore.getState().maxLineChars).toBe(60)
  })

  it('resets to defaults', () => {
    usePreferencesStore.getState().setPreferredFormat('json')
    usePreferencesStore.getState().reset()
    expect(usePreferencesStore.getState().preferredFormat).toBe('srt')
  })
})
