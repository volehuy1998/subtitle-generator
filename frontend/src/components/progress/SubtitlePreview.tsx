/**
 * SubtitlePreview — shows formatted SRT output in a code block.
 * Fetches from GET /preview/{task_id}?limit=50 when the "SRT Preview" tab is active.
 *
 * — Pixel (Sr. Frontend), Sprint L45
 */

import { useEffect, useState } from 'react'
import { api } from '@/api/client'

interface Props {
  taskId: string
}

function formatSrtTimestamp(sec: number): string {
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = Math.floor(sec % 60)
  const ms = Math.round((sec - Math.floor(sec)) * 1000)
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms).padStart(3, '0')}`
}

export function SubtitlePreview({ taskId }: Props) {
  const [srtText, setSrtText] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [totalSegments, setTotalSegments] = useState(0)
  const [shownSegments, setShownSegments] = useState(0)

  useEffect(() => {
    let cancelled = false
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    setError(null)

    api.preview(taskId, 50)
      .then((data) => {
        if (cancelled) return
        setTotalSegments(data.total_segments)
        setShownSegments(data.segments.length)

        // Format as SRT
        const lines = data.segments.map((seg, i) => {
          const num = i + 1
          const start = formatSrtTimestamp(seg.start)
          const end = formatSrtTimestamp(seg.end)
          return `${num}\n${start} --> ${end}\n${seg.text}`
        })
        setSrtText(lines.join('\n\n'))
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Failed to load preview')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [taskId])

  if (loading) {
    return (
      <div
        className="flex items-center justify-center py-8"
        style={{ color: 'var(--color-text-3)' }}
      >
        <svg className="animate-spin mr-2" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <circle cx="7" cy="7" r="5.5" stroke="var(--color-border-2)" strokeWidth="1.5" />
          <path d="M12.5 7a5.5 5.5 0 00-5.5-5.5" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <span className="text-xs">Loading preview...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div
        className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs"
        style={{
          background: 'var(--color-danger-light)',
          border: '1px solid var(--color-danger)',
          color: 'var(--color-danger)',
        }}
      >
        {error}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-1.5">
      {totalSegments > shownSegments && (
        <span className="text-xs" style={{ color: 'var(--color-text-3)' }}>
          Showing first {shownSegments} of {totalSegments} segments
        </span>
      )}
      <pre
        className="overflow-y-auto rounded-lg p-3 text-xs"
        style={{
          maxHeight: '200px',
          background: 'var(--color-surface-2)',
          border: '1px solid var(--color-border)',
          color: 'var(--color-text)',
          fontFamily: 'var(--font-family-mono)',
          margin: 0,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          lineHeight: 1.5,
          tabSize: 4,
        }}
      >
        {srtText}
      </pre>
    </div>
  )
}
