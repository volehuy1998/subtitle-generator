import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Card } from '../Card'

describe('Card', () => {
  it('renders children content', () => {
    render(<Card><p>Body content</p></Card>)
    expect(screen.getByText('Body content')).toBeInTheDocument()
  })

  it('title prop renders heading text', () => {
    render(<Card title="My Title">Content</Card>)
    expect(screen.getByText('My Title')).toBeInTheDocument()
  })

  it('subtitle prop renders subtitle text', () => {
    render(<Card title="Title" subtitle="Sub text">Content</Card>)
    expect(screen.getByText('Sub text')).toBeInTheDocument()
  })

  it('no title renders no heading', () => {
    render(<Card>Content</Card>)
    // The title div should not be present
    expect(screen.queryByText('My Title')).not.toBeInTheDocument()
  })

  it('className passthrough works', () => {
    const { container } = render(<Card className="extra">Content</Card>)
    expect(container.firstElementChild!.className).toContain('extra')
    expect(container.firstElementChild!.className).toContain('card')
  })

  it.each(['default', 'bordered', 'elevated'] as const)(
    'variant=%s renders without crashing',
    (variant) => {
      const { container } = render(<Card variant={variant}>Content</Card>)
      expect(container.firstElementChild).toBeInTheDocument()
    },
  )

  it.each(['sm', 'md', 'lg'] as const)(
    'padding=%s renders without crashing',
    (padding) => {
      const { container } = render(<Card padding={padding}>Content</Card>)
      expect(container.firstElementChild).toBeInTheDocument()
    },
  )
})
