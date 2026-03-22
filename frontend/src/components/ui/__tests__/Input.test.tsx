import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Input } from '../Input'

describe('Input', () => {
  it('no label renders no label element', () => {
    render(<Input />)
    expect(screen.queryByRole('textbox')).toBeInTheDocument()
    // No label element
    const labels = document.querySelectorAll('label')
    expect(labels.length).toBe(0)
  })

  it('label present with correct htmlFor', () => {
    render(<Input label="Email" />)
    const label = screen.getByText('Email')
    expect(label.tagName).toBe('LABEL')
    const input = screen.getByRole('textbox')
    expect(label).toHaveAttribute('for', input.id)
  })

  it('error text shown, helperText hidden when error present', () => {
    render(<Input error="Required" helperText="Enter your name" />)
    expect(screen.getByText('Required')).toBeInTheDocument()
    expect(screen.queryByText('Enter your name')).not.toBeInTheDocument()
  })

  it('helperText shown when no error', () => {
    render(<Input helperText="Enter your name" />)
    expect(screen.getByText('Enter your name')).toBeInTheDocument()
  })

  it('error styling applies danger border', () => {
    render(<Input error="Bad" />)
    const input = screen.getByRole('textbox')
    expect(input.style.border).toContain('var(--color-danger)')
  })

  it('onChange fires on user typing', () => {
    const handler = vi.fn()
    render(<Input onChange={handler} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'hello' } })
    expect(handler).toHaveBeenCalled()
  })

  it('disabled passthrough', () => {
    render(<Input disabled />)
    expect(screen.getByRole('textbox')).toBeDisabled()
  })
})
