/**
 * ProgressView tests — transcription progress display with stats and cancel.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ProgressView } from '../../components/editor/ProgressView'
import { useEditorStore } from '../../store/editorStore'

// Mock API client
const mockCancel = vi.fn().mockResolvedValue({ message: 'cancelled' })
vi.mock('../../api/client', () => ({
  api: {
    cancel: (...args: unknown[]) => mockCancel(...args),
  },
}))

// Mock navigation
const mockNavigate = vi.fn()
vi.mock('../../navigation', () => ({
  navigate: (...args: unknown[]) => mockNavigate(...args),
}))

// Mock sub-components
vi.mock('../../components/editor/PipelineSteps', () => ({
  PipelineSteps: ({ currentStep }: { currentStep: string | null }) => (
    <div data-testid="pipeline-steps">{currentStep ?? 'none'}</div>
  ),
}))
vi.mock('../../components/editor/LivePreview', () => ({
  LivePreview: () => <div data-testid="live-preview" />,
}))
vi.mock('../../components/ui/ProgressBar', () => ({
  ProgressBar: ({ value }: { value: number; showPercent?: boolean }) => (
    <div data-testid="progress-bar" data-value={value} />
  ),
}))
vi.mock('../../components/ui/Button', () => ({
  Button: ({ children, onClick, disabled }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean; variant?: string; size?: string }) => (
    <button onClick={onClick} disabled={disabled}>{children}</button>
  ),
}))
vi.mock('../../components/ui/Tooltip', () => ({
  Tooltip: ({ children, content }: { children: React.ReactNode; content: string; side?: string }) => (
    <div title={content}>{children}</div>
  ),
  TooltipProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

describe('ProgressView', () => {
  beforeEach(() => {
    useEditorStore.getState().reset()
    mockCancel.mockReset().mockResolvedValue({ message: 'cancelled' })
    mockNavigate.mockReset()
  })

  it('renders filename from file metadata', () => {
    useEditorStore.setState({
      fileMetadata: {
        filename: 'interview.mp4',
        size: 5000000,
        format: 'mp4',
        duration: 120,
        resolution: '1920x1080',
        codec: 'h264',
        isVideo: true,
      },
    })
    render(<ProgressView taskId="task-1" />)
    expect(screen.getByText('interview.mp4')).toBeDefined()
  })

  it('shows Processing... when no metadata', () => {
    render(<ProgressView taskId="task-1" />)
    expect(screen.getByText('Processing...')).toBeDefined()
  })

  it('displays progress stats when available', () => {
    useEditorStore.setState({
      progress: {
        percent: 45,
        segmentCount: 12,
        estimatedSegments: 30,
        eta: 25,
        elapsed: 15,
        speed: 2.3,
        pipelineStep: 'transcribing',
        message: 'Transcribing audio...',
      },
    })
    render(<ProgressView taskId="task-1" />)
    expect(screen.getByText('12 segments | ETA: 25s | 2.3x speed')).toBeDefined()
    expect(screen.getByText('Transcribing audio...')).toBeDefined()
  })

  it('renders Cancel button and Pause button (disabled)', () => {
    render(<ProgressView taskId="task-1" />)
    expect(screen.getByText('Cancel')).toBeDefined()
    const pauseBtn = screen.getByText('Pause')
    expect(pauseBtn).toBeDefined()
    expect((pauseBtn as HTMLButtonElement).disabled).toBe(true)
  })

  it('calls cancel API and navigates home on Cancel click', async () => {
    render(<ProgressView taskId="task-1" />)
    fireEvent.click(screen.getByText('Cancel'))
    // Wait for the async cancel to resolve
    await vi.waitFor(() => {
      expect(mockCancel).toHaveBeenCalledWith('task-1')
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })
})
