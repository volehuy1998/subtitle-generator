/**
 * navigation.ts — SPA navigation helpers.
 *
 * Separated from Router.tsx to satisfy react-refresh/only-export-components:
 * Router.tsx must export only components; navigate() lives here so it can be
 * imported by layout components and pages without causing HMR warnings.
 *
 * — Pixel (Senior Frontend Engineer)
 */

/** Programmatic navigation — updates history and fires spa-navigate event. */
export function navigate(path: string) {
  window.history.pushState(null, '', path)
  window.dispatchEvent(new CustomEvent('spa-navigate'))
}

export function matchRoute(path: string): { page: string; params: Record<string, string> } {
  const editorMatch = path.match(/^\/editor\/([^/]+)$/)
  if (editorMatch) return { page: 'editor', params: { id: editorMatch[1] } }
  const routes: Record<string, string> = {
    '/': 'landing',
    '/status': 'status',
    '/about': 'about',
    '/security': 'security',
    '/contact': 'contact',
    '/settings': 'settings',
  }
  return { page: routes[path] ?? 'landing', params: {} }
}
