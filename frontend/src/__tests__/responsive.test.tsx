/**
 * Responsive layout tests — verifies structural CSS classes and
 * key content elements for Drop, See, Refine components.
 *
 * — Scout (QA Lead), Task 42
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { UploadZone } from '../components/landing/UploadZone'
import { Footer } from '../components/layout/Footer'

// Footer uses navigate — mock to avoid jsdom pushState side effects
vi.mock('../navigation', () => ({
  navigate: vi.fn(),
  matchRoute: vi.fn().mockReturnValue({ page: 'landing', params: {} }),
}))

describe('Responsive layout', () => {
  it('UploadZone renders with full-width class', () => {
    const { container } = render(<UploadZone onUpload={() => {}} />)
    const zone = container.firstChild as HTMLElement
    expect(zone?.className).toContain('w-full')
  })

  it('UploadZone has button role for keyboard accessibility', () => {
    render(<UploadZone onUpload={() => {}} />)
    expect(screen.getByRole('button', { name: /upload file/i })).toBeDefined()
  })

  it('UploadZone renders file type hints', () => {
    render(<UploadZone onUpload={() => {}} />)
    expect(screen.getByText(/mp4/i)).toBeDefined()
  })

  it('UploadZone shows 2GB limit text', () => {
    render(<UploadZone onUpload={() => {}} />)
    expect(screen.getByText(/2gb/i)).toBeDefined()
  })

  it('Footer renders nav links', () => {
    render(<Footer />)
    expect(screen.getByText('About')).toBeDefined()
    expect(screen.getByText('Status')).toBeDefined()
  })

  it('Footer renders Security link', () => {
    render(<Footer />)
    expect(screen.getByText('Security')).toBeDefined()
  })

  it('Footer renders Contact link', () => {
    render(<Footer />)
    expect(screen.getByText('Contact')).toBeDefined()
  })

  it('Footer has footer landmark', () => {
    render(<Footer />)
    expect(screen.getByRole('contentinfo')).toBeDefined()
  })

  it('Footer nav has aria-label', () => {
    render(<Footer />)
    const nav = screen.getByRole('navigation', { name: /footer navigation/i })
    expect(nav).toBeDefined()
  })
})
