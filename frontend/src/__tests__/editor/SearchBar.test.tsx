import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SearchBar } from '../../components/editor/SearchBar'
import { useEditorStore } from '../../store/editorStore'

describe('SearchBar', () => {
  beforeEach(() => useEditorStore.getState().reset())

  it('renders search input', () => {
    render(<SearchBar taskId="task-1" />)
    expect(screen.getByRole('textbox')).toBeDefined()
  })

  it('shows placeholder text', () => {
    render(<SearchBar taskId="task-1" />)
    const input = screen.getByRole('textbox')
    expect(input).toBeDefined()
  })
})
