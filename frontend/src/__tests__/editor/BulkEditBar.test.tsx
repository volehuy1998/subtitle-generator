import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BulkEditBar } from '../../components/editor/BulkEditBar'
import { useEditorStore } from '../../store/editorStore'

describe('BulkEditBar', () => {
  beforeEach(() => {
    useEditorStore.getState().reset()
  })

  it('renders nothing when no segments are selected', () => {
    const { container } = render(<BulkEditBar />)
    expect(container.innerHTML).toBe('')
  })

  it('renders selection count when segments are selected', () => {
    useEditorStore.setState({
      segments: [
        { index: 0, start: 0, end: 1, text: 'Hello' },
        { index: 1, start: 1, end: 2, text: 'World' },
      ],
      selectedSegments: new Set([0, 1]),
    })
    render(<BulkEditBar />)
    expect(screen.getByText('2 selected')).toBeDefined()
  })

  it('performs find and replace on selected segments only', () => {
    useEditorStore.setState({
      segments: [
        { index: 0, start: 0, end: 1, text: 'Hello world' },
        { index: 1, start: 1, end: 2, text: 'Hello there' },
        { index: 2, start: 2, end: 3, text: 'Hello again' },
      ],
      selectedSegments: new Set([0, 2]),
    })
    render(<BulkEditBar />)
    fireEvent.change(screen.getByPlaceholderText('Find...'), { target: { value: 'Hello' } })
    fireEvent.change(screen.getByPlaceholderText('Replace...'), { target: { value: 'Hi' } })
    fireEvent.click(screen.getByText('Replace'))
    const segments = useEditorStore.getState().segments
    expect(segments[0].text).toBe('Hi world')
    expect(segments[1].text).toBe('Hello there') // not selected, unchanged
    expect(segments[2].text).toBe('Hi again')
  })

  it('deletes selected segments and clears selection', () => {
    useEditorStore.setState({
      segments: [
        { index: 0, start: 0, end: 1, text: 'A' },
        { index: 1, start: 1, end: 2, text: 'B' },
        { index: 2, start: 2, end: 3, text: 'C' },
      ],
      selectedSegments: new Set([0, 2]),
    })
    render(<BulkEditBar />)
    fireEvent.click(screen.getByText('Delete'))
    const state = useEditorStore.getState()
    expect(state.segments).toHaveLength(1)
    expect(state.segments[0].text).toBe('B')
    expect(state.selectedSegments.size).toBe(0)
  })

  it('select all button selects all segments', () => {
    useEditorStore.setState({
      segments: [
        { index: 0, start: 0, end: 1, text: 'A' },
        { index: 1, start: 1, end: 2, text: 'B' },
        { index: 2, start: 2, end: 3, text: 'C' },
      ],
      selectedSegments: new Set([0]),
    })
    render(<BulkEditBar />)
    fireEvent.click(screen.getByText('Select all'))
    expect(useEditorStore.getState().selectedSegments.size).toBe(3)
  })

  it('replace button is disabled when find text is empty', () => {
    useEditorStore.setState({
      segments: [{ index: 0, start: 0, end: 1, text: 'A' }],
      selectedSegments: new Set([0]),
    })
    render(<BulkEditBar />)
    const replaceBtn = screen.getByText('Replace').closest('button')!
    expect(replaceBtn.disabled).toBe(true)
  })
})
