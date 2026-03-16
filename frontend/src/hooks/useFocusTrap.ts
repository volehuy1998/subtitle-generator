/**
 * Phase Lumen — Focus trap hook for modal dialogs (Sprint L16).
 *
 * When applied to a dialog container, traps Tab / Shift+Tab cycling
 * within the focusable elements inside the container. Auto-focuses
 * the first focusable element on mount.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { useEffect, useRef } from 'react'

const FOCUSABLE_SELECTOR =
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

export function useFocusTrap() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const focusables = el.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
    const first = focusables[0]
    const last = focusables[focusables.length - 1]

    first?.focus()

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return
      // Re-query in case DOM changed
      const currentFocusables = el.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
      const currentFirst = currentFocusables[0]
      const currentLast = currentFocusables[currentFocusables.length - 1]

      if (e.shiftKey) {
        if (document.activeElement === currentFirst) {
          e.preventDefault()
          currentLast?.focus()
        }
      } else {
        if (document.activeElement === currentLast) {
          e.preventDefault()
          currentFirst?.focus()
        }
      }
    }

    el.addEventListener('keydown', handleTab)
    return () => el.removeEventListener('keydown', handleTab)
  }, [])

  return ref
}
