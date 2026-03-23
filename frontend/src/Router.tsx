/**
 * Router — SPA router with shared layout (Header + Footer on every page).
 *
 * All pages are wrapped in a consistent layout: skip-link,
 * Header, main content, Footer. Individual pages no longer render their own
 * Header/Footer — the Router provides them.
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { useState, useEffect, useMemo } from 'react'
import { useHealthStream } from './hooks/useHealthStream'
import { useUIStore } from './store/uiStore'
import { matchRoute } from './navigation'
import { Header } from './components/layout/Header'
import { Footer } from './components/layout/Footer'
import { App as MainApp } from './pages/App'
import { StatusPage } from './pages/StatusPage'
import { AboutPage } from './pages/AboutPage'
import { SecurityPage } from './pages/SecurityPage'
import { ContactPage } from './pages/ContactPage'
import { SettingsPage } from './pages/SettingsPage'
import CriticalOverlay from './components/system/CriticalOverlay'

function PageContent({ page }: { page: string }) {
  switch (page) {
    case 'status':
      return <StatusPage />
    case 'about':
      return <AboutPage />
    case 'security':
      return <SecurityPage />
    case 'contact':
      return <ContactPage />
    case 'settings':
      return <SettingsPage />
    default:
      return <MainApp />
  }
}

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

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--color-bg)' }}>
      <a href="#main-content" className="sr-only skip-nav">Skip to main content</a>
      <Header />
      <CriticalOverlay />
      <main id="main-content" style={{ flex: 1 }}>
        <PageContent page={route.page} />
      </main>
      <Footer />
    </div>
  )
}
