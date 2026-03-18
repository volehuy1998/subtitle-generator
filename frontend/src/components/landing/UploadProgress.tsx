/**
 * UploadProgress — Shows XHR upload progress with filename, bar, and spinner.
 *
 * — Pixel (Senior Frontend Engineer)
 */
import { ProgressBar } from '../ui/ProgressBar'
import { Spinner } from '../ui/Spinner'

interface UploadProgressProps {
  filename: string
  percent: number
}

export function UploadProgress({ filename, percent }: UploadProgressProps) {
  const displayName =
    filename.length > 40
      ? `${filename.slice(0, 20)}…${filename.slice(-18)}`
      : filename

  return (
    <div
      className="flex flex-col gap-3 w-full rounded-xl border border-[--color-border] bg-[--color-surface] p-5"
      role="status"
      aria-live="polite"
      aria-label={`Uploading ${filename}: ${Math.round(percent)}%`}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <Spinner size="sm" />
          <span className="text-sm font-medium text-[--color-text] truncate" title={filename}>
            {displayName}
          </span>
        </div>
        <span className="text-sm font-semibold text-[--color-primary] shrink-0">
          {Math.round(percent)}%
        </span>
      </div>

      <ProgressBar value={percent} />

      <p className="text-xs text-[--color-text-muted]">Uploading...</p>
    </div>
  )
}
