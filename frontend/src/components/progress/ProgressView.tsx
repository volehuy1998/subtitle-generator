import { useEffect, useRef } from 'react'
import { useTaskStore } from '@/store/taskStore'
import { useUIStore } from '@/store/uiStore'
import { useSSE } from '@/hooks/useSSE'
import { api } from '@/api/client'
import { PipelineSteps } from './PipelineSteps'

interface Props {
  taskId: string
}

function formatBytes(bytes: number | null): string {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatTimestamp(sec: number): string {
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = Math.floor(sec % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

export function ProgressView({ taskId }: Props) {
  useSSE(taskId)
  const store = useTaskStore()
  const { setAppMode } = useUIStore()
  const segmentsEndRef = useRef<HTMLDivElement>(null)

  const {
    filename, fileSize, status, percent, message, isPaused,
    isPauseRequesting, isCancelRequesting,
    isComplete, activeStep, stepTimings, liveSegments, warning,
  } = store

  const isActive = !isComplete && status !== 'error' && status !== 'cancelled'
  const anyRequesting = isPauseRequesting || isCancelRequesting

  // Auto-scroll segments
  useEffect(() => {
    segmentsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [liveSegments.length])

  const handlePauseResume = async () => {
    store.setPauseRequesting(true)
    if (isPaused) {
      await api.resume(taskId).catch(() => { store.setPauseRequesting(false) })
    } else {
      await api.pause(taskId).catch(() => { store.setPauseRequesting(false) })
    }
  }

  const handleCancel = async () => {
    if (!window.confirm('Cancel the transcription?')) return
    store.setCancelRequesting(true)
    await api.cancel(taskId).catch(() => { store.setCancelRequesting(false) })
  }

  const progressBarColor =
    isComplete ? 'var(--color-success)' :
    status === 'error' ? 'var(--color-danger)' :
    status === 'cancelled' ? 'var(--color-danger)' :
    isPaused || isPauseRequesting ? 'var(--color-warning)' :
    'var(--color-primary)'

  const statusColor =
    isComplete ? 'var(--color-success)' :
    status === 'error' ? 'var(--color-danger)' :
    status === 'cancelled' ? 'var(--color-danger)' :
    isPaused || isPauseRequesting ? 'var(--color-warning)' :
    'var(--color-text-2)'

  // Status text logic
  const statusText =
    status === 'error' ? (store.error ?? 'An error occurred') :
    status === 'cancelled' ? 'Task cancelled.' :
    isCancelRequesting ? 'Cancelling...' :
    isPaused ? 'Paused' :
    isPauseRequesting ? 'Pausing after current segment...' :
    message

  // Pause button label
  const pauseLabel =
    isPauseRequesting && !isPaused ? 'Pausing...' :
    isPauseRequesting && isPaused ? 'Resuming...' :
    isPaused ? 'Resume' :
    'Pause'

  return (
    <div className="flex flex-col gap-5">
      {/* File info row */}
      <div
        className="flex items-center gap-3 px-3 py-2.5 rounded-lg"
        style={{ background: 'var(--color-surface-2)' }}
      >
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: 'var(--color-primary-light)' }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <rect x="2" y="1" width="9" height="12" rx="1.5" stroke="var(--color-primary)" strokeWidth="1.2" fill="none" />
            <path d="M11 1l3 3v9a1.5 1.5 0 01-1.5 1.5H11" stroke="var(--color-primary)" strokeWidth="1.2" strokeLinejoin="round" fill="none" />
            <path d="M5 6h4M5 9h3" stroke="var(--color-primary)" strokeWidth="1.2" strokeLinecap="round" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <p
            className="text-sm font-medium truncate"
            style={{ color: 'var(--color-text)' }}
          >
            {filename ?? 'Processing…'}
          </p>
          {fileSize && (
            <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>
              {formatBytes(fileSize)}
            </p>
          )}
        </div>
        {isComplete && (
          <span
            className="text-xs font-medium px-2 py-0.5 rounded-full"
            style={{
              background: 'var(--color-success-light)',
              color: 'var(--color-success)',
            }}
          >
            Done
          </span>
        )}
      </div>

      {/* Pipeline steps */}
      <PipelineSteps
        activeStep={activeStep}
        stepTimings={stepTimings}
        isPaused={isPaused}
      />

      {/* Progress bar */}
      <div className="flex flex-col gap-2">
        <div
          className="h-1.5 rounded-full overflow-hidden"
          style={{ background: 'var(--color-border)' }}
        >
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${percent}%`,
              background: progressBarColor,
            }}
          />
        </div>

        {/* Status / percent row */}
        <div className="flex items-center justify-between">
          <span className="text-xs" style={{ color: statusColor }}>
            {statusText}
          </span>
          <span
            className="text-xs font-semibold tabular-nums"
            style={{ color: isComplete ? 'var(--color-success)' : 'var(--color-primary)' }}
          >
            {percent}%
          </span>
        </div>
      </div>

      {/* Warning */}
      {warning && (
        <div
          className="flex items-start gap-2 px-3 py-2 rounded-lg text-xs"
          style={{
            background: 'var(--color-warning-light)',
            border: '1px solid #FDE68A',
            color: 'var(--color-text)',
          }}
        >
          <span style={{ color: 'var(--color-warning)' }}>⚠</span>
          {warning}
        </div>
      )}

      {/* Live subtitles panel */}
      {liveSegments.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <span
            className="text-xs font-semibold tracking-wider"
            style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
          >
            LIVE PREVIEW
          </span>
          <div
            className="flex flex-col gap-1 overflow-y-auto rounded-lg p-3"
            style={{
              maxHeight: '200px',
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border)',
            }}
          >
            {liveSegments.map((seg, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span
                  className="font-mono flex-shrink-0"
                  style={{ color: 'var(--color-primary)', fontSize: '11px' }}
                >
                  {formatTimestamp(seg.start)}
                </span>
                <span style={{ color: 'var(--color-text)' }}>{seg.text}</span>
              </div>
            ))}
            <div ref={segmentsEndRef} />
          </div>
        </div>
      )}

      {/* Task controls */}
      {isActive && (
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handlePauseResume}
            disabled={anyRequesting}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition-all"
            style={{
              background: 'var(--color-surface)',
              borderColor: isPaused ? 'var(--color-success)' : isPauseRequesting ? 'var(--color-warning)' : 'var(--color-border)',
              color: isPaused ? 'var(--color-success)' : isPauseRequesting ? 'var(--color-warning)' : 'var(--color-text)',
              opacity: anyRequesting ? 0.6 : 1,
              cursor: anyRequesting ? 'not-allowed' : 'pointer',
            }}
          >
            {isPaused ? (
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                <path d="M3 2l7 4-7 4V2z" fill="currentColor" />
              </svg>
            ) : (
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                <rect x="2.5" y="2" width="2.5" height="8" rx="1" fill="currentColor" />
                <rect x="7" y="2" width="2.5" height="8" rx="1" fill="currentColor" />
              </svg>
            )}
            {pauseLabel}
          </button>

          <button
            type="button"
            onClick={handleCancel}
            disabled={isCancelRequesting}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition-all"
            style={{
              background: 'var(--color-surface)',
              borderColor: isCancelRequesting ? 'var(--color-danger)' : 'var(--color-border)',
              color: 'var(--color-danger)',
              opacity: isCancelRequesting ? 0.6 : 1,
              cursor: isCancelRequesting ? 'not-allowed' : 'pointer',
            }}
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
              <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            {isCancelRequesting ? 'Cancelling...' : 'Cancel'}
          </button>
        </div>
      )}

      {/* Cancelled view */}
      {status === 'cancelled' && (
        <div className="flex flex-col items-center gap-3 py-4">
          <span className="text-sm" style={{ color: 'var(--color-text-3)' }}>
            Task cancelled.
          </span>
          <button
            type="button"
            onClick={() => { store.reset(); setAppMode('transcribe') }}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium border transition-all"
            style={{
              background: 'var(--color-surface)',
              borderColor: 'var(--color-border)',
              color: 'var(--color-text)',
            }}
          >
            Try Again
          </button>
        </div>
      )}

      {/* Done: process next */}
      {isComplete && (
        <button
          type="button"
          onClick={() => {
            store.reset()
            setAppMode('transcribe')
          }}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium border transition-all"
          style={{
            background: 'var(--color-surface)',
            borderColor: 'var(--color-border)',
            color: 'var(--color-text)',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M7 2v10M2 7h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          Process Another File
        </button>
      )}
    </div>
  )
}
