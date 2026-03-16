import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusIndicator } from '../StatusIndicator'

describe('StatusIndicator', () => {
  it.each(['online', 'offline', 'warning', 'loading', 'idle'] as const)(
    'status=%s renders without crashing',
    (status) => {
      const { container } = render(<StatusIndicator status={status} />)
      expect(container.firstElementChild).toBeInTheDocument()
    },
  )

  it('label prop text visible', () => {
    render(<StatusIndicator status="online" label="Connected" />)
    expect(screen.getByText('Connected')).toBeInTheDocument()
  })

  it('no label renders no text span', () => {
    const { container } = render(<StatusIndicator status="online" />)
    // Only the dot wrapper span, no text span
    const outerSpan = container.firstElementChild!
    // Should have 1 child (the dot container), not 2
    expect(outerSpan.children.length).toBe(1)
  })

  it('online status pulses by default', () => {
    const { container } = render(<StatusIndicator status="online" />)
    const pulseSpan = container.querySelector('.animate-ping')
    expect(pulseSpan).toBeInTheDocument()
  })

  it('pulse=false overrides default pulse', () => {
    const { container } = render(<StatusIndicator status="online" pulse={false} />)
    const pulseSpan = container.querySelector('.animate-ping')
    expect(pulseSpan).not.toBeInTheDocument()
  })

  it('offline does not pulse by default', () => {
    const { container } = render(<StatusIndicator status="offline" />)
    const pulseSpan = container.querySelector('.animate-ping')
    expect(pulseSpan).not.toBeInTheDocument()
  })
})
