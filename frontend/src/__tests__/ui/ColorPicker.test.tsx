import { describe, it, expect, vi } from 'vitest'
import { render, fireEvent } from '@testing-library/react'
import { ColorPicker } from '../../components/ui/ColorPicker'

describe('ColorPicker', () => {
  it('renders label', () => {
    const { getByText } = render(<ColorPicker value="#FF0000" onChange={() => {}} label="Color" />)
    expect(getByText('Color')).toBeTruthy()
  })

  it('shows current value in text input', () => {
    const { container } = render(<ColorPicker value="#ff0000" onChange={() => {}} />)
    const textInput = container.querySelector('input[type="text"]') as HTMLInputElement
    expect(textInput.value).toBe('#FF0000')
  })

  it('calls onChange from color input', () => {
    const onChange = vi.fn()
    const { container } = render(<ColorPicker value="#000000" onChange={onChange} />)
    const colorInput = container.querySelector('input[type="color"]')!
    fireEvent.change(colorInput, { target: { value: '#123456' } })
    expect(onChange).toHaveBeenCalledWith('#123456')
  })

  it('validates hex input format', () => {
    const onChange = vi.fn()
    const { container } = render(<ColorPicker value="#000000" onChange={onChange} />)
    const textInput = container.querySelector('input[type="text"]')!
    fireEvent.change(textInput, { target: { value: '#GGG' } })
    expect(onChange).not.toHaveBeenCalled()
  })

  it('accepts valid hex from text input', () => {
    const onChange = vi.fn()
    const { container } = render(<ColorPicker value="#000000" onChange={onChange} />)
    const textInput = container.querySelector('input[type="text"]')!
    fireEvent.change(textInput, { target: { value: '#ABC123' } })
    expect(onChange).toHaveBeenCalledWith('#ABC123')
  })
})
