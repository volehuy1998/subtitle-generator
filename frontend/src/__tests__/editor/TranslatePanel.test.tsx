/**
 * TranslatePanel tests — translation engine selector with language options.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
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
vi.mock('../../components/ui/ProgressBar', () => ({
  ProgressBar: ({ label }: { label?: string }) => <div data-testid="progress-bar">{label}</div>,
}))
vi.mock('../../components/ui/ConfirmDialog', () => ({
  ConfirmDialog: ({ open, title, onConfirm }: { open: boolean; title: string; onConfirm: () => void }) =>
    open ? <div data-testid="confirm-dialog"><span>{title}</span><button onClick={onConfirm}>OK</button></div> : null,
}))
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
})
