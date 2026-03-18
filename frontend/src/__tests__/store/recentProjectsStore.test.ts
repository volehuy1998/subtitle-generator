import { describe, it, expect, beforeEach } from 'vitest'
import { useRecentProjectsStore } from '../../store/recentProjectsStore'
import type { RecentProject } from '../../types'

const makeProject = (id: string): RecentProject => ({
  taskId: id,
  filename: `file-${id}.mp4`,
  createdAt: new Date().toISOString(),
  status: 'completed',
  duration: 120,
})

describe('recentProjectsStore', () => {
  beforeEach(() => useRecentProjectsStore.getState().clearAll())

  it('adds a project', () => {
    useRecentProjectsStore.getState().addProject(makeProject('p1'))
    expect(useRecentProjectsStore.getState().projects).toHaveLength(1)
  })

  it('deduplicates on add (same taskId moves to front)', () => {
    useRecentProjectsStore.getState().addProject(makeProject('p1'))
    useRecentProjectsStore.getState().addProject(makeProject('p2'))
    useRecentProjectsStore.getState().addProject(makeProject('p1')) // re-add p1
    const projects = useRecentProjectsStore.getState().projects
    expect(projects).toHaveLength(2)
    expect(projects[0].taskId).toBe('p1') // p1 moved to front
  })

  it('limits to 20 projects', () => {
    for (let i = 0; i < 25; i++) {
      useRecentProjectsStore.getState().addProject(makeProject(`p${i}`))
    }
    expect(useRecentProjectsStore.getState().projects).toHaveLength(20)
  })

  it('updates a project', () => {
    useRecentProjectsStore.getState().addProject(makeProject('p1'))
    useRecentProjectsStore.getState().updateProject('p1', { status: 'failed' })
    expect(useRecentProjectsStore.getState().projects[0].status).toBe('failed')
  })

  it('removes a project', () => {
    useRecentProjectsStore.getState().addProject(makeProject('p1'))
    useRecentProjectsStore.getState().addProject(makeProject('p2'))
    useRecentProjectsStore.getState().removeProject('p1')
    expect(useRecentProjectsStore.getState().projects).toHaveLength(1)
    expect(useRecentProjectsStore.getState().projects[0].taskId).toBe('p2')
  })

  it('clears all', () => {
    useRecentProjectsStore.getState().addProject(makeProject('p1'))
    useRecentProjectsStore.getState().clearAll()
    expect(useRecentProjectsStore.getState().projects).toHaveLength(0)
  })
})
