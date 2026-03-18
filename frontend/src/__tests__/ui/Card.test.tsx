import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Card } from '../../components/ui/Card'

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Content here</Card>)
    expect(screen.getByText('Content here')).toBeDefined()
  })

  it('renders header with title', () => {
    render(<Card header={{ title: 'My Card' }}>Body</Card>)
    expect(screen.getByText('My Card')).toBeDefined()
  })

  it('renders header subtitle', () => {
    render(<Card header={{ title: 'T', subtitle: 'Sub text' }}>B</Card>)
    expect(screen.getByText('Sub text')).toBeDefined()
  })

  it('applies shadow class when shadow=true', () => {
    const { container } = render(<Card shadow>X</Card>)
    expect(container.firstChild).toBeDefined()
    // shadow-md is applied via cn()
    const el = container.firstChild as HTMLElement
    expect(el.className).toContain('shadow-md')
  })

  it('does not apply border class when border=false', () => {
    const { container } = render(<Card border={false}>X</Card>)
    const el = container.firstChild as HTMLElement
    expect(el.className).not.toContain('border-[--color-border]')
  })
})
