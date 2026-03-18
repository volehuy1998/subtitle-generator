import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { useUIStore } from '@/store/uiStore'
import { ConnectionBanner } from '../ConnectionBanner'

beforeEach(() => {
  useUIStore.setState({ sseConnected: true, sseReconnecting: false, systemHealth: 'healthy', modelPreloadStatus: {} })
})

describe('ConnectionBanner', () => {
  it('renders nothing when healthy, connected, no model loading', () => {
    const { container } = render(<ConnectionBanner />)
    expect(container.innerHTML).toBe('')
  })

  it('shows reconnecting banner when sseReconnecting is true', () => {
    useUIStore.setState({ sseReconnecting: true })
    render(<ConnectionBanner />)
    expect(screen.getByText(/Reconnecting to server/)).toBeInTheDocument()
  })

  it('shows critical banner when systemHealth is critical', () => {
    useUIStore.setState({ systemHealth: 'critical' })
    render(<ConnectionBanner />)
    expect(screen.getByText(/System critical/)).toBeInTheDocument()
  })

  it('critical banner has role="alert"', () => {
    useUIStore.setState({ systemHealth: 'critical' })
    render(<ConnectionBanner />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('critical takes priority over reconnecting', () => {
    useUIStore.setState({ systemHealth: 'critical', sseReconnecting: true })
    render(<ConnectionBanner />)
    expect(screen.getByText(/System critical/)).toBeInTheDocument()
    expect(screen.queryByText(/Reconnecting/)).not.toBeInTheDocument()
  })

  it('shows model loading banner when a model is loading', () => {
    useUIStore.setState({ modelPreloadStatus: { large: 'loading' } })
    render(<ConnectionBanner />)
    expect(screen.getByText(/Loading AI model/)).toBeInTheDocument()
  })

  it('model loading banner not shown when model is loaded', () => {
    useUIStore.setState({ modelPreloadStatus: { large: 'loaded' } })
    const { container } = render(<ConnectionBanner />)
    expect(container.innerHTML).toBe('')
  })
})
