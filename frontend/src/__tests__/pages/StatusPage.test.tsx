/**
 * StatusPage tests — system status dashboard with live metrics.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusPage } from '../../pages/StatusPage'
import { useUIStore } from '../../store/uiStore'

// Mock AppShell and PageLayout to isolate StatusPage rendering
vi.mock('../../components/layout/AppShell', () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => <div data-testid="app-shell">{children}</div>,
}))
vi.mock('../../components/layout/PageLayout', () => ({
  PageLayout: ({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) => (
    <div>
      <h1>{title}</h1>
      {subtitle && <p>{subtitle}</p>}
      {children}
    </div>
  ),
}))

describe('StatusPage', () => {
  beforeEach(() => {
    useUIStore.setState({
      systemHealth: 'healthy',
      healthStreamConnected: true,
      healthMetrics: {
        cpuPercent: 45.2,
        memoryPercent: 62.1,
        diskPercent: 30.5,
        diskFreeGb: 150.3,
        activeTasks: 0,
        lastUpdated: Date.now(),
      },
      modelPreloadStatus: {},
    })
  })

  it('renders System Status heading', () => {
    render(<StatusPage />)
    expect(screen.getByText('System Status')).toBeDefined()
  })

  it('shows All Systems Operational when healthy', () => {
    render(<StatusPage />)
    expect(screen.getByText('All Systems Operational')).toBeDefined()
  })

  it('shows Major Outage when critical', () => {
    useUIStore.setState({ systemHealth: 'critical' })
    render(<StatusPage />)
    expect(screen.getByText('Major Outage')).toBeDefined()
  })

  it('renders all 5 component cards', () => {
    render(<StatusPage />)
    expect(screen.getByText('Transcription Engine')).toBeDefined()
    expect(screen.getByText('Video Combine')).toBeDefined()
    expect(screen.getByText('Web Application')).toBeDefined()
    expect(screen.getByText('Database')).toBeDefined()
    expect(screen.getByText('File Storage')).toBeDefined()
  })

  it('shows loaded models section when models exist', () => {
    useUIStore.setState({ modelPreloadStatus: { large: 'ready', medium: 'loading' } })
    render(<StatusPage />)
    expect(screen.getByText('Loaded Models')).toBeDefined()
    expect(screen.getByText('large')).toBeDefined()
    expect(screen.getByText('ready')).toBeDefined()
    expect(screen.getByText('medium')).toBeDefined()
    expect(screen.getByText('loading')).toBeDefined()
  })
})
