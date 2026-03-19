/**
 * EmbedPanel tests — subtitle embedding with mode and style selection.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { EmbedPanel } from '../../components/editor/EmbedPanel'
import { useEditorStore } from '../../store/editorStore'
import { usePreferencesStore } from '../../store/preferencesStore'

// Mock API client
vi.mock('../../api/client', () => ({
  api: {
    embedPresets: vi.fn().mockResolvedValue({
      presets: {
        default: { font_name: 'Arial', font_size: 24, bold: false, position: 'bottom' },
        youtube_white: { font_name: 'Arial', font_size: 20, bold: true, position: 'bottom' },
      },
    }),
    embedQuick: vi.fn().mockResolvedValue({ download_url: '/embed/download/task-123' }),
    embedDownloadUrl: vi.fn().mockReturnValue('/embed/download/task-123'),
  },
}))

// Mock UI components
vi.mock('../../components/ui/ProgressBar', () => ({
  ProgressBar: ({ label }: { label?: string }) => <div data-testid="progress-bar">{label}</div>,
}))
vi.mock('../../components/ui/ConfirmDialog', () => ({
  ConfirmDialog: ({ open, title, description, onConfirm, onClose }: {
    open: boolean; title: string; description: string;
    onConfirm: () => void; onClose: () => void
  }) =>
    open ? (
      <div data-testid="confirm-dialog">
        <span>{title}</span>
        <span>{description}</span>
        <button onClick={onConfirm}>Confirm</button>
        <button onClick={onClose}>Cancel</button>
      </div>
    ) : null,
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
vi.mock('./CustomEmbedStyler', () => ({
  CustomEmbedStyler: () => <div data-testid="custom-styler">CustomEmbedStyler</div>,
}))

describe('EmbedPanel', () => {
  beforeEach(() => {
    useEditorStore.getState().reset()
    useEditorStore.setState({ taskId: 'task-123' })
    usePreferencesStore.getState().reset()
  })

  it('renders mode selector with Soft and Hard Burn', () => {
    render(<EmbedPanel />)
    expect(screen.getByText('Soft')).toBeDefined()
    expect(screen.getByText('Hard Burn')).toBeDefined()
    expect(screen.getByText('Fast, no re-encode')).toBeDefined()
    expect(screen.getByText('Re-encodes video')).toBeDefined()
  })

  it('renders Embed Subtitles button', () => {
    render(<EmbedPanel />)
    expect(screen.getByText('Embed Subtitles')).toBeDefined()
  })

  it('opens confirm dialog on Embed Subtitles click', () => {
    render(<EmbedPanel />)
    fireEvent.click(screen.getByText('Embed Subtitles'))
    expect(screen.getByTestId('confirm-dialog')).toBeDefined()
    expect(screen.getByText('Embed subtitles')).toBeDefined()
  })

  it('shows style options when hard mode is selected', () => {
    render(<EmbedPanel />)
    // Click hard burn mode
    fireEvent.click(screen.getByText('Hard Burn'))
    // Should show Preset/Custom toggle
    expect(screen.getByText('Preset')).toBeDefined()
    expect(screen.getByText('Custom')).toBeDefined()
  })

  it('does not show style options in soft mode by default', () => {
    render(<EmbedPanel />)
    // Soft mode is default from prefs — no Preset/Custom toggle
    expect(screen.queryByText('Preset')).toBeNull()
    expect(screen.queryByText('Custom')).toBeNull()
  })
})
