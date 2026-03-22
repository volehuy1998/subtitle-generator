import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTheme } from '../useTheme'

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  // ── Initial state ─────────────────────────────────────────────────────────

  it('defaults to system when localStorage is empty', () => {
    const { result } = renderHook(() => useTheme())
    expect(result.current.theme).toBe('system')
  })

  it('reads dark from localStorage on init', () => {
    localStorage.setItem('theme', 'dark')
    const { result } = renderHook(() => useTheme())
    expect(result.current.theme).toBe('dark')
  })

  it('reads light from localStorage on init', () => {
    localStorage.setItem('theme', 'light')
    const { result } = renderHook(() => useTheme())
    expect(result.current.theme).toBe('light')
  })

  // ── setTheme ──────────────────────────────────────────────────────────────

  it('setTheme("dark") sets data-theme attribute and persists', () => {
    const { result } = renderHook(() => useTheme())

    act(() => {
      result.current.setTheme('dark')
    })

    expect(result.current.theme).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(localStorage.getItem('theme')).toBe('dark')
  })

  it('setTheme("light") sets data-theme to light', () => {
    const { result } = renderHook(() => useTheme())

    act(() => {
      result.current.setTheme('light')
    })

    expect(result.current.theme).toBe('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(localStorage.getItem('theme')).toBe('light')
  })

  it('setTheme("system") removes data-theme attribute', () => {
    const { result } = renderHook(() => useTheme())

    // First set to dark
    act(() => {
      result.current.setTheme('dark')
    })
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')

    // Then switch to system
    act(() => {
      result.current.setTheme('system')
    })
    expect(result.current.theme).toBe('system')
    expect(document.documentElement.getAttribute('data-theme')).toBeNull()
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
    expect(localStorage.getItem('theme')).toBeNull()
    expect(document.documentElement.getAttribute('data-theme')).toBeNull()
  })
})
