/**
 * Theme hook — syncs with preferencesStore and handles system dark preference.
 *
 * - 'system': follows OS prefers-color-scheme via matchMedia listener
 * - 'dark': forces dark mode via data-theme="dark"
 * - 'light': forces light mode via data-theme="light"
 *
 * — Pixel (Sr. Frontend Engineer), Task 5
 */

import { useEffect } from 'react'
import { usePreferencesStore } from '../store/preferencesStore'

export type Theme = 'light' | 'dark' | 'system'

export function useTheme() {
  const theme = usePreferencesStore((s) => s.theme)
  const setPreference = usePreferencesStore((s) => s.setPreference)

  useEffect(() => {
    const root = document.documentElement

    const applyTheme = () => {
      if (theme === 'dark') {
        root.setAttribute('data-theme', 'dark')
      } else if (theme === 'light') {
        root.setAttribute('data-theme', 'light')
      } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        root.setAttribute('data-theme', prefersDark ? 'dark' : 'light')
      }
    }

    applyTheme()

    if (theme === 'system') {
      const mql = window.matchMedia('(prefers-color-scheme: dark)')
      const handler = () => applyTheme()
      mql.addEventListener('change', handler)
      return () => mql.removeEventListener('change', handler)
    }
  }, [theme])

  const setTheme = (t: Theme) => setPreference('theme', t)
  const cycleTheme = () => {
    setPreference('theme',
      theme === 'system' ? 'dark' :
      theme === 'dark' ? 'light' : 'system'
    )
  }

  return { theme, setTheme, cycleTheme }
}
