import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { useTaskStore } from '@/store/taskStore'

// Mock sub-components to isolate OutputPanel
vi.mock('../DownloadButtons', () => ({
  DownloadButtons: () => <div data-testid="download-buttons" />,
}))
vi.mock('../TimingBreakdown', () => ({
  TimingBreakdown: () => <div data-testid="timing-breakdown" />,
}))
vi.mock('../../embed/EmbedPanel', () => ({
  EmbedPanel: () => <div data-testid="embed-panel" />,
}))

import { OutputPanel } from '../OutputPanel'

const initialState = useTaskStore.getState()

beforeEach(() => {
  useTaskStore.setState({ ...initialState })
})

describe('OutputPanel', () => {
  it('shows empty state when not complete', () => {
    useTaskStore.setState({ isComplete: false, taskId: null })
    render(<OutputPanel />)
    expect(screen.getByText('No results yet')).toBeInTheDocument()
    expect(screen.getByText('Upload a file to get started')).toBeInTheDocument()
  })

  it('shows results when isComplete and taskId are set', () => {
    useTaskStore.setState({
      isComplete: true,
      taskId: 'abc123',
      filename: 'interview.wav',
      language: 'English',
      segments: 42,
      totalTimeSec: 180,
    })
    render(<OutputPanel />)
    expect(screen.getByText('interview.wav')).toBeInTheDocument()
  })

  it('displays filename when results are shown', () => {
    useTaskStore.setState({
      isComplete: true,
      taskId: 'abc',
      filename: 'podcast.mp3',
      segments: 10,
    })
    render(<OutputPanel />)
    expect(screen.getByText('podcast.mp3')).toBeInTheDocument()
  })

  it('displays segments count', () => {
    useTaskStore.setState({
      isComplete: true,
      taskId: 'abc',
      filename: 'test.mp3',
      segments: 15,
    })
    render(<OutputPanel />)
    expect(screen.getByText('15 segments')).toBeInTheDocument()
  })

  it('shows singular "segment" for 1 segment', () => {
    useTaskStore.setState({
      isComplete: true,
      taskId: 'abc',
      filename: 'test.mp3',
      segments: 1,
    })
    render(<OutputPanel />)
    expect(screen.getByText('1 segment')).toBeInTheDocument()
  })

  it('displays language badge', () => {
    useTaskStore.setState({
      isComplete: true,
      taskId: 'abc',
      filename: 'test.mp3',
      segments: 5,
      language: 'French',
    })
    render(<OutputPanel />)
    expect(screen.getByText('French')).toBeInTheDocument()
  })

  it('Process Next File button calls reset', () => {
    const resetSpy = vi.fn()
    useTaskStore.setState({
      isComplete: true,
      taskId: 'abc',
      filename: 'test.mp3',
      segments: 5,
      reset: resetSpy,
    })
    render(<OutputPanel />)
    fireEvent.click(screen.getByText('Process Next File'))
    expect(resetSpy).toHaveBeenCalled()
  })

  it('shows OUTPUT header', () => {
    render(<OutputPanel />)
    expect(screen.getByText('OUTPUT')).toBeInTheDocument()
  })
})
