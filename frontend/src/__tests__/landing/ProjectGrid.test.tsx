/**
 * ProjectGrid tests — recent projects grid with empty state.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ProjectGrid } from '../../components/landing/ProjectGrid'
import { useRecentProjectsStore } from '../../store/recentProjectsStore'

// Mock ProjectCard to isolate ProjectGrid
vi.mock('../../components/landing/ProjectCard', () => ({
  ProjectCard: ({ project }: { project: { taskId: string; filename: string } }) => (
    <div data-testid={`project-card-${project.taskId}`}>{project.filename}</div>
  ),
}))

// Mock EmptyState
vi.mock('../../components/ui/EmptyState', () => ({
  EmptyState: ({ title, description }: { title: string; description?: string }) => (
    <div data-testid="empty-state">
      <span>{title}</span>
      {description && <span>{description}</span>}
    </div>
  ),
}))

describe('ProjectGrid', () => {
  beforeEach(() => {
    useRecentProjectsStore.setState({ projects: [] })
  })

  it('shows empty state when no projects exist', () => {
    render(<ProjectGrid />)
    expect(screen.getByTestId('empty-state')).toBeDefined()
    expect(screen.getByText('No recent projects')).toBeDefined()
    expect(screen.getByText('Upload a file to get started')).toBeDefined()
  })

  it('renders project cards when projects exist', () => {
    useRecentProjectsStore.setState({
      projects: [
        { taskId: 'abc', filename: 'video1.mp4', createdAt: new Date().toISOString(), status: 'completed' as const, duration: 60 },
        { taskId: 'def', filename: 'audio2.wav', createdAt: new Date().toISOString(), status: 'processing' as const, duration: null },
      ],
    })
    render(<ProjectGrid />)
    expect(screen.getByTestId('project-card-abc')).toBeDefined()
    expect(screen.getByTestId('project-card-def')).toBeDefined()
    expect(screen.getByText('video1.mp4')).toBeDefined()
    expect(screen.getByText('audio2.wav')).toBeDefined()
  })

  it('shows Recent Projects heading with projects', () => {
    useRecentProjectsStore.setState({
      projects: [
        { taskId: 'abc', filename: 'video.mp4', createdAt: new Date().toISOString(), status: 'completed' as const, duration: 60 },
      ],
    })
    render(<ProjectGrid />)
    expect(screen.getByText('Recent Projects')).toBeDefined()
  })

  it('calls clearAll when Clear button is clicked', () => {
    useRecentProjectsStore.setState({
      projects: [
        { taskId: 'abc', filename: 'video.mp4', createdAt: new Date().toISOString(), status: 'completed' as const, duration: 60 },
      ],
    })
    render(<ProjectGrid />)
    fireEvent.click(screen.getByText('Clear'))
    expect(useRecentProjectsStore.getState().projects).toEqual([])
  })
})
