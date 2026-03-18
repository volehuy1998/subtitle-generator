/**
 * UploadZone — Adaptive drag-and-drop upload entry point.
 * Detects file combination type and routes to the correct workflow.
 *
 * — Pixel (Senior Frontend Engineer)
 */
import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { UploadCloud } from 'lucide-react'
import { cn } from '../ui/cn'
import { detectUploadType } from '../../types'

const ALLOWED_EXTENSIONS = [
  '.mp4', '.mkv', '.mov', '.wav', '.mp3', '.ogg', '.m4a', '.webm', '.srt', '.vtt'
]

const MIN_SIZE = 1024                        // 1 KB
const MAX_SIZE = 2 * 1024 * 1024 * 1024     // 2 GB

interface UploadZoneProps {
  onUpload: (files: File | File[], type: 'transcribe' | 'combine' | 'edit-srt') => void
  onError?: (message: string) => void
  disabled?: boolean
}

export function UploadZone({ onUpload, onError, disabled = false }: UploadZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return

      // Client-side validation: extension allowlist + size bounds
      for (const file of acceptedFiles) {
        const name = file.name.toLowerCase()
        const hasAllowedExt = ALLOWED_EXTENSIONS.some(ext => name.endsWith(ext))
        if (!hasAllowedExt) {
          onError?.(`Unsupported file type: ${file.name}`)
          return
        }
        if (file.size < MIN_SIZE || file.size > MAX_SIZE) {
          onError?.(`File size out of range: ${file.name}`)
          return
        }
      }

      const uploadType = detectUploadType(acceptedFiles)

      if (uploadType === 'unknown') {
        onError?.('Unsupported file type')
        return
      }

      if (uploadType === 'combine') {
        onUpload(acceptedFiles, 'combine')
      } else if (uploadType === 'transcribe') {
        onUpload(acceptedFiles[0], 'transcribe')
      } else {
        // edit-srt
        onUpload(acceptedFiles[0], 'edit-srt')
      }
    },
    [onUpload, onError]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled,
    multiple: true,
  })

  return (
    <div
      {...getRootProps()}
      className={cn(
        'flex flex-col items-center justify-center gap-4',
        'w-full rounded-xl border-2 border-dashed',
        'px-8 py-12 cursor-pointer transition-colors',
        'bg-[--color-surface] border-[--color-border]',
        'hover:border-[--color-primary] hover:bg-[--color-primary-light]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[--color-primary]',
        isDragActive && 'upload-zone-active border-[--color-primary] bg-[--color-primary-light]',
        disabled && 'opacity-50 cursor-not-allowed pointer-events-none'
      )}
      role="button"
      aria-label="Upload file — click or drag and drop"
    >
      <input {...getInputProps()} />

      <UploadCloud
        className={cn(
          'h-10 w-10 transition-colors',
          isDragActive ? 'text-[--color-primary]' : 'text-[--color-text-muted]'
        )}
        aria-hidden="true"
      />

      <div className="text-center space-y-1">
        <p className="text-base font-semibold text-[--color-text]">
          Drop your file here
        </p>
        <p className="text-sm text-[--color-text-secondary]">
          or click to browse
        </p>
      </div>

      <div className="text-center space-y-1">
        <p className="text-xs text-[--color-text-muted]">
          MP4, MKV, MOV, WAV, MP3, OGG, M4A, WEBM, SRT, VTT
        </p>
        <p className="text-xs text-[--color-text-muted]">
          Up to 2GB
        </p>
      </div>
    </div>
  )
}
