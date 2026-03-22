import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { Tooltip } from '../Tooltip'

/** Helper: get the outermost wrapper div that has the mouse/focus event handlers */
function getWrapper(container: HTMLElement): HTMLElement {
  // The Tooltip renders a single root <div style="position: relative; display: inline-flex;">
  return container.firstElementChild as HTMLElement
}

describe('Tooltip', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('tooltip hidden initially', () => {
    render(<Tooltip content="Help text"><button>Hover me</button></Tooltip>)
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('mouse enter after delay shows tooltip', () => {
    const { container } = render(
      <Tooltip content="Help text" delay={300}><button>Hover me</button></Tooltip>,
    )
    const wrapper = getWrapper(container)
    fireEvent.mouseEnter(wrapper)
    // Before delay — not visible
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
    // After delay
    act(() => { vi.advanceTimersByTime(300) })
    expect(screen.getByRole('tooltip')).toHaveTextContent('Help text')
  })

  it('mouse leave hides tooltip', () => {
    const { container } = render(
      <Tooltip content="Help text" delay={0}><button>Hover me</button></Tooltip>,
    )
    const wrapper = getWrapper(container)
    fireEvent.mouseEnter(wrapper)
    act(() => { vi.advanceTimersByTime(0) })
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    fireEvent.mouseLeave(wrapper)
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('role="tooltip" on visible tooltip', () => {
    const { container } = render(
      <Tooltip content="Tip" delay={0}><span>Target</span></Tooltip>,
    )
    const wrapper = getWrapper(container)
    fireEvent.mouseEnter(wrapper)
    act(() => { vi.advanceTimersByTime(0) })
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
  })

  it('focus shows tooltip, blur hides it', () => {
    const { container } = render(
      <Tooltip content="Focus tip" delay={0}><button>Focusable</button></Tooltip>,
    )
    const wrapper = getWrapper(container)
    fireEvent.focus(wrapper)
    act(() => { vi.advanceTimersByTime(0) })
    expect(screen.getByRole('tooltip')).toHaveTextContent('Focus tip')
    fireEvent.blur(wrapper)
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })
})
