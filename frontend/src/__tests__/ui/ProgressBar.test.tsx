import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProgressBar } from '../../components/ui/ProgressBar'

describe('ProgressBar', () => {
  it('renders with aria-valuenow', () => {
    render(<ProgressBar value={45} />)
    const pb = screen.getByRole('progressbar')
    expect(pb.getAttribute('aria-valuenow')).toBe('45')
  })

  it('shows percentage when showPercent=true', () => {
    render(<ProgressBar value={72} showPercent />)
    expect(screen.getByText('72%')).toBeDefined()
  })

  it('renders indeterminate when value undefined', () => {
    render(<ProgressBar />)
    const pb = screen.getByRole('progressbar')
    expect(pb.getAttribute('aria-valuenow')).toBeNull()
  })

  it('renders label', () => {
    render(<ProgressBar value={30} label="Processing..." />)
    expect(screen.getByText('Processing...')).toBeDefined()
  })
})
