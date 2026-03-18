import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ProjectCard } from '../../components/landing/ProjectCard'
import * as navigation from '../../navigation'

describe('ProjectCard', () => {
  const project = {
    taskId: 'task-abc',
    filename: 'video.mp4',
    createdAt: new Date().toISOString(),
    status: 'completed' as const,
    duration: 125,
  }

  it('renders filename', () => {
    render(<ProjectCard project={project} />)
    expect(screen.getByText('video.mp4')).toBeDefined()
  })

  it('renders formatted duration', () => {
    render(<ProjectCard project={project} />)
    expect(screen.getByText('2:05')).toBeDefined()
  })

  it('navigates on click', () => {
    const spy = vi.spyOn(navigation, 'navigate').mockImplementation(() => {})
    render(<ProjectCard project={project} />)
    fireEvent.click(screen.getByRole('button'))
    expect(spy).toHaveBeenCalledWith('/editor/task-abc')
    spy.mockRestore()
  })
})
