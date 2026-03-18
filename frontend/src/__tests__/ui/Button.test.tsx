import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../../components/ui/Button'
import { IconButton } from '../../components/ui/IconButton'
import { X } from 'lucide-react'

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: 'Click me' })).toBeDefined()
  })

  it('calls onClick handler', () => {
    const fn = vi.fn()
    render(<Button onClick={fn}>Go</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(fn).toHaveBeenCalledOnce()
  })

  it('is disabled when disabled prop set', () => {
    render(<Button disabled>Locked</Button>)
    const btn = screen.getByRole('button') as HTMLButtonElement
    expect(btn.disabled).toBe(true)
  })

  it('is disabled when loading', () => {
    render(<Button loading>Save</Button>)
    const btn = screen.getByRole('button') as HTMLButtonElement
    expect(btn.disabled).toBe(true)
  })

  it('does not fire onClick when disabled', () => {
    const fn = vi.fn()
    render(<Button disabled onClick={fn}>Nope</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(fn).not.toHaveBeenCalled()
  })
})

describe('IconButton', () => {
  it('renders with aria-label', () => {
    render(<IconButton icon={<X />} aria-label="Close" />)
    expect(screen.getByRole('button', { name: 'Close' })).toBeDefined()
  })

  it('calls onClick handler', () => {
    const fn = vi.fn()
    render(<IconButton icon={<X />} aria-label="Close" onClick={fn} />)
    fireEvent.click(screen.getByRole('button'))
    expect(fn).toHaveBeenCalledOnce()
  })

  it('is disabled when disabled prop set', () => {
    render(<IconButton icon={<X />} aria-label="Close" disabled />)
    const btn = screen.getByRole('button') as HTMLButtonElement
    expect(btn.disabled).toBe(true)
  })
})
