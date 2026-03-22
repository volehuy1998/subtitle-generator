import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Select } from '../Select'

const options = [
  { value: 'en', label: 'English' },
  { value: 'fr', label: 'French' },
  { value: 'es', label: 'Spanish' },
]

describe('Select', () => {
  it('renders all options', () => {
    render(<Select options={options} />)
    expect(screen.getByText('English')).toBeInTheDocument()
    expect(screen.getByText('French')).toBeInTheDocument()
    expect(screen.getByText('Spanish')).toBeInTheDocument()
  })

  it('placeholder renders as disabled option', () => {
    render(<Select options={options} placeholder="Choose language" />)
    const placeholder = screen.getByText('Choose language') as HTMLOptionElement
    expect(placeholder.tagName).toBe('OPTION')
    expect(placeholder).toBeDisabled()
  })

  it('no placeholder renders no empty option', () => {
    render(<Select options={options} />)
    const allOptions = screen.getAllByRole('option')
    expect(allOptions.length).toBe(3)
  })

  it('label rendered with htmlFor', () => {
    render(<Select options={options} label="Language" />)
    const label = screen.getByText('Language')
    expect(label.tagName).toBe('LABEL')
    const select = screen.getByRole('combobox')
    expect(label).toHaveAttribute('for', select.id)
  })

  it('error shown', () => {
    render(<Select options={options} error="Selection required" />)
    expect(screen.getByText('Selection required')).toBeInTheDocument()
  })

  it('onChange fires on selection', () => {
    const handler = vi.fn()
    render(<Select options={options} onChange={handler} />)
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'fr' } })
    expect(handler).toHaveBeenCalled()
  })
})
