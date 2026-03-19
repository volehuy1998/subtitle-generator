import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AdvancedUploadOptions, type UploadOptions } from '../../components/editor/AdvancedUploadOptions'

const defaultOptions: UploadOptions = {
  model: 'auto',
  language: 'auto',
  diarize: false,
  numSpeakers: null,
  wordTimestamps: false,
  initialPrompt: '',
  translateToEnglish: false,
}

describe('AdvancedUploadOptions', () => {
  it('renders collapsed by default', () => {
    render(<AdvancedUploadOptions options={defaultOptions} onChange={() => {}} />)
    expect(screen.getByText('Advanced options')).toBeDefined()
    expect(screen.queryByText('Model')).toBeNull()
  })

  it('expands panel on click and shows all fields', () => {
    render(<AdvancedUploadOptions options={defaultOptions} onChange={() => {}} />)
    fireEvent.click(screen.getByText('Advanced options'))
    expect(screen.getByText('Model')).toBeDefined()
    expect(screen.getByText('Language')).toBeDefined()
    expect(screen.getByText('Speaker diarization')).toBeDefined()
    expect(screen.getByText('Word-level timestamps')).toBeDefined()
    expect(screen.getByText('Translate to English')).toBeDefined()
    expect(screen.getByText('Initial prompt')).toBeDefined()
  })

  it('calls onChange when model is changed', () => {
    const onChange = vi.fn()
    render(<AdvancedUploadOptions options={defaultOptions} onChange={onChange} />)
    fireEvent.click(screen.getByText('Advanced options'))
    const modelSelect = screen.getByLabelText('Model')
    fireEvent.change(modelSelect, { target: { value: 'large' } })
    expect(onChange).toHaveBeenCalledWith({ ...defaultOptions, model: 'large' })
  })

  it('calls onChange when diarization switch is toggled', () => {
    const onChange = vi.fn()
    render(<AdvancedUploadOptions options={defaultOptions} onChange={onChange} />)
    fireEvent.click(screen.getByText('Advanced options'))
    const diarizeSwitch = screen.getByRole('switch', { name: /speaker diarization/i })
    fireEvent.click(diarizeSwitch)
    expect(onChange).toHaveBeenCalledWith({ ...defaultOptions, diarize: true })
  })

  it('sets aria-expanded attribute correctly', () => {
    render(<AdvancedUploadOptions options={defaultOptions} onChange={() => {}} />)
    const toggle = screen.getByText('Advanced options').closest('button')!
    expect(toggle.getAttribute('aria-expanded')).toBe('false')
    fireEvent.click(toggle)
    expect(toggle.getAttribute('aria-expanded')).toBe('true')
  })
})
