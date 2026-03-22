import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { useTaskStore } from '@/store/taskStore'
import { useUIStore } from '@/store/uiStore'

// Mock useSSE
vi.mock('@/hooks/useSSE', () => ({
  useSSE: () => ({ close: vi.fn() }),
}))

// Mock sub-components to isolate ProgressView
vi.mock('../PipelineSteps', () => ({
  PipelineSteps: () => <div data-testid="pipeline-steps" />,
}))
vi.mock('../LivenessIndicator', () => ({
  LivenessIndicator: () => <div data-testid="liveness" />,
}))
vi.mock('../CancelConfirmationDialog', () => ({
  CancelConfirmationDialog: () => <div data-testid="cancel-dialog" />,
}))
vi.mock('../SubtitlePreview', () => ({
  SubtitlePreview: () => <div data-testid="subtitle-preview" />,
}))

// Mock api
vi.mock('@/api/client', () => ({
  api: {
    pause: vi.fn().mockResolvedValue({}),
    resume: vi.fn().mockResolvedValue({}),
    cancel: vi.fn().mockResolvedValue({}),
  },
}))

// We need to import ProgressView after mocks are set up
import { ProgressView } from '../ProgressView'

const initialState = useTaskStore.getState()

beforeEach(() => {
  useTaskStore.setState({ ...initialState, lastEventTime: Date.now() })
  useUIStore.setState({ appMode: 'transcribe' })
})

describe('ProgressView', () => {
  it('progress bar shows correct percentage via aria-valuenow', () => {
    useTaskStore.setState({ percent: 42, status: 'transcribing' })
    render(<ProgressView taskId="t1" />)
    const bar = screen.getByRole('progressbar')
    expect(bar).toHaveAttribute('aria-valuenow', '42')
  })

  it('progress bar has aria-valuemin and aria-valuemax', () => {
    useTaskStore.setState({ percent: 50, status: 'transcribing' })
    render(<ProgressView taskId="t1" />)
    const bar = screen.getByRole('progressbar')
    expect(bar).toHaveAttribute('aria-valuemin', '0')
    expect(bar).toHaveAttribute('aria-valuemax', '100')
  })

  it('shows success banner with role="status" when complete', () => {
    useTaskStore.setState({ isComplete: true, percent: 100, status: 'done', liveSegments: [] })
    render(<ProgressView taskId="t1" />)
    const status = screen.getByRole('status')
    expect(status).toBeInTheDocument()
    expect(screen.getByText('Transcription complete!')).toBeInTheDocument()
  })

  it('shows error view when status is error', () => {
    useTaskStore.setState({ status: 'error', error: 'Model failed to load', percent: 30 })
    render(<ProgressView taskId="t1" />)
    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getAllByText(/Model failed to load/).length).toBeGreaterThanOrEqual(1)
  })

  it('shows Try Again button on error', () => {
    useTaskStore.setState({ status: 'error', error: 'fail', percent: 0 })
    render(<ProgressView taskId="t1" />)
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('shows cancelled view when status is cancelled', () => {
    useTaskStore.setState({ status: 'cancelled', percent: 0 })
    render(<ProgressView taskId="t1" />)
    expect(screen.getByText('Transcription cancelled.')).toBeInTheDocument()
    expect(screen.getByText('Start Over')).toBeInTheDocument()
  })

  it('shows warning with role="alert"', () => {
    useTaskStore.setState({
      status: 'transcribing',
      percent: 20,
      warning: 'Low disk space',
      lastEventTime: Date.now(),
    })
    render(<ProgressView taskId="t1" />)
    const alerts = screen.getAllByRole('alert')
    const warningAlert = alerts.find((a) => a.textContent?.includes('Low disk space'))
    expect(warningAlert).toBeDefined()
  })

  it('shows cancel and pause buttons during active transcription', () => {
    useTaskStore.setState({
      status: 'transcribing',
      percent: 30,
      isComplete: false,
      lastEventTime: Date.now(),
    })
    render(<ProgressView taskId="t1" />)
    expect(screen.getByText('Pause')).toBeInTheDocument()
    expect(screen.getByText('Cancel')).toBeInTheDocument()
  })

  it('shows Process Another File button when complete', () => {
    useTaskStore.setState({ isComplete: true, percent: 100, status: 'done' })
    render(<ProgressView taskId="t1" />)
    expect(screen.getByText('Process Another File')).toBeInTheDocument()
  })

  it('displays filename', () => {
    useTaskStore.setState({ filename: 'lecture.mp3', status: 'transcribing', percent: 10, lastEventTime: Date.now() })
    render(<ProgressView taskId="t1" />)
    expect(screen.getByText('lecture.mp3')).toBeInTheDocument()
  })
})
