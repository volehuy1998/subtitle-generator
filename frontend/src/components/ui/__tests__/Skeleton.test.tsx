import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { Skeleton } from '../Skeleton'

describe('Skeleton', () => {
  it('renders with aria-hidden', () => {
    const { container } = render(<Skeleton />)
    const el = container.firstElementChild as HTMLElement
    expect(el.getAttribute('aria-hidden')).toBe('true')
  })

  it('applies skeleton class for shimmer animation', () => {
    const { container } = render(<Skeleton />)
    const el = container.firstElementChild as HTMLElement
    expect(el.className).toContain('skeleton')
  })

  it('custom width applied via style', () => {
    const { container } = render(<Skeleton width="200px" />)
    const el = container.firstElementChild as HTMLElement
    expect(el.style.width).toBe('200px')
  })

  it('custom height applied via style', () => {
    const { container } = render(<Skeleton height="32px" />)
    const el = container.firstElementChild as HTMLElement
    expect(el.style.height).toBe('32px')
  })

  it('merges className via cn', () => {
    const { container } = render(<Skeleton className="my-custom-class" />)
    const el = container.firstElementChild as HTMLElement
    expect(el.className).toContain('my-custom-class')
  })
})
