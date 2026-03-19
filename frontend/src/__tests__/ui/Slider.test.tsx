import { describe, it, expect, vi } from 'vitest'
import { render, fireEvent } from '@testing-library/react'
import { Slider } from '../../components/ui/Slider'

describe('Slider', () => {
  it('renders with label and value display', () => {
    const { getByText } = render(
      <Slider value={42} onChange={() => {}} min={0} max={100} label="Volume" unit="%" />
    )
    expect(getByText('Volume')).toBeTruthy()
    expect(getByText('42%')).toBeTruthy()
  })

  it('renders range input with correct attributes', () => {
    const { container } = render(
      <Slider value={50} onChange={() => {}} min={10} max={200} step={5} />
    )
    const input = container.querySelector('input[type="range"]')!
    expect(input.getAttribute('min')).toBe('10')
    expect(input.getAttribute('max')).toBe('200')
    expect(input.getAttribute('step')).toBe('5')
  })

  it('calls onChange with numeric value', () => {
    const onChange = vi.fn()
    const { container } = render(
      <Slider value={50} onChange={onChange} min={0} max={100} />
    )
    const input = container.querySelector('input[type="range"]')!
    fireEvent.change(input, { target: { value: '75' } })
    expect(onChange).toHaveBeenCalledWith(75)
  })

  it('renders without label', () => {
    const { container } = render(<Slider value={0} onChange={() => {}} min={0} max={10} />)
    expect(container.querySelector('label')).toBeNull()
  })

  it('is disabled when disabled prop set', () => {
    const { container } = render(
      <Slider value={50} onChange={() => {}} min={0} max={100} disabled />
    )
    const input = container.querySelector('input[type="range"]')!
    expect(input.hasAttribute('disabled')).toBe(true)
  })
})
