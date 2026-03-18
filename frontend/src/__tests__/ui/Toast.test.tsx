import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Toast } from '../../components/ui/Toast'

const baseToast = { id: 't1', type: 'success' as const, title: 'Saved!', duration: 5000 }

describe('Toast', () => {
  it('renders title', () => {
    render(<Toast toast={baseToast} onDismiss={() => {}} />)
    expect(screen.getByText('Saved!')).toBeDefined()
  })

  it('renders description', () => {
    const t = { ...baseToast, description: 'File saved to disk' }
    render(<Toast toast={t} onDismiss={() => {}} />)
    expect(screen.getByText('File saved to disk')).toBeDefined()
  })

  it('calls onDismiss when X clicked', () => {
    const fn = vi.fn()
    render(<Toast toast={baseToast} onDismiss={fn} />)
    fireEvent.click(screen.getByLabelText('Dismiss notification'))
    expect(fn).toHaveBeenCalledWith('t1')
  })

  it('calls action onClick', () => {
    const fn = vi.fn()
    const t = { ...baseToast, action: { label: 'Undo', onClick: fn } }
    render(<Toast toast={t} onDismiss={() => {}} />)
    fireEvent.click(screen.getByRole('button', { name: 'Undo' }))
    expect(fn).toHaveBeenCalledOnce()
  })
})
