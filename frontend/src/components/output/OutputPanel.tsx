import { useTaskStore } from '@/store/taskStore'
import { DownloadButtons } from './DownloadButtons'
import { TimingBreakdown } from './TimingBreakdown'
import { EmbedPanel } from '../embed/EmbedPanel'

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12 px-4 text-center">
      {/* Telescope SVG */}
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
        <circle cx="24" cy="24" r="23" stroke="var(--color-border)" strokeWidth="1.5" fill="none" />
        <path
          d="M14 30l6-12 14-4-12 18-8-2z"
          stroke="var(--color-border-2)"
          strokeWidth="1.5"
          strokeLinejoin="round"
          fill="none"
        />
        <circle cx="28" cy="20" r="3" stroke="var(--color-border-2)" strokeWidth="1.5" fill="none" />
        <path d="M18 34l-2 4M22 34l2 4" stroke="var(--color-border-2)" strokeWidth="1.5" strokeLinecap="round" />
      </svg>

      <div className="flex flex-col gap-1">
        <p
          className="text-sm font-medium"
          style={{ color: 'var(--color-text-2)' }}
        >
          No results yet
        </p>
        <p
          className="text-xs"
          style={{ color: 'var(--color-text-3)' }}
        >
          Upload a file to get started
        </p>
      </div>
    </div>
  )
}

function formatDuration(sec: number | null): string {
  if (!sec) return ''
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  if (m === 0) return `${s}s`
  return `${m}m ${s}s`
}

export function OutputPanel() {
  const store = useTaskStore()
  const { taskId, isComplete, filename, language, segments, totalTimeSec, stepTimings, isVideo } = store

  const showResults = isComplete && taskId

  return (
    <div
      className="flex flex-col rounded-xl overflow-hidden"
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-sm)',
        minHeight: '200px',
      }}
    >
      {/* Header */}
      <div
        className="px-4 py-3"
        style={{ borderBottom: '1px solid var(--color-border)' }}
      >
        <h2
          className="text-xs font-semibold tracking-wider"
          style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
        >
          OUTPUT
        </h2>
      </div>

      {/* Body */}
      <div className="flex flex-col flex-1 p-4 gap-4">
        {!showResults ? (
          <EmptyState />
        ) : (
          <>
            {/* Filename + metadata */}
            <div className="flex flex-col gap-1.5">
              <h3
                className="text-sm font-semibold truncate"
                style={{ color: 'var(--color-text)' }}
              >
                {filename}
              </h3>
              <div className="flex items-center gap-2 flex-wrap">
                {segments > 0 && (
                  <span
                    className="text-xs px-1.5 py-0.5 rounded"
                    style={{
                      background: 'var(--color-surface-2)',
                      color: 'var(--color-text-2)',
                    }}
                  >
                    {segments} segment{segments !== 1 ? 's' : ''}
                  </span>
                )}
                {language && (
                  <span
                    className="text-xs px-1.5 py-0.5 rounded"
                    style={{
                      background: 'var(--color-surface-2)',
                      color: 'var(--color-text-2)',
                    }}
                  >
                    {language}
                  </span>
                )}
                {totalTimeSec && (
                  <span
                    className="text-xs px-1.5 py-0.5 rounded"
                    style={{
                      background: 'var(--color-surface-2)',
                      color: 'var(--color-text-2)',
                    }}
                  >
                    {formatDuration(totalTimeSec)}
                  </span>
                )}
              </div>
            </div>

            {/* Download buttons */}
            <DownloadButtons taskId={taskId} />

            {/* Process next file button */}
            <button
              type="button"
              onClick={() => store.reset()}
              className="flex items-center justify-center gap-2 w-full px-3 py-2 rounded-lg text-xs font-medium border transition-all"
              style={{
                background: 'var(--color-surface)',
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-2)',
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-primary)'
                e.currentTarget.style.color = 'var(--color-primary)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border)'
                e.currentTarget.style.color = 'var(--color-text-2)'
              }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                <path d="M6 1v10M1 6h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              Process Next File
            </button>

            {/* Divider */}
            <div style={{ height: '1px', background: 'var(--color-border)' }} />

            {/* Embed panel (video only) — shown before timing so it's prominent */}
            {isVideo && (
              <div
                className="rounded-lg p-4"
                style={{
                  background: 'var(--color-primary-light)',
                  border: '1px solid var(--color-primary-border, #d8b4fe)',
                }}
              >
                <EmbedPanel taskId={taskId} />
              </div>
            )}

            {/* Timing breakdown */}
            <TimingBreakdown timings={stepTimings} />
          </>
        )}
      </div>
    </div>
  )
}
