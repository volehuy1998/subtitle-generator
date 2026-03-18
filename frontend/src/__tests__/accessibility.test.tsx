/**
 * Accessibility tests — WCAG 2.1 AA landmark and ARIA attribute checks
 * for Drop, See, Refine components.
 *
 * — Scout (QA Lead), Task 42
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProgressBar } from '../components/ui/ProgressBar'
import { TooltipProvider } from '../components/ui/Tooltip'
import { AppShell } from '../components/layout/AppShell'

// Mock navigate used by Header and Footer
vi.mock('../navigation', () => ({
  navigate: vi.fn(),
  matchRoute: vi.fn().mockReturnValue({ page: 'landing', params: {} }),
}))

function renderWithProviders(ui: React.ReactElement) {
  return render(<TooltipProvider>{ui}</TooltipProvider>)
}

describe('Accessibility', () => {
  it('ProgressBar has progressbar role', () => {
    render(<ProgressBar value={50} />)
    expect(screen.getByRole('progressbar')).toBeDefined()
  })

  it('ProgressBar has aria-valuenow when determinate', () => {
    render(<ProgressBar value={75} />)
    const bar = screen.getByRole('progressbar')
    expect(bar.getAttribute('aria-valuenow')).toBe('75')
  })

  it('ProgressBar has no aria-valuenow when indeterminate', () => {
    render(<ProgressBar />)
    const bar = screen.getByRole('progressbar')
    expect(bar.getAttribute('aria-valuenow')).toBeNull()
  })

  it('ProgressBar aria-valuemin is 0', () => {
    render(<ProgressBar value={50} />)
    const bar = screen.getByRole('progressbar')
    expect(bar.getAttribute('aria-valuemin')).toBe('0')
  })

  it('ProgressBar aria-valuemax is 100', () => {
    render(<ProgressBar value={50} />)
    const bar = screen.getByRole('progressbar')
    expect(bar.getAttribute('aria-valuemax')).toBe('100')
  })

  it('AppShell has skip navigation link', () => {
    renderWithProviders(<AppShell><div>content</div></AppShell>)
    const skipLink = screen.getByText(/skip to main content/i)
    expect(skipLink).toBeDefined()
  })

  it('AppShell has main landmark', () => {
    renderWithProviders(<AppShell><div>content</div></AppShell>)
    expect(screen.getByRole('main')).toBeDefined()
  })

  it('AppShell skip link points to #main-content', () => {
    renderWithProviders(<AppShell><div>content</div></AppShell>)
    const skipLink = screen.getByText(/skip to main content/i)
    expect(skipLink.getAttribute('href')).toBe('#main-content')
  })

  it('AppShell main has id=main-content', () => {
    renderWithProviders(<AppShell><div>content</div></AppShell>)
    const main = screen.getByRole('main')
    expect(main.getAttribute('id')).toBe('main-content')
  })
})
