import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SegmentList } from '../../components/editor/SegmentList'
import { useEditorStore } from '../../store/editorStore'

describe('SegmentList', () => {
  beforeEach(() => useEditorStore.getState().reset())

  it('shows empty state when no segments', () => {
    render(<SegmentList taskId="task-1" />)
    expect(screen.getByText(/no subtitles/i)).toBeDefined()
  })

  it('renders segments when present', () => {
    useEditorStore.getState().setComplete({
      segments: [{ index: 0, start: 0, end: 5, text: 'Test segment' }],
      language: 'en', modelUsed: 'large', timings: {}, isVideo: false
    })
    render(<SegmentList taskId="task-1" />)
    expect(screen.getByText('Test segment')).toBeDefined()
  })
})
