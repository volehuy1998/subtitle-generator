/**
 * Header tests — sticky navigation bar with logo and nav links.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Header } from '../../components/layout/Header'
import { useUIStore } from '../../store/uiStore'
import * as navigation from '../../navigation'

// Mock child components to isolate Header
vi.mock('../../components/system/HealthIndicator', () => ({
  HealthIndicator: () => <div data-testid="health-indicator" />,
}))
vi.mock('../../components/ui/ThemeToggle', () => ({
  ThemeToggle: () => <div data-testid="theme-toggle" />,
}))

describe('Header', () => {
  beforeEach(() => {
    useUIStore.setState({ currentPage: '/' })
  })

  it('renders SubForge logo text', () => {
    render(<Header />)
    expect(screen.getByText('SubForge')).toBeDefined()
  })

  it('renders Status, Settings, and About nav links', () => {
    render(<Header />)
    expect(screen.getByText('Status')).toBeDefined()
    expect(screen.getByText('Settings')).toBeDefined()
    expect(screen.getByText('About')).toBeDefined()
  })

  it('navigates home when logo is clicked', () => {
    const spy = vi.spyOn(navigation, 'navigate').mockImplementation(() => {})
    render(<Header />)
    fireEvent.click(screen.getByLabelText('SubForge home'))
    expect(spy).toHaveBeenCalledWith('/')
    spy.mockRestore()
  })

  it('navigates to /status when Status link is clicked', () => {
    const spy = vi.spyOn(navigation, 'navigate').mockImplementation(() => {})
    render(<Header />)
    fireEvent.click(screen.getByText('Status'))
    expect(spy).toHaveBeenCalledWith('/status')
    spy.mockRestore()
  })

  it('includes HealthIndicator and ThemeToggle', () => {
    render(<Header />)
    expect(screen.getByTestId('health-indicator')).toBeDefined()
    expect(screen.getByTestId('theme-toggle')).toBeDefined()
  })
})
