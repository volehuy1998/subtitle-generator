/**
 * Theme hook — manages light/dark/system preference with localStorage persistence.
 *
 * - 'system': follows OS prefers-color-scheme (no data-theme attribute)
 * - 'dark': forces dark mode via data-theme="dark"
 * - 'light': forces light mode via data-theme="light"
 *
 * — Pixel (Sr. Frontend Engineer), Sprint L30
 */

import { useState, useEffect } from 'react'

export type Theme = 'light' | 'dark' | 'system'

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'system'
    return (localStorage.getItem('theme') as Theme) || 'system'
  })

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.setAttribute('data-theme', 'dark')
    } else if (theme === 'light') {
      root.setAttribute('data-theme', 'light')
    } else {
      root.removeAttribute('data-theme')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  const setTheme = (t: Theme) => setThemeState(t)

  const cycleTheme = () => {
    setThemeState(prev =>
      prev === 'system' ? 'dark' :
      prev === 'dark' ? 'light' :
      'system'
    )
  }

  return { theme, setTheme, cycleTheme }
}
