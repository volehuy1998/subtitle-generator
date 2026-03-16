/**
 * Phase Lumen — Embed Tab redesign.
 *
 * Upload video + subtitle file, choose embed mode, confirm settings,
 * then embed subtitles. Follows Lumen design language with confirmation
 * step before any action starts.
 *
 * — Prism (UI/UX Engineer) — Sprint L8
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '@/api/client'
import { ModeSelector } from './ModeSelector'
import { StyleOptions } from './StyleOptions'
import { EmbedConfirmationDialog } from './EmbedConfirmationDialog'
import { useUIStore } from '@/store/uiStore'
import type { EmbedMode } from '@/store/uiStore'
import type { TranslationPair } from '@/api/types'

type EmbedState = 'idle' | 'confirming' | 'processing' | 'done' | 'error'

/** Shared file picker with Lumen styling — Prism (UI/UX Engineer) */
function FilePicker({
  label,
  accept,
  filename,
  onFile,
  ariaLabel,
  icon,
}: {
  label: string
  accept: string
  filename: string | null
  onFile: (f: File) => void
  ariaLabel: string
  icon: React.ReactNode
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const inputId = `file-picker-${label.toLowerCase().replace(/\s+/g, '-')}`

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-xs font-medium" style={{ color: 'var(--color-text-2)' }}>
        {label}
      </label>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        aria-label={ariaLabel}
        className="flex items-center gap-3 w-full px-4 py-3 rounded-lg border-2 border-dashed text-sm transition-all text-left"
        style={{
          background: filename ? 'var(--color-primary-light)' : 'var(--color-surface)',
          borderColor: filename ? 'var(--color-primary-border)' : 'var(--color-border)',
          color: filename ? 'var(--color-text)' : 'var(--color-text-3)',
          cursor: 'pointer',
        }}
      >
        {icon}
        <span className="truncate flex-1">
          {filename ?? `Choose ${label.toLowerCase()}...`}
        </span>
        {filename && (
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <circle cx="7" cy="7" r="6" stroke="var(--color-success)" strokeWidth="1.4" fill="none" />
            <path d="M4 7l2 2 4-4" stroke="var(--color-success)" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </button>
      <input
        ref={inputRef}
        id={inputId}
        type="file"
        accept={accept}
        aria-label={ariaLabel}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) onFile(f)
        }}
      />
    </div>
  )
}

/** Video file icon */
const VideoIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
    <rect x="2" y="3" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.3" fill="none" />
    <path d="M7 6.5l4 2.5-4 2.5V6.5z" fill="currentColor" opacity="0.6" />
    <path d="M6 16h6M9 13v3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
  </svg>
)

/** Subtitle file icon */
const SubtitleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
    <rect x="2" y="2" width="14" height="14" rx="2" stroke="currentColor" strokeWidth="1.3" fill="none" />
    <path d="M5 10h8M5 13h5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    <path d="M5 7h3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" opacity="0.5" />
  </svg>
)

const STYLE_PRESET_LABELS: Record<string, string> = {
  default: 'Default',
  youtube_white: 'YouTube White',
  youtube_yellow: 'YouTube Yellow',
  cinema: 'Cinema',
  large_bold: 'Large Bold',
  top: 'Top Position',
}

