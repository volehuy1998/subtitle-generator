import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { RecentProject } from '../types'

const MAX_PROJECTS = 20

interface RecentProjectsState {
  projects: RecentProject[]
  addProject: (project: RecentProject) => void
  updateProject: (taskId: string, updates: Partial<RecentProject>) => void
  removeProject: (taskId: string) => void
  clearAll: () => void
}

export const useRecentProjectsStore = create<RecentProjectsState>()(
  persist(
    (set) => ({
      projects: [],
      addProject: (project) => set(s => ({
        projects: [project, ...s.projects.filter(p => p.taskId !== project.taskId)].slice(0, MAX_PROJECTS),
      })),
      updateProject: (taskId, updates) => set(s => ({
        projects: s.projects.map(p => p.taskId === taskId ? { ...p, ...updates } : p),
      })),
      removeProject: (taskId) => set(s => ({
        projects: s.projects.filter(p => p.taskId !== taskId),
      })),
      clearAll: () => set({ projects: [] }),
    }),
    { name: 'sg-recent-projects' }
  )
)
