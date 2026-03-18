import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Dialog } from '../Dialog'

describe('Dialog', () => {
  it('open=false renders nothing', () => {
    const { container } = render(
      <Dialog open={false} onClose={() => {}} title="Test">
        <p>Body</p>
      </Dialog>,
    )
    expect(screen.queryByText('Test')).not.toBeInTheDocument()
    expect(container.innerHTML).toBe('')
  })

  it('open=true renders title and content', () => {
    render(
      <Dialog open onClose={() => {}} title="Test Dialog">
        <p>Dialog body</p>
      </Dialog>,
    )
    expect(screen.getByText('Test Dialog')).toBeInTheDocument()
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

  it('close button calls onClose', () => {
    const onClose = vi.fn()
    render(
      <Dialog open onClose={onClose} title="T">
        <p>Content</p>
      </Dialog>,
    )
    fireEvent.click(screen.getByLabelText('Close dialog'))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('size prop renders without crashing', () => {
    render(
      <Dialog open onClose={() => {}} title="T" size="lg">
        <p>Content</p>
      </Dialog>,
    )
    expect(screen.getByText('T')).toBeInTheDocument()
  })
})
