import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Dialog } from '../../components/ui/Dialog'
import { ConfirmDialog } from '../../components/ui/ConfirmDialog'

describe('Dialog', () => {
  it('renders when open', () => {
    render(<Dialog open={true} onClose={() => {}} title="My Dialog">Content</Dialog>)
    expect(screen.getByText('My Dialog')).toBeDefined()
    expect(screen.getByText('Content')).toBeDefined()
  })

  it('does not render content when closed', () => {
    render(<Dialog open={false} onClose={() => {}} title="Hidden">Secret</Dialog>)
    expect(screen.queryByText('Hidden')).toBeNull()
  })

  it('calls onClose when close button clicked', () => {
    const fn = vi.fn()
    render(<Dialog open={true} onClose={fn} title="Test">X</Dialog>)
    fireEvent.click(screen.getByLabelText('Close dialog'))
    expect(fn).toHaveBeenCalledOnce()
  })
})

describe('ConfirmDialog', () => {
  it('calls onConfirm when confirm button clicked', () => {
    const confirm = vi.fn()
    render(
      <ConfirmDialog open={true} onClose={() => {}} onConfirm={confirm} title="Are you sure?" />
    )
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))
    expect(confirm).toHaveBeenCalledOnce()
  })

  it('calls onClose when cancel clicked', () => {
    const close = vi.fn()
    render(
      <ConfirmDialog open={true} onClose={close} onConfirm={() => {}} title="Delete?" />
    )
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(close).toHaveBeenCalledOnce()
  })
})
