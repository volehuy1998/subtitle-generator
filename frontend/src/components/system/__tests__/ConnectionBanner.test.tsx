import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { useUIStore } from '@/store/uiStore'
import { ConnectionBanner } from '../ConnectionBanner'

beforeEach(() => {
  useUIStore.setState({ sseConnected: true, reconnecting: false, dbOk: true })
})

describe('ConnectionBanner', () => {
  it('renders nothing when connected and dbOk', () => {
    useUIStore.setState({ sseConnected: true, reconnecting: false, dbOk: true })
    const { container } = render(<ConnectionBanner />)
    expect(container.innerHTML).toBe('')
  })

  it('shows reconnecting banner when reconnecting', () => {
    useUIStore.setState({ sseConnected: false, reconnecting: true, dbOk: true })
    render(<ConnectionBanner />)
    expect(screen.getByText(/Reconnecting in/)).toBeInTheDocument()
  })

  it('shows danger banner when DB is down', () => {
    useUIStore.setState({ sseConnected: true, reconnecting: false, dbOk: false })
    render(<ConnectionBanner />)
    expect(screen.getByText(/Database unavailable/)).toBeInTheDocument()
  })

  it('DB down has role="alert"', () => {
    useUIStore.setState({ sseConnected: true, reconnecting: false, dbOk: false })
    render(<ConnectionBanner />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('DB down takes priority over reconnecting', () => {
    // sseConnected=true + dbOk=false means isDbDown=true
    useUIStore.setState({ sseConnected: true, reconnecting: false, dbOk: false })
    render(<ConnectionBanner />)
    expect(screen.getByText(/Database unavailable/)).toBeInTheDocument()
    expect(screen.queryByText(/Reconnecting/)).not.toBeInTheDocument()
  })

  it('shows reconnect now button when disconnected', () => {
    useUIStore.setState({ sseConnected: false, reconnecting: false, dbOk: true })
    render(<ConnectionBanner />)
    expect(screen.getByText('Reconnect Now')).toBeInTheDocument()
  })
})
