import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { Skeleton, SkeletonLine } from '../Skeleton'

describe('Skeleton', () => {
  it('default dimensions (width 100%, height 16px)', () => {
    const { container } = render(<Skeleton />)
    const el = container.firstElementChild as HTMLElement
    expect(el.style.width).toBe('100%')
    expect(el.style.height).toBe('16px')
  })

  it('custom width/height applied', () => {
    const { container } = render(<Skeleton width="200px" height="32px" />)
    const el = container.firstElementChild as HTMLElement
    expect(el.style.width).toBe('200px')
    expect(el.style.height).toBe('32px')
  })
})

describe('SkeletonLine', () => {
  it('renders correct number of lines', () => {
    const { container } = render(<SkeletonLine lines={5} />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBe(5)
  })

  it('last line has reduced width (60%)', () => {
    const { container } = render(<SkeletonLine lines={3} />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    const last = skeletons[skeletons.length - 1] as HTMLElement
    expect(last.style.width).toBe('60%')
    // Non-last lines are 100%
    const first = skeletons[0] as HTMLElement
    expect(first.style.width).toBe('100%')
  })
})
