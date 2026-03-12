import { StrictMode, useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import MainApp from './pages/App'
import StatusPage from './pages/StatusPage'
import SecurityPage from './pages/SecurityPage'
import AboutPage from './pages/AboutPage'
import ContactPage from './pages/ContactPage'
import { useHealthStream } from './hooks/useHealthStream'

function getPage(path: string) {
  if (path === '/status') return StatusPage
  if (path === '/security') return SecurityPage
  if (path === '/about') return AboutPage
  if (path === '/contact') return ContactPage
  return MainApp
}

function Router() {
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

  const Page = getPage(path)
  return <Page />
}

async function bootstrap() {
  if (import.meta.env.DEV && import.meta.env.VITE_MOCK === 'true') {
    const { worker } = await import('./mocks/browser')
    await worker.start({ onUnhandledRequest: 'bypass' })
    console.info('[MSW] Mock service worker active — backend not required')
  }

  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <Router />
    </StrictMode>,
  )
}

bootstrap()
