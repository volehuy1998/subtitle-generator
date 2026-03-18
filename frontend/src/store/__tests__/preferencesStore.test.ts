import { describe, it, expect, beforeEach } from 'vitest'
import { usePreferencesStore } from '../preferencesStore'

const store = () => usePreferencesStore.getState()

describe('preferencesStore', () => {
  beforeEach(() => {
    store().reset()
  })

  // ── Default state ─────────────────────────────────────────────────────────

  it('starts with correct defaults', () => {
    const s = store()
    expect(s.preferredFormat).toBe('srt')
    expect(s.maxLineChars).toBe(42)
  })

  // ── setPreferredFormat ────────────────────────────────────────────────────

  it('setPreferredFormat updates preferred format', () => {
    store().setPreferredFormat('vtt')
    expect(store().preferredFormat).toBe('vtt')
  })

  it('setPreferredFormat updates to json', () => {
    store().setPreferredFormat('json')
    expect(store().preferredFormat).toBe('json')
  })

  it('setPreferredFormat updates to srt', () => {
    store().setPreferredFormat('json')
    store().setPreferredFormat('srt')
    expect(store().preferredFormat).toBe('srt')
  })

  // ── setMaxLineChars ───────────────────────────────────────────────────────

  it('setMaxLineChars updates the value', () => {
    store().setMaxLineChars(60)
    expect(store().maxLineChars).toBe(60)
  })

  // ── reset ─────────────────────────────────────────────────────────────────

  it('reset restores defaults', () => {
    store().setPreferredFormat('vtt')
    store().setMaxLineChars(80)

    store().reset()

    const s = store()
    expect(s.preferredFormat).toBe('srt')
    expect(s.maxLineChars).toBe(42)
  })

  // ── state isolation ───────────────────────────────────────────────────────

  it('each test starts with fresh defaults (beforeEach verification)', () => {
    expect(store().preferredFormat).toBe('srt')
    expect(store().maxLineChars).toBe(42)
  })

  // ── partial stored object ─────────────────────────────────────────────────

  it('partial update preserves other fields', () => {
    store().setPreferredFormat('vtt')
    const s = store()
    expect(s.preferredFormat).toBe('vtt')
    // Other fields should remain at defaults
    expect(s.maxLineChars).toBe(42)
  })
})
