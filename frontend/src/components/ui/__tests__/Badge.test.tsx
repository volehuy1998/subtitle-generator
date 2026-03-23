import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Badge } from '../Badge'

describe('Badge', () => {
  it('renders children text', () => {
    render(<Badge>Active</Badge>)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('dot=true renders dot span', () => {
    const { container } = render(<Badge dot>Status</Badge>)
    // The outer span contains a dot span (small circle) + text
    const spans = container.querySelectorAll('span > span')
    // First inner span is the dot
    const dotSpan = spans[0]
    expect(dotSpan).toBeInTheDocument()
    expect((dotSpan as HTMLElement).style.borderRadius).toBe('50%')
  })

  it('dot=false renders no dot', () => {
    const { container } = render(<Badge>Status</Badge>)
    const innerSpans = container.querySelectorAll('span > span')
    // No inner span elements — only text node inside the outer span
    expect(innerSpans.length).toBe(0)
  })

})
