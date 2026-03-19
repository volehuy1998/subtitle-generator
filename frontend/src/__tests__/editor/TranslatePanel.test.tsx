/**
 * TranslatePanel tests — translation engine selector with language options.
 * Updated to reflect guidance-based flow (no standalone translate API).
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { TranslatePanel } from '../../components/editor/TranslatePanel'
import { useEditorStore } from '../../store/editorStore'

// Mock API client
vi.mock('../../api/client', () => ({
  api: {
    translationLanguages: vi.fn().mockResolvedValue({
      pairs: [
        { source: 'en', source_name: 'English', target: 'es', target_name: 'Spanish' },
        { source: 'en', source_name: 'English', target: 'fr', target_name: 'French' },
      ],
    }),
  },
}))

// Mock UI components to simplify rendering
vi.mock('../../components/ui/Button', () => ({
  Button: ({ children, onClick, disabled }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean }) => (
    <button onClick={onClick} disabled={disabled}>{children}</button>
  ),
}))
vi.mock('../../components/ui/Select', () => ({
  Select: ({ label, options, value, onChange }: { label: string; options: Array<{ value: string; label: string }>; value: string; onChange: (e: { target: { value: string } }) => void }) => (
    <label>
      {label}
      <select value={value} onChange={onChange}>
        {options.map((o: { value: string; label: string }) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  ),
}))

describe('TranslatePanel', () => {
  beforeEach(() => {
    useEditorStore.getState().reset()
    useEditorStore.setState({ taskId: 'task-123', language: 'en' })
  })

  it('renders source language display', () => {
    render(<TranslatePanel />)
    expect(screen.getByText('Source language')).toBeDefined()
    expect(screen.getByText('en')).toBeDefined()
  })

  it('shows Auto-detected when source language is null', () => {
    useEditorStore.setState({ language: null })
    render(<TranslatePanel />)
    expect(screen.getByText('Auto-detected')).toBeDefined()
  })

  it('renders engine selector with Whisper and Argos', () => {
    render(<TranslatePanel />)
    expect(screen.getByText('Whisper')).toBeDefined()
    expect(screen.getByText('Argos')).toBeDefined()
    expect(screen.getByText('EN only')).toBeDefined()
    expect(screen.getByText('Any language')).toBeDefined()
  })

  it('renders Begin Translation button', () => {
    render(<TranslatePanel />)
    expect(screen.getByText('Begin Translation')).toBeDefined()
  })

  it('loads translation language pairs from API', async () => {
    render(<TranslatePanel />)
    await waitFor(() => {
      expect(screen.getByText('Target language')).toBeDefined()
    })
  })

  it('shows re-transcribe guidance when Whisper engine is selected', () => {
    render(<TranslatePanel />)
    fireEvent.click(screen.getByText('Begin Translation'))
    expect(screen.getByText('Use Re-transcribe')).toBeDefined()
    expect(screen.getByText(/Translate to English/)).toBeDefined()
  })

  it('shows error message when Argos engine is selected', () => {
    render(<TranslatePanel />)
    // Click Argos engine button
    fireEvent.click(screen.getByText('Argos'))
    fireEvent.click(screen.getByText('Begin Translation'))
    expect(screen.getByText(/Standalone Argos translation is not yet available/)).toBeDefined()
  })

  it('disables button after showing whisper guidance', () => {
    render(<TranslatePanel />)
    fireEvent.click(screen.getByText('Begin Translation'))
    expect(screen.getByText('Begin Translation').closest('button')?.disabled).toBe(true)
  })

  it('does nothing when taskId is not set', () => {
    useEditorStore.setState({ taskId: null })
    render(<TranslatePanel />)
    fireEvent.click(screen.getByText('Begin Translation'))
    // No guidance or error should appear
    expect(screen.queryByText('Use Re-transcribe')).toBeNull()
    expect(screen.queryByText(/not yet available/)).toBeNull()
  })
})
