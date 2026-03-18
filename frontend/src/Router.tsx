/**
 * Router — Drop, See, Refine SPA router.
 *
 * Handles parameterised routes (/editor/:id), listens for both
 * popstate and spa-navigate events, and syncs the current path
 * into uiStore. The health stream SSE connection is mounted here
 * so it is shared across all pages.
 *
 * navigate() and matchRoute() live in navigation.ts to satisfy
 * react-refresh/only-export-components (Router.tsx exports only components).
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { useState, useEffect, useMemo } from 'react'
import { useHealthStream } from './hooks/useHealthStream'
import { useUIStore } from './store/uiStore'
import { matchRoute } from './navigation'
import { LandingPage } from './pages/LandingPage'
import { EditorPage } from './pages/EditorPage'
import { StatusPage } from './pages/StatusPage'
import { AboutPage } from './pages/AboutPage'
import { SecurityPage } from './pages/SecurityPage'
import { ContactPage } from './pages/ContactPage'

export function Router() {
  const [path, setPath] = useState(window.location.pathname)
  const setCurrentPage = useUIStore((s) => s.setCurrentPage)

  // Single SSE connection shared across all pages — never remounts on navigation
  useHealthStream()

  useEffect(() => {
    const handle = () => setPath(window.location.pathname)
    window.addEventListener('popstate', handle)
    window.addEventListener('spa-navigate', handle as EventListener)
    return () => {
      window.removeEventListener('popstate', handle)
      window.removeEventListener('spa-navigate', handle as EventListener)
    }
  }, [])

  const route = useMemo(() => matchRoute(path), [path])

  useEffect(() => {
    setCurrentPage(path)
  }, [path, setCurrentPage])

  switch (route.page) {
    case 'editor':
      return <EditorPage taskId={route.params.id} />
    case 'status':
      return <StatusPage />
    case 'about':
      return <AboutPage />
    case 'security':
      return <SecurityPage />
    case 'contact':
      return <ContactPage />
    default:
      return <LandingPage />
  }
}
