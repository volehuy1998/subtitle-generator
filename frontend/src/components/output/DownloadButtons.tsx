import { api } from '@/api/client'

interface Props {
  taskId: string
  format?: 'srt' | 'vtt'
  segments?: number
}

interface DownloadButtonProps {
  href: string
  ext: string
  label: string
  description: string
  estimatedSize: string
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

function DownloadButton({ href, ext, label, description, estimatedSize }: DownloadButtonProps) {
  return (
    <a
      href={href}
      download
      className="btn-download btn-interactive flex items-center gap-3 w-full px-4 py-2.5 rounded-lg border text-sm font-medium group"
      style={{ textDecoration: 'none' }}
    >
      <DownloadIcon />

      <div className="flex-1 flex flex-col">
        <span>{label}</span>
        <span
          className="text-xs font-normal"
          style={{ opacity: 0.75, fontSize: '11px' }}
        >
          {description}
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
          .{ext}
        </span>
        <span
          className="text-xs"
          style={{ opacity: 0.6, fontSize: '10px' }}
        >
          {estimatedSize}
        </span>
      </div>
    </a>
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

export function DownloadButtons({ taskId, format, segments = 0 }: Props) {
  if (format === 'srt') {
    return (
      <DownloadButton
        href={api.downloadUrl(taskId, 'srt')}
        ext="srt"
        label="Download SRT"
        description="SubRip Text"
        estimatedSize={estimateSize(segments, 'srt')}
      />
    )
  }
  if (format === 'vtt') {
    return (
      <DownloadButton
        href={api.downloadUrl(taskId, 'vtt')}
        ext="vtt"
        label="Download VTT"
        description="Web Video Text Tracks"
        estimatedSize={estimateSize(segments, 'vtt')}
      />
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {/* Section header */}
      <h4
        className="text-xs font-semibold tracking-wider"
        style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
      >
        DOWNLOADS
      </h4>

      <DownloadButton
        href={api.downloadUrl(taskId, 'srt')}
        ext="srt"
        label="Download SRT"
        description="SubRip Text — universal format"
        estimatedSize={estimateSize(segments, 'srt')}
      />
      <DownloadButton
        href={api.downloadUrl(taskId, 'vtt')}
        ext="vtt"
        label="Download VTT"
        description="Web Video Text Tracks"
        estimatedSize={estimateSize(segments, 'vtt')}
      />
      <DownloadButton
        href={api.downloadUrl(taskId, 'json')}
        ext="json"
        label="Download JSON"
        description="Structured data with timestamps"
        estimatedSize={estimateSize(segments, 'json')}
      />

      {/* Download All (ZIP) */}
      <a
        href={api.downloadAllUrl(taskId)}
        download
        className="btn-interactive flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg border text-sm font-medium"
        style={{
          textDecoration: 'none',
          background: 'var(--color-surface-2)',
          borderColor: 'var(--color-border)',
          color: 'var(--color-text)',
        }}
      >
        {/* Archive icon */}
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <rect x="2" y="3" width="12" height="11" rx="1.5" stroke="currentColor" strokeWidth="1.5" fill="none" />
          <path d="M6 3v11M10 3v11" stroke="currentColor" strokeWidth="1" strokeDasharray="2 2" />
          <path d="M5 7h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        Download All (ZIP)
        {segments > 0 && (
          <span
            className="text-xs"
            style={{ opacity: 0.6, fontSize: '10px' }}
          >
            {estimateSize(segments, 'zip')}
          </span>
        )}
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
