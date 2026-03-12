import { api } from '@/api/client'

interface Props {
  taskId: string
  format?: 'srt' | 'vtt'
}

interface DownloadButtonProps {
  href: string
  ext: string
  label: string
}

function DownloadButton({ href, ext, label }: DownloadButtonProps) {
  return (
    <a
      href={href}
      download
      className="flex items-center gap-3 w-full px-4 py-3 rounded-lg border text-sm font-medium transition-all group"
      style={{
        background: 'var(--color-surface)',
        borderColor: 'var(--color-border)',
        color: 'var(--color-text)',
        textDecoration: 'none',
      }}
      onMouseEnter={(e) => {
        const el = e.currentTarget
        el.style.borderColor = 'var(--color-primary)'
        el.style.background = 'var(--color-primary-light)'
      }}
      onMouseLeave={(e) => {
        const el = e.currentTarget
        el.style.borderColor = 'var(--color-border)'
        el.style.background = 'var(--color-surface)'
      }}
    >
      {/* Arrow down icon */}
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path
          d="M8 3v8M4 8l4 4 4-4"
          stroke="var(--color-primary)"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>

      <span className="flex-1">{label}</span>

      {/* Extension badge */}
      <span
        className="px-1.5 py-0.5 rounded text-xs font-semibold"
        style={{
          background: 'var(--color-primary-light)',
          color: 'var(--color-primary)',
          fontSize: '11px',
          letterSpacing: '0.04em',
        }}
      >
        .{ext}
      </span>
    </a>
  )
}

export function DownloadButtons({ taskId, format }: Props) {
  if (format === 'srt') {
    return (
      <DownloadButton
        href={api.downloadUrl(taskId, 'srt')}
        ext="srt"
        label="Download SRT"
      />
    )
  }
  if (format === 'vtt') {
    return (
      <DownloadButton
        href={api.downloadUrl(taskId, 'vtt')}
        ext="vtt"
        label="Download VTT"
      />
    )
  }
  // Show both if no format specified
  return (
    <div className="flex flex-col gap-2">
      <DownloadButton
        href={api.downloadUrl(taskId, 'srt')}
        ext="srt"
        label="Download SRT"
      />
      <DownloadButton
        href={api.downloadUrl(taskId, 'vtt')}
        ext="vtt"
        label="Download VTT"
      />
    </div>
  )
}