export function EmbedTab() {
  const { dbOk } = useUIStore()
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [subtitleFile, setSubtitleFile] = useState<File | null>(null)
  const [mode, setMode] = useState<EmbedMode>('soft')
  const [color, setColor] = useState('#FFFFFF')
  const [size, setSize] = useState(24)
  const [embedState, setEmbedState] = useState<EmbedState>('idle')
  const [progress, setProgress] = useState(0)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [combineTaskId, setCombineTaskId] = useState<string | null>(null)
  const [translateTo, setTranslateTo] = useState<string>('')
  const [translationTargets, setTranslationTargets] = useState<TranslationPair[]>([])

  useEffect(() => {
    api.translationLanguages()
      .then((res) => setTranslationTargets(res.pairs))
      .catch(() => {})
  }, [])

  // Cleanup ref for polling — prevents state updates after unmount
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current)
    }
  }, [])

  const canEmbed = videoFile !== null && subtitleFile !== null && embedState !== 'processing' && embedState !== 'confirming'

  /** Show confirmation dialog before starting — Prism (UI/UX Engineer) */
  const handleEmbedClick = () => {
    if (!videoFile || !subtitleFile) return
    setEmbedState('confirming')
  }

  const handleConfirm = useCallback(async () => {
    if (!videoFile || !subtitleFile) return

    setEmbedState('processing')
    setProgress(5)
    setErrorMsg(null)

    let cancelled = false

    try {
      const fd = new FormData()
      fd.append('video', videoFile)
      fd.append('subtitle', subtitleFile)
      fd.append('mode', mode)
      if (mode === 'hard') {
        fd.append('font_color', color.replace('#', ''))
        fd.append('font_size', String(size))
      }
      if (translateTo) {
        fd.append('translate_to', translateTo)
      }

      const { task_id } = await api.combineStart(fd)
      setCombineTaskId(task_id)

      // Poll for completion with cleanup support
      const poll = async () => {
        if (cancelled) return
        const status = await api.combineStatus(task_id)
        if (cancelled) return

        setProgress(status.percent)

        if (status.status === 'done') {
          setDownloadUrl(api.combineDownloadUrl(task_id))
          setEmbedState('done')
          return
        }
        if (status.status === 'error') {
          throw new Error(status.message ?? 'Combine failed')
        }
        if (status.status === 'cancelled') {
          throw new Error('Cancelled')
        }

        pollTimerRef.current = setTimeout(poll, 1000)
      }

      await poll()
    } catch (err) {
      if (!cancelled) {
        setEmbedState('error')
        setErrorMsg(err instanceof Error ? err.message : 'Embedding failed')
      }
    }

    return () => { cancelled = true }
  }, [videoFile, subtitleFile, mode, color, size, translateTo])

  const handleCancelConfirm = () => {
    setEmbedState('idle')
  }

  const handleReset = () => {
    setEmbedState('idle')
    setProgress(0)
    setDownloadUrl(null)
    setErrorMsg(null)
    setCombineTaskId(null)
  }

  if (!dbOk) {
    return (
      <div
        className="flex flex-col items-center justify-center gap-3 rounded-xl p-10 text-center animate-fade-in"
        style={{ background: 'var(--color-danger-light)', border: '1px solid var(--color-danger)' }}
      >
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
          <circle cx="16" cy="16" r="14" stroke="var(--color-danger)" strokeWidth="2" />
          <path d="M16 9v8M16 21v2" stroke="var(--color-danger)" strokeWidth="2" strokeLinecap="round" />
        </svg>
        <p className="text-sm font-semibold" style={{ color: 'var(--color-danger)' }}>
          Database unavailable
        </p>
        <p className="text-xs" style={{ color: 'var(--color-text-2)' }}>
          This feature is disabled until the database connection is restored.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Header — Prism (UI/UX Engineer) */}
      <div className="flex items-start gap-3">
        <div
          className="flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center"
          style={{ background: 'var(--color-primary-light)' }}
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <rect x="2" y="3" width="14" height="10" rx="2" stroke="var(--color-primary)" strokeWidth="1.3" fill="none" />
            <path d="M5 16h8M9 13v3" stroke="var(--color-primary)" strokeWidth="1.3" strokeLinecap="round" />
            <path d="M5 8h8M5 10.5h5" stroke="var(--color-primary)" strokeWidth="1.1" strokeLinecap="round" />
          </svg>
        </div>
        <div>
          <h3
            className="text-sm font-semibold"
            style={{ color: 'var(--color-text)', margin: 0 }}
          >
            Embed Subtitles
          </h3>
          <p
            className="text-xs mt-0.5"
            style={{ color: 'var(--color-text-3)', margin: 0 }}
          >
            Upload a video and subtitle file to combine them
          </p>
        </div>
      </div>

      {/* File pickers section */}
      <div
        className="flex flex-col gap-4 p-4 rounded-lg"
        style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
        }}
      >
        <span
          className="text-xs font-semibold tracking-wider"
          style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
        >
          SOURCE FILES
        </span>
        <FilePicker
          label="Video file"
          accept="video/*"
          filename={videoFile?.name ?? null}
          onFile={setVideoFile}
          ariaLabel="Select video file"
          icon={<VideoIcon />}
        />
        <FilePicker
          label="Subtitle file"
          accept=".srt,.vtt"
          filename={subtitleFile?.name ?? null}
          onFile={setSubtitleFile}
          ariaLabel="Select subtitle file"
          icon={<SubtitleIcon />}
        />
      </div>

      {/* Mode selector section */}
      <div
        className="flex flex-col gap-3 p-4 rounded-lg"
        style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
        }}
      >
        <span
          className="text-xs font-semibold tracking-wider"
          style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
        >
          EMBED MODE
        </span>
        <ModeSelector value={mode} onChange={setMode} />
      </div>

      {/* Style options for hard burn */}
      {mode === 'hard' && (
        <div
          className="flex flex-col gap-3 p-4 rounded-lg animate-fade-in"
          style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
          }}
        >
          <span
            className="text-xs font-semibold tracking-wider"
            style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
          >
            SUBTITLE STYLE
          </span>
          <StyleOptions
            color={color}
            size={size}
            onChange={(c, s) => { setColor(c); setSize(s) }}
          />
        </div>
      )}

      {/* Translation section */}
      <div
        className="flex flex-col gap-3 p-4 rounded-lg"
        style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
        }}
      >
        <span
          className="text-xs font-semibold tracking-wider"
          style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
        >
          TRANSLATE SUBTITLES
        </span>
        <select
          value={translateTo}
          onChange={(e) => setTranslateTo(e.target.value)}
          aria-label="Select translation language"
          className="w-full px-3 py-2.5 rounded-lg text-sm appearance-none"
          style={{
            background: 'var(--color-bg)',
            border: '1px solid var(--color-border)',
            color: 'var(--color-text)',
          }}
        >
          <option value="">No translation</option>
          {[...new Map(translationTargets.map(p => [p.target, p])).values()].map((pair) => (
            <option key={pair.target} value={pair.target}>
              {pair.target_name}{pair.method === 'whisper_translate' ? ' (Whisper)' : ''}
            </option>
          ))}
        </select>
      </div>

      {/* Error message */}
      {embedState === 'error' && errorMsg && (
        <div
          className="flex items-center gap-2.5 px-4 py-3 rounded-lg text-xs animate-fade-in"
          role="alert"
          style={{
            background: 'var(--color-danger-light)',
            color: 'var(--color-danger)',
            border: '1px solid var(--color-danger-border)',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.4" fill="none" />
            <path d="M7 4v4M7 10v1" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
          </svg>
          {errorMsg}
        </div>
      )}

      {/* Progress bar */}
      {embedState === 'processing' && (
        <div className="flex flex-col gap-2 animate-fade-in">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium" style={{ color: 'var(--color-text-2)' }}>
              Embedding subtitles...
            </span>
            <span className="text-xs font-mono" style={{ color: 'var(--color-primary)' }}>
              {progress}%
            </span>
          </div>
          <div
            className="h-2 rounded-full overflow-hidden"
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Embedding progress"
            style={{ background: 'var(--color-surface-2)' }}
          >
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${progress}%`,
                background: 'var(--color-primary)',
              }}
            />
          </div>
          {combineTaskId && (
            <span className="text-xs font-mono" style={{ color: 'var(--color-text-3)' }}>
              Task {combineTaskId.slice(0, 8)}
            </span>
          )}
        </div>
      )}

      {/* Success result — Prism (UI/UX Engineer) */}
      {embedState === 'done' && downloadUrl && (
        <div className="flex flex-col gap-3 animate-success-fade-in" role="status">
          <div
            className="flex items-center gap-2.5 px-4 py-3 rounded-lg"
            style={{
              background: 'var(--color-success-light)',
              border: '1px solid var(--color-success-border)',
            }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <circle cx="8" cy="8" r="7" stroke="var(--color-success)" strokeWidth="1.5" fill="none" />
              <path d="M4.5 8l2.5 2.5 4.5-4.5" stroke="var(--color-success)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="text-sm font-medium" style={{ color: 'var(--color-success)' }}>
              Embedding complete
            </span>
          </div>

          <a
            href={downloadUrl}
            download
            className="btn-download btn-interactive flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg text-sm font-semibold"
            style={{ textDecoration: 'none' }}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M7 2v7M3.5 6.5l3.5 3.5 3.5-3.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 11h10" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            Download Video
          </a>

          <button
            type="button"
            onClick={handleReset}
            className="btn-process-next text-xs text-center py-2 rounded-lg"
            style={{
              color: 'var(--color-text-3)',
              background: 'none',
              border: '1px solid var(--color-border)',
              cursor: 'pointer',
            }}
          >
            Embed another file
          </button>
        </div>
      )}

      {/* Embed action button */}
      {embedState !== 'done' && embedState !== 'confirming' && (
        <button
          type="button"
          onClick={handleEmbedClick}
          disabled={!canEmbed}
          className="btn-interactive flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg text-sm font-semibold transition-all"
          style={{
            background: !canEmbed ? 'var(--color-surface-2)' : 'var(--color-primary)',
            color: !canEmbed ? 'var(--color-text-3)' : 'white',
            border: !canEmbed ? '1px solid var(--color-border)' : 'none',
            cursor: !canEmbed ? 'not-allowed' : 'pointer',
            boxShadow: canEmbed ? 'var(--shadow-sm)' : 'none',
          }}
        >
          {embedState === 'processing' ? (
            <>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"
                className="animate-spin">
                <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" strokeDasharray="20 10" fill="none" />
              </svg>
              Embedding...
            </>
          ) : (
            <>
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
                <rect x="1.5" y="2" width="12" height="8.5" rx="1.5" stroke="currentColor" strokeWidth="1.2" fill="none" />
                <path d="M5 13.5h5M7.5 10.5v3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                <path d="M4.5 6.5h6M4.5 8.5h3.5" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
              </svg>
              Embed Subtitles
            </>
          )}
        </button>
      )}

      {/* Confirmation dialog — Prism (UI/UX Engineer) */}
      {embedState === 'confirming' && videoFile && subtitleFile && (
        <EmbedConfirmationDialog
          videoFile={videoFile}
          subtitleFile={subtitleFile}
          mode={mode}
          color={mode === 'hard' ? color : undefined}
          fontSize={mode === 'hard' ? size : undefined}
          translateTo={translateTo || undefined}
          onConfirm={handleConfirm}
          onCancel={handleCancelConfirm}
        />
      )}
    </div>
  )
}
