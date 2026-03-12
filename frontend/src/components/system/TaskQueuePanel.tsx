import { useTaskQueue } from '@/hooks/useTaskQueue'
import { useUIStore } from '@/store/uiStore'
import type { TaskStatus } from '@/api/types'

function statusDotColor(status: TaskStatus): string {
  switch (status) {
    case 'done': return 'var(--color-success)'
    case 'error': return 'var(--color-danger)'
    case 'cancelled': return 'var(--color-text-3)'
    case 'paused': return 'var(--color-warning)'
    case 'queued': return 'var(--color-text-3)'
    default: return 'var(--color-primary)'
  }
}

function statusLabel(status: TaskStatus): string {
  switch (status) {
    case 'uploading': return 'Uploading'
    case 'probing': return 'Probing'
    case 'extracting': return 'Extracting'
    case 'loading_model': return 'Loading'
    case 'transcribing': return 'Transcribing'
    case 'formatting': return 'Formatting'
    case 'writing': return 'Writing'
    case 'done': return 'Done'
    case 'error': return 'Error'
    case 'cancelled': return 'Cancelled'
    case 'paused': return 'Paused'
    case 'queued': return 'Queued'
    case 'combining': return 'Combining'
    default: return status
  }
}

export function TaskQueuePanel() {
  const { taskQueueOpen, setTaskQueueOpen } = useUIStore()
  const tasks = useTaskQueue(taskQueueOpen)

  return (
    <div
      className="fixed z-40 rounded-xl overflow-hidden bottom-3 right-3 w-52 sm:bottom-5 sm:left-5 sm:right-auto sm:w-60"
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-lg)',
      }}
    >
      {/* Header */}
      <button
        type="button"
        onClick={() => setTaskQueueOpen(!taskQueueOpen)}
        className="w-full flex items-center justify-between px-3 py-2.5 transition-colors"
        style={{
          background: 'transparent',
          border: 'none',
          borderBottom: taskQueueOpen ? '1px solid var(--color-border)' : 'none',
          cursor: 'pointer',
        }}
      >
        <div className="flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path
              d="M2 3h10M2 7h10M2 11h6"
              stroke="var(--color-text-2)"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          <span
            className="text-xs font-semibold tracking-wider"
            style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
          >
            TASK QUEUE
          </span>
          {tasks.length > 0 && (
            <span
              className="flex items-center justify-center w-4 h-4 rounded-full text-xs font-medium text-white"
              style={{ background: 'var(--color-primary)', fontSize: '10px' }}
            >
              {tasks.length}
            </span>
          )}
        </div>
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          aria-hidden="true"
          style={{
            transform: taskQueueOpen ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s ease',
          }}
        >
          <path
            d="M2 4l4 4 4-4"
            stroke="var(--color-text-3)"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      {/* Body */}
      {taskQueueOpen && (
        <div className="flex flex-col max-h-64 overflow-y-auto">
          {tasks.length === 0 ? (
            <div
              className="px-3 py-4 text-center text-xs"
              style={{ color: 'var(--color-text-3)' }}
            >
              No active tasks
            </div>
          ) : (
            tasks.map((task) => (
              <div
                key={task.task_id}
                className="flex items-center gap-2.5 px-3 py-2.5"
                style={{ borderBottom: '1px solid var(--color-border)' }}
              >
                {/* Status dot */}
                <span
                  className="flex-shrink-0 w-1.5 h-1.5 rounded-full"
                  style={{
                    background: statusDotColor(task.status),
                    boxShadow: ['uploading','transcribing','extracting','formatting'].includes(task.status)
                      ? `0 0 0 3px ${statusDotColor(task.status)}30`
                      : 'none',
                  }}
                />

                {/* File info */}
                <div className="flex-1 min-w-0 flex flex-col gap-0.5">
                  <span
                    className="text-xs font-medium truncate"
                    style={{ color: 'var(--color-text)' }}
                  >
                    {task.filename ?? task.task_id.slice(0, 8)}
                  </span>
                  <span className="text-xs" style={{ color: 'var(--color-text-3)' }}>
                    {statusLabel(task.status)}
                    {task.percent > 0 && task.status !== 'done' && ` · ${task.percent}%`}
                  </span>
                </div>

                {/* Progress */}
                {task.status !== 'done' && task.status !== 'error' && task.status !== 'cancelled' && (
                  <span
                    className="text-xs font-medium flex-shrink-0"
                    style={{ color: 'var(--color-primary)' }}
                  >
                    {task.percent}%
                  </span>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
