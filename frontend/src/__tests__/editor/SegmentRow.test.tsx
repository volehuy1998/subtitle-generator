import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SegmentRow } from '../../components/editor/SegmentRow'

describe('SegmentRow', () => {
  const segment = { index: 0, start: 1.5, end: 4.8, text: 'Hello world' }

  it('renders timecodes and text', () => {
    render(<SegmentRow segment={segment} onEdit={() => {}} />)
    expect(screen.getByText('00:00:01')).toBeDefined()
    expect(screen.getByText('Hello world')).toBeDefined()
  })

  it('enters edit mode on click', () => {
    render(<SegmentRow segment={segment} onEdit={() => {}} editing={true} />)
    const input = screen.getByRole('textbox')
    expect(input).toBeDefined()
  })

  it('calls onEdit with new text on blur', () => {
    const fn = vi.fn()
    render(<SegmentRow segment={segment} onEdit={fn} editing={true} />)
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'New text' } })
    fireEvent.blur(input)
    expect(fn).toHaveBeenCalledWith(0, 'New text')
  })

  it('shows speaker label', () => {
    const seg = { ...segment, speaker: 'Speaker 1' }
    render(<SegmentRow segment={seg} onEdit={() => {}} />)
    expect(screen.getByText('Speaker 1')).toBeDefined()
  })
})
