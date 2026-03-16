import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

const mockCycleTheme = vi.fn()

vi.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({ theme: 'system' as const, setTheme: vi.fn(), cycleTheme: mockCycleTheme }),
}))

vi.mock('@/components/settings/PreferencesPanel', () => ({
  PreferencesPanel: () => null,
}))

import { useUIStore } from '@/store/uiStore'
import { AppHeader } from '../AppHeader'

beforeEach(() => {
  mockCycleTheme.mockClear()
  useUIStore.setState({ healthPanelOpen: false, health: null })
})

describe('AppHeader', () => {
  it('renders "SubForge" logo text', () => {
    render(<AppHeader />)
    expect(screen.getByText('SubForge')).toBeInTheDocument()
  })

  it('renders navigation links: App, Status, About', () => {
    render(<AppHeader />)
    expect(screen.getByText('App')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()
  })

  it('renders theme toggle button with aria-label', () => {
    render(<AppHeader />)
    const themeBtn = screen.getByLabelText('System theme')
    expect(themeBtn).toBeInTheDocument()
  })

  it('theme toggle click calls cycleTheme', () => {
    render(<AppHeader />)
    const themeBtn = screen.getByLabelText('System theme')
    fireEvent.click(themeBtn)
    expect(mockCycleTheme).toHaveBeenCalledOnce()
  })

  it('renders a header element', () => {
    render(<AppHeader />)
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })

  it('renders a nav element', () => {
    render(<AppHeader />)
    expect(screen.getByRole('navigation')).toBeInTheDocument()
  })

  it('renders health status button', () => {
    useUIStore.setState({ health: { status: 'healthy', uptime_sec: 0 } })
    render(<AppHeader />)
    expect(screen.getByText('Healthy')).toBeInTheDocument()
  })

  it('shows "Connecting" when health is null', () => {
    useUIStore.setState({ health: null })
    render(<AppHeader />)
    expect(screen.getByText('Connecting')).toBeInTheDocument()
  })
})
