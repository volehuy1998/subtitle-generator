import { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { useTaskStore } from '@/store/taskStore'
import { useUIStore } from '@/store/uiStore'
import { useToastStore } from '@/store/toastStore'
import { usePreferencesStore } from '@/store/preferencesStore'
import { useSSE } from '@/hooks/useSSE'
import { api } from '@/api/client'
import { PipelineSteps } from './PipelineSteps'
import { LivenessIndicator } from './LivenessIndicator'
import { CancelConfirmationDialog } from './CancelConfirmationDialog'
import { SubtitlePreview } from './SubtitlePreview'

// Clock tick for stale detection — Pixel (Sr. Frontend), Sprint L13
let staleClockListeners: Array<() => void> = [];
let staleClockSnapshot = Date.now();
setInterval(() => {
  staleClockSnapshot = Date.now();
  staleClockListeners.forEach((fn) => fn());
}, 5000);
function subscribeStale(cb: () => void) {
  staleClockListeners.push(cb);
  return () => { staleClockListeners = staleClockListeners.filter((fn) => fn !== cb); };
}
function getStaleSnapshot() { return staleClockSnapshot; }

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
    isUploading, uploadPercent, uploadEta,
  } = store

  const { processed_sec: processedSec, total_sec: totalSec, speed_x: speedX, eta, elapsed } = store
  const { estimated_segments: estimatedSegments, current_segment: currentSegment, substage } = store

  const [showCancelDialog, setShowCancelDialog] = useState(false)
  const [queuePosition, setQueuePosition] = useState<number | null>(null)
  const [queueEta, setQueueEta] = useState<string | null>(null)
  const [previewMode, setPreviewMode] = useState<'segments' | 'srt'>('segments')
  const addToast = useToastStore((s) => s.addToast)

  const isTranscribing = status === 'transcribing' && processedSec !== undefined && totalSec !== undefined && totalSec > 0

  const isActive = !isComplete && status !== 'error' && status !== 'cancelled'
  const anyRequesting = isPauseRequesting || isCancelRequesting

  // Stale warning: show after 30s with no SSE event — Pixel (Sr. Frontend), Sprint L13
  const now = useSyncExternalStore(subscribeStale, getStaleSnapshot)
  const secSinceUpdate = (now - store.lastEventTime) / 1000
  const isStale = isActive && !isUploading && secSinceUpdate > 30

  // Auto-scroll segments
  useEffect(() => {
    segmentsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [liveSegments.length])

  // Auto-copy on completion when autoCopy preference is enabled — Pixel (Sr. Frontend), Sprint L49
  useEffect(() => {
    if (isComplete && liveSegments.length > 0) {
      const prefs = usePreferencesStore.getState()
      if (prefs.autoCopy) {
        const text = liveSegments.map((s) => s.text).join('\n')
        navigator.clipboard.writeText(text).then(() => {
          addToast('info', 'Subtitles copied to clipboard')
        }).catch(() => {})
      }
    }
  }, [isComplete]) // eslint-disable-line react-hooks/exhaustive-deps

  // Poll queue position when task is queued — Pixel (Sr. Frontend), Sprint L44
  useEffect(() => {
    if (status !== 'queued' || !taskId) {
      setQueuePosition(null)
      setQueueEta(null)
      return
    }
    let cancelled = false
    const poll = () => {
      fetch(`/tasks/${taskId}/position`)
        .then((r) => r.json())
        .then((data: { position?: number; estimated_wait?: string }) => {
          if (cancelled) return
          setQueuePosition(data.position ?? null)
          setQueueEta(data.estimated_wait ?? null)
        })
        .catch(() => {})
    }
    poll()
    const interval = setInterval(poll, 5000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [status, taskId])

  // Copy all segments to clipboard — Pixel (Sr. Frontend), Sprint L43
  const handleCopyAll = async () => {
    const text = liveSegments.map((seg) => seg.text).join('\n')
    try {
      await navigator.clipboard.writeText(text)
      addToast('success', 'Copied to clipboard')
    } catch {
      addToast('error', 'Failed to copy to clipboard')
    }
  }

  const handlePauseResume = async () => {
    store.setPauseRequesting(true)
    if (isPaused) {
      await api.resume(taskId).catch(() => { store.setPauseRequesting(false) })
    } else {
      await api.pause(taskId).catch(() => { store.setPauseRequesting(false) })
    }
  }

  const handleCancel = async () => {
    setShowCancelDialog(true)
  }

  const handleCancelConfirm = async () => {
    setShowCancelDialog(false)
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

  // Status text logic (used for non-transcribing phases)
  const statusText =
    status === 'error' ? (store.error ?? 'An error occurred') :
    status === 'cancelled' ? 'Task cancelled.' :
    isCancelRequesting ? 'Cancelling...' :
    isPaused ? 'Paused' :
    isPauseRequesting ? 'Pausing after current segment...' :
    substage === 'loading_model' ? 'Loading model...' :
    substage === 'transcribing' ? 'Transcribing audio...' :
    message

  // Pause button label
  const pauseLabel =
    isPauseRequesting && !isPaused ? 'Pausing...' :
    isPauseRequesting && isPaused ? 'Resuming...' :
    isPaused ? 'Resume' :
    'Pause'

  // Audio progress ratio for the mini bar
  const audioRatio = (isTranscribing && totalSec > 0)
    ? Math.min((processedSec ?? 0) / totalSec, 1)
    : 0

  return (
    <div className="flex flex-col gap-5 animate-fade-in" aria-live="polite">
      {/* Success celebration banner */}
      {isComplete && (
        <div
          className="animate-success-fade-in flex items-start gap-3 px-4 py-3 rounded-lg"
          role="status"
          style={{
            background: 'var(--color-success-light)',
            border: '1px solid var(--color-success-border)',
          }}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true" className="flex-shrink-0 mt-0.5">
            <circle cx="10" cy="10" r="9" stroke="var(--color-success)" strokeWidth="1.5" fill="none" />
            <path d="M6 10l3 3 5-6" stroke="var(--color-success)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <div className="flex flex-col gap-1">
            <span className="text-sm font-semibold" style={{ color: 'var(--color-success)' }}>
              Transcription complete!
            </span>
            <div className="flex items-center gap-2 flex-wrap text-xs" style={{ color: 'var(--color-text-2)' }}>
              {liveSegments.length > 0 && (
                <span>{liveSegments.length} segment{liveSegments.length !== 1 ? 's' : ''}</span>
              )}
              {totalSec && totalSec > 0 && (
                <span>{formatTimestamp(totalSec)} total</span>
              )}
              {store.language && (
                <span>{store.language}</span>
              )}
            </div>
          </div>
        </div>
      )}

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
        isUploading={isUploading}
        uploadPercent={uploadPercent}
      />

      {/* Progress bar */}
      <div className="flex flex-col gap-2">
        <div
          className="h-1.5 rounded-full overflow-hidden"
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Task progress"
          style={{ background: 'var(--color-border)' }}
        >
          <div
            className={`h-full rounded-full transition-all duration-500${isActive && !isPaused && !isComplete ? ' progress-bar-shimmer' : ''}`}
            style={{
              width: `${percent}%`,
              ...((isActive && !isPaused && !isComplete) ? {} : { background: progressBarColor }),
            }}
          />
        </div>

        {/* Status / percent row */}
        <div className="flex items-center justify-between" aria-live="assertive">
          <span className="text-xs" style={{ color: statusColor }}>
            {isUploading && uploadEta
              ? `Uploading... ${uploadEta} remaining`
              : isTranscribing && !isPaused && !isCancelRequesting
                ? 'Transcribing audio...'
                : statusText}
          </span>
          <span
            className="text-xs font-semibold tabular-nums"
            style={{ color: isComplete ? 'var(--color-success)' : 'var(--color-primary)' }}
          >
            {percent}%
          </span>
          {/* Phase Lumen: liveness indicator */}
          <LivenessIndicator />
        </div>
      </div>

      {/* Transcription detail panel — only during active transcription */}
      {isTranscribing && (
        <div
          className="rounded-lg px-3 py-2.5"
          style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border)' }}
        >
          {/* Audio position bar */}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs tabular-nums font-medium" style={{ color: 'var(--color-primary)', minWidth: '36px' }}>
              {formatTimestamp(processedSec ?? 0)}
            </span>
            <div
              className="flex-1 h-1 rounded-full overflow-hidden"
              style={{ background: 'var(--color-border)' }}
            >
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${audioRatio * 100}%`, background: 'var(--color-primary)' }}
              />
            </div>
            <span className="text-xs tabular-nums" style={{ color: 'var(--color-text-3)', minWidth: '36px', textAlign: 'right' }}>
              {formatTimestamp(totalSec ?? 0)}
            </span>
          </div>

          {/* Stats row */}
          <div className="flex items-center gap-3 flex-wrap">
            {/* Speed */}
            {speedX !== undefined && speedX > 0 && (
              <div className="flex items-center gap-1" title="Processing speed relative to audio duration. 2.0x means 1 minute of audio is processed in 30 seconds.">
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
                  <path d="M5 1v4l2.5 1.5" stroke="var(--color-text-3)" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
                  <circle cx="5" cy="5" r="4" stroke="var(--color-text-3)" strokeWidth="1" fill="none" />
                </svg>
                <span className="text-xs tabular-nums" style={{ color: 'var(--color-text-2)', cursor: 'help' }}>
                  {speedX.toFixed(1)}x realtime
                </span>
              </div>
            )}

            {/* ETA */}
            <div className="flex items-center gap-1" title="Estimated Time of Arrival — approximate time until transcription completes, based on current processing speed.">
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
                <path d="M5 2v3h3" stroke="var(--color-text-3)" strokeWidth="1" strokeLinecap="round" />
                <circle cx="5" cy="5" r="4" stroke="var(--color-text-3)" strokeWidth="1" fill="none" />
              </svg>
              <span className="text-xs tabular-nums" style={{ color: 'var(--color-text-2)', cursor: 'help' }}>
                {!eta || eta === '-' || eta === '0:00' ? 'Calculating...' : `~${eta} remaining`}
              </span>
            </div>

            {/* Elapsed */}
            {elapsed && elapsed !== '0:00' && (
              <div className="flex items-center gap-1" title="Total wall-clock time since transcription started.">
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
                  <path d="M2 8l3-3 2 1.5L8 3" stroke="var(--color-text-3)" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                </svg>
                <span className="text-xs tabular-nums" style={{ color: 'var(--color-text-3)', cursor: 'help' }}>
                  {elapsed} elapsed
                </span>
              </div>
            )}

            {/* Segments found */}
            {(liveSegments.length > 0 || (currentSegment && currentSegment > 0)) && (
              <div className="flex items-center gap-1" title="Number of subtitle segments (sentences or phrases) detected so far.">
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
                  <rect x="1" y="2" width="8" height="1.5" rx="0.5" fill="var(--color-text-3)" />
                  <rect x="1" y="4.5" width="6" height="1.5" rx="0.5" fill="var(--color-text-3)" />
                  <rect x="1" y="7" width="7" height="1.5" rx="0.5" fill="var(--color-text-3)" />
                </svg>
                <span className="text-xs tabular-nums" style={{ color: 'var(--color-text-3)', cursor: 'help' }}>
                  {currentSegment && estimatedSegments
                    ? `${currentSegment} of ~${estimatedSegments} segments`
                    : `${liveSegments.length} segments`}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Warning */}
      {warning && (
        <div
          className="flex items-start gap-2 px-3 py-2 rounded-lg text-xs"
          role="alert"
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

      {/* Stale warning — Pixel (Sr. Frontend), Sprint L13 */}
      {isStale && (
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs"
          style={{
            background: 'var(--color-warning-light)',
            border: '1px solid #FDE68A',
            color: 'var(--color-text)',
          }}
        >
          <span style={{ color: 'var(--color-warning)' }}>⚠</span>
          This is taking longer than expected. The system is still working.
        </div>
      )}

      {/* Queue position indicator — Pixel (Sr. Frontend), Sprint L44 */}
      {status === 'queued' && (
        <div
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg"
          style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border)' }}
        >
          <svg className="animate-spin flex-shrink-0" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <circle cx="7" cy="7" r="5.5" stroke="var(--color-border-2)" strokeWidth="1.5" />
            <path d="M12.5 7a5.5 5.5 0 00-5.5-5.5" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <div className="flex flex-col gap-0.5">
            <span className="text-xs font-medium" style={{ color: 'var(--color-text)' }}>
              {queuePosition !== null && queuePosition > 0
                ? `Queued — position ${queuePosition}`
                : 'Queued — waiting to start'}
            </span>
            {queueEta && (
              <span className="text-xs" style={{ color: 'var(--color-text-3)' }}>
                Estimated wait: {queueEta}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Live subtitles panel — with Segments / SRT Preview toggle (Sprint L45) */}
      {liveSegments.length > 0 && (() => {
        const maxVisible = 50
        const visibleSegments = liveSegments.length > maxVisible
          ? liveSegments.slice(-maxVisible)
          : liveSegments
        return (
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              {/* Tab toggle: Segments vs SRT Preview — Pixel (Sr. Frontend), Sprint L45 */}
              <div className="flex items-center gap-0.5">
                <button
                  type="button"
                  onClick={() => setPreviewMode('segments')}
                  className="text-xs font-semibold tracking-wider px-2 py-1 rounded transition-colors"
                  style={{
                    letterSpacing: '0.07em',
                    background: previewMode === 'segments' ? 'var(--color-surface-2)' : 'transparent',
                    color: previewMode === 'segments' ? 'var(--color-primary)' : 'var(--color-text-3)',
                    border: 'none',
                    cursor: 'pointer',
                  }}
                >
                  SEGMENTS
                </button>
                {isComplete && (
                  <button
                    type="button"
                    onClick={() => setPreviewMode('srt')}
                    className="text-xs font-semibold tracking-wider px-2 py-1 rounded transition-colors"
                    style={{
                      letterSpacing: '0.07em',
                      background: previewMode === 'srt' ? 'var(--color-surface-2)' : 'transparent',
                      color: previewMode === 'srt' ? 'var(--color-primary)' : 'var(--color-text-3)',
                      border: 'none',
                      cursor: 'pointer',
                    }}
                  >
                    SRT PREVIEW
                  </button>
                )}
              </div>
              <div className="flex items-center gap-3">
                {previewMode === 'segments' && liveSegments.length > maxVisible && (
                  <span className="text-xs" style={{ color: 'var(--color-text-3)' }}>
                    Showing last {maxVisible} of {liveSegments.length} segments
                  </span>
                )}
                {/* Copy All button — Pixel (Sr. Frontend), Sprint L43 */}
                {isComplete && liveSegments.length > 0 && previewMode === 'segments' && (
                  <button
                    type="button"
                    onClick={handleCopyAll}
                    className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border transition-colors"
                    style={{
                      background: 'var(--color-surface)',
                      borderColor: 'var(--color-border)',
                      color: 'var(--color-text-2)',
                      cursor: 'pointer',
                    }}
                    title="Copy all segment text to clipboard"
                  >
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                      <rect x="4" y="4" width="6.5" height="6.5" rx="1" stroke="currentColor" strokeWidth="1.2" fill="none" />
                      <path d="M8 4V2.5A1 1 0 007 1.5H2.5A1 1 0 001.5 2.5V7a1 1 0 001 1H4" stroke="currentColor" strokeWidth="1.2" fill="none" />
                    </svg>
                    Copy All
                  </button>
                )}
              </div>
            </div>

            {/* Segments view */}
            {previewMode === 'segments' && (
              <div
                className="flex flex-col gap-1 overflow-y-auto rounded-lg p-3"
                role="log"
                aria-live="polite"
                aria-label="Live subtitle preview"
                style={{
                  maxHeight: '200px',
                  background: 'var(--color-surface-2)',
                  border: '1px solid var(--color-border)',
                }}
              >
                {visibleSegments.map((seg, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs">
                    <span
                      className="font-mono flex-shrink-0"
                      style={{ color: 'var(--color-primary)', fontSize: '11px' }}
                    >
                      {formatTimestamp(seg.start)}
                    </span>
                    <span
                      title={seg.text}
                      style={{
                        color: 'var(--color-text)',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical' as const,
                        overflow: 'hidden',
                        wordBreak: 'break-word',
                      }}
                    >
                      {seg.text}
                    </span>
                  </div>
                ))}
                <div ref={segmentsEndRef} />
              </div>
            )}

            {/* SRT Preview view — Pixel (Sr. Frontend), Sprint L45 */}
            {previewMode === 'srt' && isComplete && (
              <SubtitlePreview taskId={taskId} />
            )}
          </div>
        )
      })()}

      {/* Task controls (hide during upload) */}
      {isActive && !isUploading && (
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handlePauseResume}
            disabled={anyRequesting}
            className="btn-interactive flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border"
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
            className="btn-interactive flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border"
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

      {/* Error view */}
      {status === 'error' && (
        <div className="flex flex-col gap-3 py-4">
          <div
            className="flex items-start gap-2.5 px-3 py-2.5 rounded-lg"
            role="alert"
            style={{
              background: 'var(--color-danger-light)',
              border: '1px solid var(--color-danger)',
            }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" className="flex-shrink-0 mt-0.5">
              <circle cx="8" cy="8" r="7" stroke="var(--color-danger)" strokeWidth="1.5" fill="none" />
              <path d="M8 4.5v4M8 10.5v1" stroke="var(--color-danger)" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <div className="text-xs font-medium" style={{ color: 'var(--color-danger)' }}>
              <p style={{ margin: '0 0 4px 0', fontWeight: 600 }}>Something went wrong</p>
              <p style={{ margin: 0, color: 'var(--color-text-2)', fontWeight: 400 }}>
                {store.error ?? 'An unexpected error occurred during processing. Please try again with a different file or model.'}
              </p>
            </div>
          </div>
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

      {/* Cancelled view */}
      {status === 'cancelled' && (
        <div className="flex flex-col items-center gap-3 py-4">
          <span className="text-sm" style={{ color: 'var(--color-text-3)' }}>
            Transcription cancelled.
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
            Start Over
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
          className="btn-interactive btn-process-next flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium border"
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

      {/* Cancel confirmation dialog — Pixel (Sr. Frontend Engineer), Sprint L8 */}
      {showCancelDialog && (
        <CancelConfirmationDialog
          filename={filename ?? 'this file'}
          onConfirm={handleCancelConfirm}
          onCancel={() => setShowCancelDialog(false)}
        />
      )}
    </div>
  )
}
