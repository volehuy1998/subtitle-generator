import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { Router } from './Router'
import { ErrorBoundary } from './components/system/ErrorBoundary'

async function bootstrap() {
  if (import.meta.env.DEV && import.meta.env.VITE_MOCK === 'true') {
    const { worker } = await import('./mocks/browser')
    await worker.start({ onUnhandledRequest: 'bypass' })
    console.info('[MSW] Mock service worker active — backend not required')
  }

  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <ErrorBoundary>
        <Router />
      </ErrorBoundary>
    </StrictMode>,
  )
}

bootstrap()
