import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Card } from '../Card'

describe('Card', () => {
  it('renders children content', () => {
    render(<Card><p>Body content</p></Card>)
    expect(screen.getByText('Body content')).toBeInTheDocument()
  })

  it('header.title renders heading text', () => {
    render(<Card header={{ title: 'My Title' }}>Content</Card>)
    expect(screen.getByText('My Title')).toBeInTheDocument()
  })

  it('header.subtitle renders subtitle text', () => {
    render(<Card header={{ title: 'Title', subtitle: 'Sub text' }}>Content</Card>)
    expect(screen.getByText('Sub text')).toBeInTheDocument()
  })

  it('no header renders no heading', () => {
    render(<Card>Content</Card>)
    expect(screen.queryByText('My Title')).not.toBeInTheDocument()
  })

  it('className passthrough works', () => {
    const { container } = render(<Card className="extra">Content</Card>)
    expect(container.firstElementChild!.className).toContain('extra')
  })

  it('shadow=true applies shadow-md class', () => {
    const { container } = render(<Card shadow>Content</Card>)
    expect(container.firstElementChild!.className).toContain('shadow-md')
  })

  it('border=false removes border class', () => {
    const { container } = render(<Card border={false}>Content</Card>)
    expect(container.firstElementChild!.className).not.toContain('border-[--color-border]')
  })

  it.each(['sm', 'md', 'lg', 'none'] as const)(
    'padding=%s renders without crashing',
    (padding) => {
      const { container } = render(<Card padding={padding}>Content</Card>)
      expect(container.firstElementChild).toBeInTheDocument()
    },
  )
})
