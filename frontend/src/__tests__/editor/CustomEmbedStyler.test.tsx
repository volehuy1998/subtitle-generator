import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CustomEmbedStyler, type EmbedStyle } from '../../components/editor/CustomEmbedStyler'

const defaultStyle: EmbedStyle = {
  fontName: 'Arial',
  fontSize: 24,
  fontColor: '#ffffff',
  bold: false,
  position: 'bottom',
  backgroundOpacity: 0.5,
}

describe('CustomEmbedStyler', () => {
  it('renders all style controls', () => {
    render(<CustomEmbedStyler style={defaultStyle} onChange={() => {}} />)
    expect(screen.getByText('Custom style')).toBeDefined()
    expect(screen.getByText('Font name')).toBeDefined()
    expect(screen.getByText('Font size')).toBeDefined()
    expect(screen.getByText('Font color')).toBeDefined()
    expect(screen.getByText('Bold')).toBeDefined()
    expect(screen.getByText('Position')).toBeDefined()
    expect(screen.getByText('Background opacity')).toBeDefined()
  })

  it('calls onChange when font name is changed', () => {
    const onChange = vi.fn()
    render(<CustomEmbedStyler style={defaultStyle} onChange={onChange} />)
    const fontInput = screen.getByDisplayValue('Arial')
    fireEvent.change(fontInput, { target: { value: 'Helvetica' } })
    expect(onChange).toHaveBeenCalledWith({ ...defaultStyle, fontName: 'Helvetica' })
  })

  it('calls onChange when bold switch is toggled', () => {
    const onChange = vi.fn()
    render(<CustomEmbedStyler style={defaultStyle} onChange={onChange} />)
    const boldSwitch = screen.getByRole('switch', { name: /bold/i })
    fireEvent.click(boldSwitch)
    expect(onChange).toHaveBeenCalledWith({ ...defaultStyle, bold: true })
  })

  it('calls onChange when position select is changed', () => {
    const onChange = vi.fn()
    render(<CustomEmbedStyler style={defaultStyle} onChange={onChange} />)
    const posSelect = screen.getByLabelText('Position')
    fireEvent.change(posSelect, { target: { value: 'top' } })
    expect(onChange).toHaveBeenCalledWith({ ...defaultStyle, position: 'top' })
  })

  it('displays current font size value', () => {
    render(<CustomEmbedStyler style={defaultStyle} onChange={() => {}} />)
    expect(screen.getByText('24pt')).toBeDefined()
  })
})
