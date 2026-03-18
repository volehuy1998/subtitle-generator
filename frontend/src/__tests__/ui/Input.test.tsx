import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'

describe('Input', () => {
  it('renders label associated with input', () => {
    render(<Input label="Email" />)
    const label = screen.getByText('Email')
    const input = screen.getByRole('textbox')
    expect(label).toBeDefined()
    expect(input).toBeDefined()
  })

  it('displays error message', () => {
    render(<Input label="Email" error="Required" />)
    expect(screen.getByText('Required')).toBeDefined()
  })

  it('calls onChange callback', () => {
    const fn = vi.fn()
    render(<Input onChange={fn} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'hello' } })
    expect(fn).toHaveBeenCalled()
  })

  it('displays helper text', () => {
    render(<Input helperText="Use your work email" />)
    expect(screen.getByText('Use your work email')).toBeDefined()
  })
})

describe('Select', () => {
  const options = [{ value: 'a', label: 'Option A' }, { value: 'b', label: 'Option B' }]

  it('renders options', () => {
    render(<Select options={options} />)
    expect(screen.getByRole('combobox')).toBeDefined()
    expect(screen.getByText('Option A')).toBeDefined()
  })

  it('renders label', () => {
    render(<Select label="Language" options={options} />)
    expect(screen.getByText('Language')).toBeDefined()
  })

  it('shows error', () => {
    render(<Select label="L" options={options} error="Pick one" />)
    expect(screen.getByText('Pick one')).toBeDefined()
  })
})
