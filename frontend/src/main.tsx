import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import MainApp from './pages/App'
import StatusPage from './pages/StatusPage'

async function bootstrap() {
  // Activate MSW service worker in dev mode when VITE_MOCK=true.
  // One-time setup after cloning: cd frontend && npx msw init public/ --save
  // Then run: VITE_MOCK=true npm run dev
  if (import.meta.env.DEV && import.meta.env.VITE_MOCK === 'true') {
    const { worker } = await import('./mocks/browser')
    await worker.start({ onUnhandledRequest: 'bypass' })
    console.info('[MSW] Mock service worker active — backend not required')
  }

  const Page = window.location.pathname === '/status' ? StatusPage : MainApp

  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <Page />
    </StrictMode>,
  )
}

bootstrap()
