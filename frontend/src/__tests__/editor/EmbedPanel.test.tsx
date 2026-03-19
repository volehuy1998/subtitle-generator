/**
 * EmbedPanel tests — subtitle embedding with mode and style selection.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
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

  it('disables embed button during running state', async () => {
    const { api } = await import('../../api/client')
    // Make embedQuick hang so status stays 'running'
    ;(api.embedQuick as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))
    render(<EmbedPanel />)
    // Open dialog and confirm to trigger embed
    fireEvent.click(screen.getByText('Embed Subtitles'))
    fireEvent.click(screen.getByText('Confirm'))
    // Button should now be disabled
    const btn = screen.getByText('Embed Subtitles')
    expect(btn.getAttribute('disabled')).not.toBeNull()
  })

  it('clears download link when starting new embed', async () => {
    // Mock EventSource for this test since embed now waits for SSE
    class InlineES {
      static instance: InlineES | null = null
      listeners: Record<string, ((...args: unknown[]) => void)[]> = {}
      readyState = 0
      constructor() { InlineES.instance = this }
      addEventListener(type: string, fn: (...args: unknown[]) => void) { (this.listeners[type] ??= []).push(fn) }
      close() { this.readyState = 2 }
      emit(type: string, data: unknown) {
        for (const fn of this.listeners[type] ?? []) fn({ data: JSON.stringify(data) })
      }
    }
    const origES = globalThis.EventSource
    globalThis.EventSource = InlineES as unknown as typeof EventSource

    try {
      const { api } = await import('../../api/client')
      ;(api.embedQuick as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ status: 'started' })
      render(<EmbedPanel />)
      // First embed — trigger and wait for SSE setup
      fireEvent.click(screen.getByText('Embed Subtitles'))
      fireEvent.click(screen.getByText('Confirm'))
      await vi.waitFor(() => { expect(InlineES.instance).not.toBeNull() })
      // Fire embed_done to complete the first embed
      InlineES.instance!.emit('embed_done', { download_url: '/embed/download/task-123' })
      await vi.waitFor(() => {
        expect(screen.getByText('Download embedded video')).toBeDefined()
      })
      // Second embed — download link should disappear immediately
      ;(api.embedQuick as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))
      fireEvent.click(screen.getByText('Embed Subtitles'))
      fireEvent.click(screen.getByText('Confirm'))
      expect(screen.queryByText('Download embedded video')).toBeNull()
    } finally {
      globalThis.EventSource = origES
    }
  })

  it('shows friendly message on 409 conflict', async () => {
    const { api } = await import('../../api/client')
    ;(api.embedQuick as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('409: Embed already in progress'))
    render(<EmbedPanel />)
    fireEvent.click(screen.getByText('Embed Subtitles'))
    fireEvent.click(screen.getByText('Confirm'))
    await vi.waitFor(() => {
      expect(screen.getByText('An embed is already in progress. Please wait for it to finish.')).toBeDefined()
    })
  })

  describe('SSE-based embed completion', () => {
    // Mock EventSource for SSE tests
    class MockEventSource {
      static instance: MockEventSource | null = null
      listeners: Record<string, ((...args: unknown[]) => void)[]> = {}
      readyState = 0
      constructor() {
        MockEventSource.instance = this
      }
      addEventListener(type: string, fn: (...args: unknown[]) => void) {
        ;(this.listeners[type] ??= []).push(fn)
      }
      close() {
        this.readyState = 2
      }
      emit(type: string, data: unknown) {
        for (const fn of this.listeners[type] ?? []) {
          fn({ data: JSON.stringify(data) })
        }
      }
    }

    let originalEventSource: typeof EventSource

    beforeEach(() => {
      originalEventSource = globalThis.EventSource
      globalThis.EventSource = MockEventSource as unknown as typeof EventSource
      MockEventSource.instance = null
    })

    afterEach(() => {
      globalThis.EventSource = originalEventSource
    })

    it('does not show download link immediately after embedQuick resolves', async () => {
      const { api } = await import('../../api/client')
      ;(api.embedQuick as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ status: 'started' })
      render(<EmbedPanel />)
      fireEvent.click(screen.getByText('Embed Subtitles'))
      fireEvent.click(screen.getByText('Confirm'))
      // Wait for embedQuick to resolve and SSE to be set up
      await vi.waitFor(() => {
        expect(MockEventSource.instance).not.toBeNull()
      })
      // Status should be 'running', NOT 'done' — no download link yet
      expect(screen.queryByText('Download embedded video')).toBeNull()
      expect(screen.getByTestId('progress-bar')).toBeDefined()
    })

    it('shows download link after embed_done SSE event', async () => {
      const { api } = await import('../../api/client')
      ;(api.embedQuick as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ status: 'started' })
      render(<EmbedPanel />)
      fireEvent.click(screen.getByText('Embed Subtitles'))
      fireEvent.click(screen.getByText('Confirm'))
      // Wait for EventSource to be created
      await vi.waitFor(() => {
        expect(MockEventSource.instance).not.toBeNull()
      })
      // Fire embed_done SSE event
      MockEventSource.instance!.emit('embed_done', { download_url: '/embed/download/task-123' })
      // Now download link should appear
      await vi.waitFor(() => {
        expect(screen.getByText('Download embedded video')).toBeDefined()
      })
      const link = screen.getByText('Download embedded video').closest('a')
      expect(link?.getAttribute('href')).toBe('/embed/download/task-123')
    })
  })
})
