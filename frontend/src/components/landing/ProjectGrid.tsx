/**
 * ProjectGrid — Displays the recent projects grid on the landing page.
 * Reads from useRecentProjectsStore; shows EmptyState when no projects exist.
 *
 * — Pixel (Senior Frontend Engineer)
 */
import { useRecentProjectsStore } from '../../store/recentProjectsStore'
import { ProjectCard } from './ProjectCard'
import { EmptyState } from '../ui/EmptyState'

export function ProjectGrid() {
  const { projects, clearAll } = useRecentProjectsStore()

  if (projects.length === 0) {
    return (
      <div data-testid="project-grid">
        <EmptyState
          title="No recent projects"
          description="Upload a file to get started"
        />
      </div>
    )
  }

  return (
    <section data-testid="project-grid">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-[var(--color-text)]">Recent Projects</h2>
        <button
          type="button"
          onClick={clearAll}
          className="text-xs text-[var(--color-text-secondary)] hover:text-[var(--color-danger)] transition-colors"
        >
          Clear
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {projects.map(project => (
          <ProjectCard key={project.taskId} project={project} />
        ))}
      </div>
    </section>
  )
}
