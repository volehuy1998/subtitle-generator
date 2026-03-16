import { useEffect, useState, useCallback } from 'react'
import { api } from '@/api/client'
import type { TaskListItem } from '@/api/types'
import { Skeleton } from '@/components/ui/Skeleton'
import { Dialog } from '@/components/ui/Dialog'
import { useToastStore } from '@/store/toastStore'

/**
 * TaskHistory — shows last 5 completed/failed tasks with quick access to downloads.
 * Polls GET /tasks?session_only=true on mount.
 * — Pixel (Sr. Frontend), Sprint L17 (loading skeletons: L18, delete dialog: L41)
 */

function timeAgo(dateStr: string): string {
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diffSec = Math.floor((now - then) / 1000)
  if (diffSec < 60) return 'just now'
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`
  return `${Math.floor(diffSec / 86400)}d ago`
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'done') {
    return (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-label="Completed">
        <circle cx="7" cy="7" r="6" stroke="var(--color-success)" strokeWidth="1.5" fill="none" />
        <path d="M4.5 7l2 2 3-3.5" stroke="var(--color-success)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    )
  }
  if (status === 'error') {
    return (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-label="Error">
        <circle cx="7" cy="7" r="6" stroke="var(--color-danger)" strokeWidth="1.5" fill="none" />
        <path d="M5 5l4 4M9 5l-4 4" stroke="var(--color-danger)" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    )
  }
  // cancelled or other
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-label="Cancelled">
      <circle cx="7" cy="7" r="6" stroke="var(--color-text-3)" strokeWidth="1.5" fill="none" />
      <path d="M4.5 7h5" stroke="var(--color-text-3)" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

function TrashIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <path d="M3 4h8M5.5 4V3a.5.5 0 01.5-.5h2a.5.5 0 01.5.5v1M4.5 4v7a1 1 0 001 1h3a1 1 0 001-1V4"
        stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function TaskHistory() {
  const [tasks, setTasks] = useState<TaskListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<{ taskId: string; filename: string } | null>(null)
  const [filterText, setFilterText] = useState('')
  const addToast = useToastStore((s) => s.addToast)

  const fetchTasks = useCallback(() => {
    api.tasksBySession()
      .then((res) => {
        // Filter to terminal states and take last 5, most recent first
        const terminal = res.tasks
          .filter((t) => t.status === 'done' || t.status === 'error' || t.status === 'cancelled')
          .slice(0, 5)
        setTasks(terminal)
      })
      .catch(() => {
        // silently fail — not critical
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  const handleDeleteClick = (taskId: string, filename?: string) => {
    setDeleteTarget({ taskId, filename: filename ?? taskId.slice(0, 8) })
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return
    const { taskId } = deleteTarget
    setDeleteTarget(null)
    setDeleting(taskId)
    try {
      await api.deleteTask(taskId)
      setTasks((prev) => prev.filter((t) => t.task_id !== taskId))
      addToast('success', 'Task deleted')
    } catch {
      addToast('error', 'Failed to delete task')
      fetchTasks()
    } finally {
      setDeleting(null)
    }
  }

  if (loading) {
    return (
      <div
        className="rounded-xl overflow-hidden"
        style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div
          className="px-4 py-3"
          style={{ borderBottom: '1px solid var(--color-border)' }}
        >
          <Skeleton width="100px" height="10px" />
        </div>
        <div className="flex flex-col">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="flex items-center gap-3 px-4 py-2.5"
              style={{ borderBottom: '1px solid var(--color-border)' }}
            >
              <Skeleton width="14px" height="14px" borderRadius="50%" />
              <Skeleton width={`${70 - i * 10}%`} height="12px" />
              <Skeleton width="32px" height="10px" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Filter tasks by filename — Pixel (Sr. Frontend), Sprint L51
  const filteredTasks = filterText.trim()
    ? tasks.filter((t) =>
        (t.filename ?? t.task_id).toLowerCase().includes(filterText.trim().toLowerCase())
      )
    : tasks

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      {/* Header */}
      <div
        className="px-4 py-3 flex flex-col gap-2"
        style={{ borderBottom: '1px solid var(--color-border)' }}
      >
        <h2
          className="text-xs font-semibold tracking-wider"
          style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
        >
          RECENT TASKS
        </h2>
        {/* Search filter — Pixel (Sr. Frontend), Sprint L51 */}
        {tasks.length > 0 && (
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder="Filter tasks..."
              className="flex-1 text-xs px-2.5 py-1.5 rounded-md outline-none transition-colors"
              style={{
                background: 'var(--color-surface-2)',
                border: '1px solid var(--color-border)',
                color: 'var(--color-text)',
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary)' }}
              onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)' }}
            />
            {filterText && (
              <span className="text-xs flex-shrink-0" style={{ color: 'var(--color-text-3)' }}>
                {filteredTasks.length} of {tasks.length} task{tasks.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Body */}
      <div className="flex flex-col">
        {filteredTasks.length === 0 ? (
          <div className="px-4 py-6 text-center">
            <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>
              {filterText ? 'No matching tasks' : 'No recent tasks'}
            </p>
          </div>
        ) : (
          filteredTasks.map((task) => (
            <div
              key={task.task_id}
              className="flex items-center gap-3 px-4 py-2.5 group"
              style={{ borderBottom: '1px solid var(--color-border)' }}
            >
              {/* Status icon */}
              <StatusIcon status={task.status} />

              {/* Filename — truncated */}
              <span
                className="flex-1 text-xs truncate"
                style={{ color: 'var(--color-text)', minWidth: 0 }}
                title={task.filename ?? task.task_id}
              >
                {task.filename ?? task.task_id.slice(0, 12)}
              </span>

              {/* Time ago */}
              {task.created_at && (
                <span
                  className="text-xs flex-shrink-0"
                  style={{ color: 'var(--color-text-3)', fontSize: '11px' }}
                >
                  {timeAgo(task.created_at)}
                </span>
              )}

              {/* Download link (done tasks only) */}
              {task.status === 'done' && (
                <a
                  href={api.downloadUrl(task.task_id, 'srt')}
                  download
                  className="flex-shrink-0 btn-interactive rounded p-1"
                  style={{ color: 'var(--color-primary)' }}
                  title="Download SRT"
                  onClick={() => addToast('info', 'Download started')}
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                    <path d="M7 2v7M4 6.5L7 9.5 10 6.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M2 11h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </a>
              )}

              {/* Delete button */}
              <button
                type="button"
                onClick={() => handleDeleteClick(task.task_id, task.filename)}
                disabled={deleting === task.task_id}
                className="flex-shrink-0 rounded p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: deleting === task.task_id ? 'var(--color-text-3)' : 'var(--color-danger)',
                  cursor: deleting === task.task_id ? 'not-allowed' : 'pointer',
                }}
                title="Delete task"
              >
                <TrashIcon />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Delete confirmation dialog — Pixel (Sr. Frontend), Sprint L41 */}
      <Dialog
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        title="Delete task"
        description={`Delete task and files for "${deleteTarget?.filename ?? ''}"? This action cannot be undone.`}
        actions={
          <>
            <button
              type="button"
              onClick={() => setDeleteTarget(null)}
              className="px-4 py-2 rounded-lg text-sm font-medium border transition-colors"
              style={{
                background: 'var(--color-surface)',
                borderColor: 'var(--color-border)',
                color: 'var(--color-text)',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDeleteConfirm}
              className="px-4 py-2 rounded-lg text-sm font-medium border transition-colors"
              style={{
                background: 'var(--color-danger)',
                borderColor: 'var(--color-danger)',
                color: 'white',
                cursor: 'pointer',
              }}
            >
              Delete
            </button>
          </>
        }
      >
        <div />
      </Dialog>
    </div>
  )
}
