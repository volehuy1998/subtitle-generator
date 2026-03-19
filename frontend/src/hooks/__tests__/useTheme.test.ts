import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTheme } from '../useTheme'
import { usePreferencesStore } from '../../store/preferencesStore'

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    // Reset Zustand store to defaults
    usePreferencesStore.getState().reset()

    // Mock matchMedia for jsdom (defaults to light)
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    })
  })

  // ── Initial state ─────────────────────────────────────────────────────────

  it('defaults to system when store is fresh', () => {
    const { result } = renderHook(() => useTheme())
    expect(result.current.theme).toBe('system')
  })

  // ── setTheme ──────────────────────────────────────────────────────────────

  it('setTheme("dark") sets data-theme attribute', () => {
    const { result } = renderHook(() => useTheme())

    act(() => {
      result.current.setTheme('dark')
    })

    expect(result.current.theme).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('setTheme("light") sets data-theme to light', () => {
    const { result } = renderHook(() => useTheme())

    act(() => {
      result.current.setTheme('light')
    })

    expect(result.current.theme).toBe('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('setTheme("system") applies resolved theme from media query', () => {
    const { result } = renderHook(() => useTheme())

    // First set to dark
    act(() => {
      result.current.setTheme('dark')
    })
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')

    // Then switch to system — should resolve to light or dark based on media query
    act(() => {
      result.current.setTheme('system')
    })
    expect(result.current.theme).toBe('system')
    // System mode resolves to a concrete theme via matchMedia
    const resolved = document.documentElement.getAttribute('data-theme')
    expect(['light', 'dark']).toContain(resolved)
  })

  it('persists theme in preferencesStore', () => {
    const { result } = renderHook(() => useTheme())

    act(() => {
      result.current.setTheme('dark')
    })

    expect(usePreferencesStore.getState().theme).toBe('dark')
  })

  // ── cycleTheme ────────────────────────────────────────────────────────────

  it('cycleTheme cycles: system -> dark -> light -> system', () => {
    const { result } = renderHook(() => useTheme())
    expect(result.current.theme).toBe('system')

    act(() => {
      result.current.cycleTheme()
    })
    expect(result.current.theme).toBe('dark')

    act(() => {
      result.current.cycleTheme()
    })
    expect(result.current.theme).toBe('light')

    act(() => {
      result.current.cycleTheme()
    })
    expect(result.current.theme).toBe('system')
  })

  // ── state isolation ───────────────────────────────────────────────────────

  it('each test starts clean (beforeEach verification)', () => {
    expect(usePreferencesStore.getState().theme).toBe('system')
    expect(document.documentElement.getAttribute('data-theme')).toBeNull()
  })
})
