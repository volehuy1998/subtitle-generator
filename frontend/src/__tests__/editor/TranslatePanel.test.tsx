/**
 * TranslatePanel tests — translation engine selector with language options.
 * Tests Whisper guidance flow and Argos api.translate() call.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { TranslatePanel } from '../../components/editor/TranslatePanel'
import { useEditorStore } from '../../store/editorStore'

const mockTranslate = vi.fn().mockResolvedValue({ message: 'Translation started', task_id: 'task-123' })

// Mock API client
vi.mock('../../api/client', () => ({
  api: {
    translationLanguages: vi.fn().mockResolvedValue({
      pairs: [
        { source: 'en', source_name: 'English', target: 'es', target_name: 'Spanish' },
        { source: 'en', source_name: 'English', target: 'fr', target_name: 'French' },
      ],
    }),
    translate: (...args: unknown[]) => mockTranslate(...args),
  },
}))

// Mock UI components to simplify rendering
vi.mock('../../components/ui/Button', () => ({
  Button: ({ children, onClick, disabled, loading }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean; loading?: boolean }) => (
    <button onClick={onClick} disabled={disabled || loading} data-loading={loading}>{children}</button>
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
vi.mock('../../components/ui/ProgressBar', () => ({
  ProgressBar: ({ label }: { label?: string }) => <div data-testid="progress-bar">{label}</div>,
}))

describe('TranslatePanel', () => {
  beforeEach(() => {
    useEditorStore.getState().reset()
    useEditorStore.setState({ taskId: 'task-123', language: 'en' })
    mockTranslate.mockClear()
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

  it('calls api.translate when Argos engine is selected', async () => {
    // Mock EventSource
    const mockES = { addEventListener: vi.fn(), close: vi.fn(), readyState: 0 }
    vi.stubGlobal('EventSource', vi.fn(() => mockES))

    render(<TranslatePanel />)
    // Click Argos engine button
    fireEvent.click(screen.getByText('Argos'))
    fireEvent.click(screen.getByText('Begin Translation'))

    await waitFor(() => {
      expect(mockTranslate).toHaveBeenCalledWith('task-123', 'en')
    })

    vi.unstubAllGlobals()
  })

  it('shows Translate Again after whisper guidance', () => {
    render(<TranslatePanel />)
    fireEvent.click(screen.getByText('Begin Translation'))
    expect(screen.getByText('Translate Again')).toBeDefined()
  })

  it('does nothing when taskId is not set', () => {
    useEditorStore.setState({ taskId: null })
    render(<TranslatePanel />)
    fireEvent.click(screen.getByText('Begin Translation'))
    // No guidance or error should appear
    expect(screen.queryByText('Use Re-transcribe')).toBeNull()
  })
})
