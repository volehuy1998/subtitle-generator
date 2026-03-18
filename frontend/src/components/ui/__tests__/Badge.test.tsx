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
    const dotSpan = spans[0]
    expect(dotSpan).toBeInTheDocument()
    // dot uses Tailwind classes: rounded-full bg-current
    expect((dotSpan as HTMLElement).className).toContain('rounded-full')
  })

  it('dot=false renders no dot', () => {
    const { container } = render(<Badge>Status</Badge>)
    const innerSpans = container.querySelectorAll('span > span')
    expect(innerSpans.length).toBe(0)
  })

  it.each(['default', 'success', 'warning', 'danger', 'info'] as const)(
    'variant=%s renders without crashing',
    (variant) => {
      render(<Badge variant={variant}>Tag</Badge>)
      expect(screen.getByText('Tag')).toBeInTheDocument()
    },
  )

  it('className passthrough works', () => {
    const { container } = render(<Badge className="extra-class">Tag</Badge>)
    expect(container.firstElementChild!.className).toContain('extra-class')
  })
})
