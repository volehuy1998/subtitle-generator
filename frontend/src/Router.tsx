import { useState, useEffect } from 'react'
import { App as MainApp } from './pages/App'
import { StatusPage } from './pages/StatusPage'
import { SecurityPage } from './pages/SecurityPage'
import { AboutPage } from './pages/AboutPage'
import { ContactPage } from './pages/ContactPage'
import { useHealthStream } from './hooks/useHealthStream'

export function Router() {
  const [path, setPath] = useState(window.location.pathname)

  // Single SSE connection shared across all pages — never remounts on navigation
  useHealthStream()

  useEffect(() => {
    const handleNav = () => setPath(window.location.pathname)
    window.addEventListener('popstate', handleNav)
    window.addEventListener('spa-navigate', handleNav)
    return () => {
      window.removeEventListener('popstate', handleNav)
      window.removeEventListener('spa-navigate', handleNav)
    }
  }, [])

  if (path === '/status') return <StatusPage />
  if (path === '/security') return <SecurityPage />
  if (path === '/about') return <AboutPage />
  if (path === '/contact') return <ContactPage />
  return <MainApp />
}
