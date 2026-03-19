import { describe, it, expect, vi } from 'vitest'
import { render, fireEvent } from '@testing-library/react'
import { Switch } from '../../components/ui/Switch'

describe('Switch', () => {
  it('renders with label', () => {
    const { getByText } = render(<Switch checked={false} onChange={() => {}} label="Enable" />)
    expect(getByText('Enable')).toBeTruthy()
  })

  it('renders description text', () => {
    const { getByText } = render(
      <Switch checked={false} onChange={() => {}} label="Enable" description="Turns on the feature" />
    )
    expect(getByText('Turns on the feature')).toBeTruthy()
  })

  it('calls onChange when clicked', () => {
    const onChange = vi.fn()
    const { getByRole } = render(<Switch checked={false} onChange={onChange} label="Toggle" />)
    fireEvent.click(getByRole('switch'))
    expect(onChange).toHaveBeenCalledWith(true)
  })

  it('has correct aria-checked when on', () => {
    const { getByRole } = render(<Switch checked={true} onChange={() => {}} />)
    expect(getByRole('switch').getAttribute('aria-checked')).toBe('true')
  })

  it('has correct aria-checked when off', () => {
    const { getByRole } = render(<Switch checked={false} onChange={() => {}} />)
    expect(getByRole('switch').getAttribute('aria-checked')).toBe('false')
  })

  it('is disabled when disabled prop is set', () => {
    const onChange = vi.fn()
    const { getByRole } = render(<Switch checked={false} onChange={onChange} disabled />)
    const btn = getByRole('switch')
    expect(btn.hasAttribute('disabled')).toBe(true)
  })
})
