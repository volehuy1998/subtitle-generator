import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import MainApp from './pages/App'
import StatusPage from './pages/StatusPage'

const Page = window.location.pathname === '/status' ? StatusPage : MainApp

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Page />
  </StrictMode>,
)
