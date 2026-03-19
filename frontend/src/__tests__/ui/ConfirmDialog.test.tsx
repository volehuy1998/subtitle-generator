import { describe, it, expect, vi } from 'vitest'
import { render, fireEvent } from '@testing-library/react'
import { ConfirmDialog } from '../../components/ui/ConfirmDialog'

describe('ConfirmDialog', () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    onConfirm: vi.fn(),
    title: 'Delete item?',
    description: 'This action cannot be undone.',
  }

  it('renders title and description when open', () => {
    const { getByText } = render(<ConfirmDialog {...defaultProps} />)
    expect(getByText('Delete item?')).toBeTruthy()
    expect(getByText('This action cannot be undone.')).toBeTruthy()
  })

  it('does not render when closed', () => {
    const { queryByText } = render(<ConfirmDialog {...defaultProps} open={false} />)
    expect(queryByText('Delete item?')).toBeNull()
  })

  it('calls onConfirm when confirm button clicked', () => {
    const onConfirm = vi.fn()
    const { getByText } = render(<ConfirmDialog {...defaultProps} onConfirm={onConfirm} />)
    fireEvent.click(getByText('Confirm'))
    expect(onConfirm).toHaveBeenCalled()
  })

  it('calls onClose when cancel button clicked', () => {
    const onClose = vi.fn()
    const { getByText } = render(<ConfirmDialog {...defaultProps} onClose={onClose} />)
    fireEvent.click(getByText('Cancel'))
    expect(onClose).toHaveBeenCalled()
  })

  it('uses custom labels', () => {
    const { getByText } = render(
      <ConfirmDialog {...defaultProps} confirmLabel="Yes, delete" cancelLabel="No, keep" />
    )
    expect(getByText('Yes, delete')).toBeTruthy()
    expect(getByText('No, keep')).toBeTruthy()
  })
})
