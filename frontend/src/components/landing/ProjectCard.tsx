/**
 * ProjectCard — Displays a single recent project with status and metadata.
 * Click navigates to the editor for that project.
 *
 * — Pixel (Senior Frontend Engineer)
 */
import { Badge } from '../ui/Badge'
import { Spinner } from '../ui/Spinner'
import { cn } from '../ui/cn'
import { navigate } from '../../navigation'
import { formatDuration, type RecentProject } from '../../types'

function relativeTime(isoString: string): string {
  const diffMs = Date.now() - new Date(isoString).getTime()
  const diffSec = Math.floor(diffMs / 1000)
  if (diffSec < 60) return 'just now'
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)} min ago`
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} hr ago`
  return `${Math.floor(diffSec / 86400)} days ago`
}

interface ProjectCardProps {
  project: RecentProject
}

export function ProjectCard({ project }: ProjectCardProps) {
  const { taskId, filename, createdAt, status, duration } = project

  function handleClick() {
    navigate('/editor/' + taskId)
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        'w-full text-left rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]',
        'p-4 flex flex-col gap-2',
        'hover:-translate-y-0.5 hover:shadow-md transition-transform transition-shadow',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]',
      )}
    >
      <p className="text-sm font-medium text-[var(--color-text)] truncate" title={filename}>
        {filename}
      </p>

      <div className="flex items-center gap-2 flex-wrap">
        {status === 'processing' && (
          <Badge variant="default">
            <Spinner size="sm" />
            Processing
          </Badge>
        )}
        {status === 'completed' && (
          <Badge variant="success">Completed</Badge>
        )}
        {status === 'failed' && (
          <Badge variant="danger">Failed</Badge>
        )}

        {duration != null && (
          <span className="text-xs text-[var(--color-text-secondary)]">
            {formatDuration(duration)}
          </span>
        )}
      </div>

      <p className="text-xs text-[var(--color-text-muted)]">{relativeTime(createdAt)}</p>
    </button>
  )
}
