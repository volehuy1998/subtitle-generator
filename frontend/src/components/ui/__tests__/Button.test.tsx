import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../Button'

describe('Button', () => {
  it('renders children text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('loading=true renders spinner and hides icon', () => {
    const icon = <span data-testid="icon">icon</span>
    const { container } = render(<Button loading icon={icon}>Save</Button>)
    // Spinner present (aria-hidden span)
    const spinner = container.querySelector('span[aria-hidden="true"]')
    expect(spinner).toBeInTheDocument()
    // Icon not rendered when loading
    expect(screen.queryByTestId('icon')).not.toBeInTheDocument()
  })

  it('loading=true makes button disabled', () => {
    render(<Button loading>Save</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('disabled=true sets disabled attribute', () => {
    render(<Button disabled>Save</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('onClick fires when not disabled', () => {
    const handler = vi.fn()
    render(<Button onClick={handler}>Go</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(handler).toHaveBeenCalledOnce()
  })

  it('onClick blocked when loading', () => {
    const handler = vi.fn()
    render(<Button loading onClick={handler}>Go</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(handler).not.toHaveBeenCalled()
  })

  it('className passthrough works', () => {
    render(<Button className="my-class">Btn</Button>)
    expect(screen.getByRole('button').className).toContain('my-class')
  })
})
