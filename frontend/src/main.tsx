import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { Router } from './Router'
import { ErrorBoundary } from './components/system/ErrorBoundary'
import { ToastContainer } from './components/ui/ToastContainer'
import { TooltipProvider } from './components/ui/Tooltip'

async function bootstrap() {
  if (import.meta.env.DEV && import.meta.env.VITE_MOCK === 'true') {
    const { worker } = await import('./mocks/browser')
    await worker.start({ onUnhandledRequest: 'bypass' })
  }

  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <ErrorBoundary>
        <TooltipProvider>
          <Router />
          <ToastContainer />
        </TooltipProvider>
      </ErrorBoundary>
    </StrictMode>,
  )
}

bootstrap()
