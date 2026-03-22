import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

// Mock useFocusTrap before importing Dialog
vi.mock('@/hooks/useFocusTrap', () => ({
  useFocusTrap: () => ({ current: null }),
}))

import { Dialog } from '../Dialog'

describe('Dialog', () => {
  it('open=false renders nothing', () => {
    const { container } = render(
      <Dialog open={false} onClose={() => {}} title="Test">
        <p>Body</p>
      </Dialog>,
    )
    expect(container.innerHTML).toBe('')
  })

  it('open=true renders overlay and panel', () => {
    render(
      <Dialog open onClose={() => {}} title="Test Dialog">
        <p>Dialog body</p>
      </Dialog>,
    )
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Dialog body')).toBeInTheDocument()
  })

  it('title and description are displayed', () => {
    render(
      <Dialog open onClose={() => {}} title="Confirm" description="Are you sure?">
        <p>Content</p>
      </Dialog>,
    )
    expect(screen.getByText('Confirm')).toBeInTheDocument()
    expect(screen.getByText('Are you sure?')).toBeInTheDocument()
  })

  it('onClose called on overlay click', () => {
    const onClose = vi.fn()
    render(
      <Dialog open onClose={onClose} title="T">
        <p>Content</p>
      </Dialog>,
    )
    // Click the overlay (the dialog role element itself)
    fireEvent.click(screen.getByRole('dialog'))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('onClose NOT called on panel click (stopPropagation)', () => {
    const onClose = vi.fn()
    render(
      <Dialog open onClose={onClose} title="T">
        <p>Content</p>
      </Dialog>,
    )
    // Click the inner panel content — should not propagate
    fireEvent.click(screen.getByText('Content'))
    expect(onClose).not.toHaveBeenCalled()
  })

  it('Escape key calls onClose', () => {
    const onClose = vi.fn()
    render(
      <Dialog open onClose={onClose} title="T">
        <p>Content</p>
      </Dialog>,
    )
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('has role="dialog" and aria-modal="true"', () => {
    render(
      <Dialog open onClose={() => {}} title="T">
        <p>Content</p>
      </Dialog>,
    )
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
  })

  it('actions slot renders', () => {
    render(
      <Dialog
        open
        onClose={() => {}}
        title="T"
        actions={<button>Confirm</button>}
      >
        <p>Content</p>
      </Dialog>,
    )
    expect(screen.getByText('Confirm')).toBeInTheDocument()
  })
})
