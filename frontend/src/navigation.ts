/**
 * navigation.ts — SPA navigation helper.
 *
 * Centralizes the pushState + spa-navigate event pattern used by
 * layout components. Extracted to keep Header/Footer clean.
 */

/** Programmatic SPA navigation — updates history and fires spa-navigate event. */
export function navigate(path: string) {
  if (window.location.pathname === path) return
  window.history.pushState(null, '', path)
  window.dispatchEvent(new Event('spa-navigate'))
}
