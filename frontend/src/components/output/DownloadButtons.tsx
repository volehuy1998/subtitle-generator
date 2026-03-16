/**
 * DownloadButtons — export format selection with single-click download.
 * Sprint L46 adds format selector tabs (SRT | VTT | JSON | All).
 *
 * — Pixel (Sr. Frontend), Sprint L46
 */

import { useState } from 'react'
import { api } from '@/api/client'

interface Props {
  taskId: string
  format?: 'srt' | 'vtt'
  segments?: number
}

type ExportFormat = 'srt' | 'vtt' | 'json' | 'all'

const FORMAT_META: Record<ExportFormat, { label: string; ext: string; description: string }> = {
  srt: { label: 'SRT', ext: 'srt', description: 'SubRip Text — universal format' },
  vtt: { label: 'VTT', ext: 'vtt', description: 'Web Video Text Tracks' },
  json: { label: 'JSON', ext: 'json', description: 'Structured data with timestamps' },
  all: { label: 'All (ZIP)', ext: 'zip', description: 'SRT + VTT + JSON in a ZIP archive' },
}

function DownloadIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M8 2v8M4 7l4 4 4-4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M2 12h12"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  )
}

function estimateSize(segments: number, format: 'srt' | 'vtt' | 'json' | 'zip'): string {
  // Rough estimates: ~80 bytes per segment for SRT, ~75 for VTT, ~120 for JSON
  if (segments <= 0) return ''
  const bytes = format === 'json' ? segments * 120
    : format === 'vtt' ? segments * 75
    : format === 'zip' ? segments * (80 + 75 + 120)
    : segments * 80
  if (bytes < 1024) return `~${bytes} B`
  if (bytes < 1024 * 1024) return `~${Math.round(bytes / 1024)} KB`
  return `~${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function getDownloadUrl(taskId: string, fmt: ExportFormat): string {
  if (fmt === 'all') return api.downloadAllUrl(taskId)
  return api.downloadUrl(taskId, fmt)
}

export function DownloadButtons({ taskId, format, segments = 0 }: Props) {
  // If a specific format was requested (legacy prop), render a single button
  if (format === 'srt' || format === 'vtt') {
    const meta = FORMAT_META[format]
    return (
      <a
        href={api.downloadUrl(taskId, format)}
        download
        className="btn-download btn-interactive flex items-center gap-3 w-full px-4 py-2.5 rounded-lg border text-sm font-medium group"
        style={{ textDecoration: 'none' }}
      >
        <DownloadIcon />
        <div className="flex-1 flex flex-col">
          <span>Download {meta.label}</span>
          <span className="text-xs font-normal" style={{ opacity: 0.75, fontSize: '11px' }}>
            {meta.description}
          </span>
        </div>
        <span
          className="px-1.5 py-0.5 rounded text-xs font-semibold"
          style={{ background: 'rgba(255,255,255,0.2)', color: 'white', fontSize: '11px', letterSpacing: '0.04em' }}
        >
          .{meta.ext}
        </span>
      </a>
    )
  }

  return <FormatSelector taskId={taskId} segments={segments} />
}

/** Format selector with tabs — Pixel (Sr. Frontend), Sprint L46 */
function FormatSelector({ taskId, segments }: { taskId: string; segments: number }) {
  const [selected, setSelected] = useState<ExportFormat>('srt')

  const formats: ExportFormat[] = ['srt', 'vtt', 'json', 'all']
  const meta = FORMAT_META[selected]
  const sizeStr = estimateSize(segments, selected === 'all' ? 'zip' : selected)

  return (
    <div className="flex flex-col gap-2">
      {/* Section header */}
      <h4
        className="text-xs font-semibold tracking-wider"
        style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
      >
        DOWNLOADS
      </h4>

      {/* Format tabs — Pixel (Sr. Frontend), Sprint L46 */}
      <div
        className="flex items-center gap-0.5 p-0.5 rounded-lg"
        role="tablist"
        aria-label="Export format"
        style={{ background: 'var(--color-surface-2)' }}
      >
        {formats.map((fmt) => {
          const isActive = selected === fmt
          return (
            <button
              key={fmt}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => setSelected(fmt)}
              className="flex-1 flex items-center justify-center gap-1 py-1.5 px-2 rounded-md text-xs font-medium transition-all"
              style={{
                background: isActive ? 'var(--color-surface)' : 'transparent',
                color: isActive ? 'var(--color-primary)' : 'var(--color-text-3)',
                border: isActive ? '1px solid var(--color-border)' : '1px solid transparent',
                cursor: 'pointer',
                boxShadow: isActive ? 'var(--shadow-sm)' : 'none',
              }}
            >
              {FORMAT_META[fmt].label}
              {fmt === 'srt' && (
                <span
                  className="text-xs px-1 py-0 rounded"
                  style={{
                    fontSize: '9px',
                    background: 'var(--color-primary-light)',
                    color: 'var(--color-primary)',
                    fontWeight: 600,
                    lineHeight: '14px',
                  }}
                >
                  REC
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Download button for selected format */}
      <a
        href={getDownloadUrl(taskId, selected)}
        download
        className="btn-download btn-interactive flex items-center gap-3 w-full px-4 py-2.5 rounded-lg border text-sm font-medium group"
        style={{ textDecoration: 'none' }}
      >
        <DownloadIcon />
        <div className="flex-1 flex flex-col">
          <span>Download {meta.label}</span>
          <span className="text-xs font-normal" style={{ opacity: 0.75, fontSize: '11px' }}>
            {meta.description}
          </span>
        </div>
        <div className="flex flex-col items-end gap-0.5">
          <span
            className="px-1.5 py-0.5 rounded text-xs font-semibold"
            style={{
              background: 'rgba(255,255,255,0.2)',
              color: 'white',
              fontSize: '11px',
              letterSpacing: '0.04em',
            }}
          >
            .{meta.ext}
          </span>
          {sizeStr && (
            <span className="text-xs" style={{ opacity: 0.6, fontSize: '10px' }}>
              {sizeStr}
            </span>
          )}
        </div>
      </a>

      {/* Preview link */}
      <button
        type="button"
        onClick={() => window.open(`/subtitles/${taskId}`, '_blank')}
        className="btn-interactive flex items-center justify-center gap-2 w-full px-3 py-2 rounded-lg text-xs font-medium"
        style={{
          background: 'transparent',
          border: '1px solid var(--color-border)',
          color: 'var(--color-text-2)',
          cursor: 'pointer',
        }}
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.5" fill="none" />
          <circle cx="7" cy="7" r="2" stroke="currentColor" strokeWidth="1.5" fill="none" />
        </svg>
        Preview Subtitles
      </button>
    </div>
  )
}
