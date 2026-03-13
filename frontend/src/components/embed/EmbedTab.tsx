import { useState, useEffect, useRef } from 'react'
import { api } from '@/api/client'
import { ModeSelector } from './ModeSelector'
import { StyleOptions } from './StyleOptions'
import { useUIStore } from '@/store/uiStore'
import type { EmbedMode } from '@/store/uiStore'
import type { TranslationPair } from '@/api/types'

type EmbedState = 'idle' | 'processing' | 'done' | 'error'

function FilePicker({
  label,
  accept,
  filename,
  onFile,
}: {
  label: string
  accept: string
  filename: string | null
  onFile: (f: File) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)

  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs font-medium" style={{ color: 'var(--color-text-2)' }}>
        {label}
      </span>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg border-2 border-dashed text-sm transition-all text-left"
        style={{
          background: filename ? 'var(--color-surface-2)' : 'var(--color-surface)',
          borderColor: filename ? 'var(--color-border-2)' : 'var(--color-border)',
          color: filename ? 'var(--color-text)' : 'var(--color-text-3)',
          cursor: 'pointer',
        }}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path
            d="M9 2H4a1.5 1.5 0 00-1.5 1.5v9A1.5 1.5 0 004 14h8a1.5 1.5 0 001.5-1.5V7L9 2z"
            stroke="currentColor"
            strokeWidth="1.2"
            fill="none"
          />
          <path d="M9 2v5h5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span className="truncate">
          {filename ?? `Choose ${label.toLowerCase()}…`}
        </span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) onFile(f)
        }}
      />
    </div>
  )
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

  const canEmbed = videoFile !== null && subtitleFile !== null && embedState !== 'processing'

  const handleEmbed = async () => {
    if (!videoFile || !subtitleFile) return

    setEmbedState('processing')
    setProgress(5)
    setErrorMsg(null)

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

      // Poll for completion
      const poll = async () => {
        const status = await api.combineStatus(task_id)
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

        setTimeout(poll, 1000)
      }

      await poll()
    } catch (err) {
      setEmbedState('error')
      setErrorMsg(err instanceof Error ? err.message : 'Embedding failed')
    }
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
        className="flex flex-col items-center justify-center gap-3 rounded-xl p-10 text-center"
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
    <div className="flex flex-col gap-5">
      {/* File pickers */}
      <FilePicker
        label="Video file"
        accept="video/*"
        filename={videoFile?.name ?? null}
        onFile={setVideoFile}
      />
      <FilePicker
        label="Subtitle file"
        accept=".srt,.vtt"
        filename={subtitleFile?.name ?? null}
        onFile={setSubtitleFile}
      />

      {/* Mode selector */}
      <div className="flex flex-col gap-2">
        <span
          className="text-xs font-semibold tracking-wider"
          style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
        >
          EMBED MODE
        </span>
        <ModeSelector value={mode} onChange={setMode} />
      </div>

      {/* Style options */}
      {mode === 'hard' && (
        <StyleOptions
          color={color}
          size={size}
          onChange={(c, s) => { setColor(c); setSize(s) }}
        />
      )}

      {/* Translate subtitles */}
      <div className="flex flex-col gap-2">
        <span
          className="text-xs font-semibold tracking-wider"
          style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
        >
          TRANSLATE SUBTITLES
        </span>
        <select
          value={translateTo}
          onChange={(e) => setTranslateTo(e.target.value)}
          className="w-full px-3 py-2 rounded-lg text-sm border appearance-none"
          style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            color: 'var(--color-text)',
            outline: 'none',
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

      {/* Error */}
      {embedState === 'error' && errorMsg && (
        <div
          className="px-3 py-2 rounded-lg text-xs"
          style={{
            background: 'var(--color-danger-light)',
            color: 'var(--color-danger)',
            border: '1px solid #FECACA',
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* Progress */}
      {embedState === 'processing' && (
        <div className="flex flex-col gap-1.5">
          <div
            className="h-1.5 rounded-full overflow-hidden"
            style={{ background: 'var(--color-border)' }}
          >
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${progress}%`, background: 'var(--color-primary)' }}
            />
          </div>
          <span className="text-xs" style={{ color: 'var(--color-text-3)' }}>
            Embedding… {progress}%
            {combineTaskId && (
              <span style={{ color: 'var(--color-text-3)' }}> · task {combineTaskId.slice(0, 8)}</span>
            )}
          </span>
        </div>
      )}

      {/* Result */}
      {embedState === 'done' && downloadUrl && (
        <div className="flex flex-col gap-3">
          <div
            className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg"
            style={{
              background: 'var(--color-success-light)',
              border: '1px solid var(--color-success-border)',
            }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <circle cx="8" cy="8" r="7" stroke="var(--color-success)" strokeWidth="1.5" fill="none" />
              <path d="M4.5 8l2.5 2.5 4.5-4.5" stroke="var(--color-success)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="text-xs font-medium" style={{ color: 'var(--color-success)' }}>
              Embedding complete
            </span>
          </div>

          <a
            href={downloadUrl}
            download
            className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg text-sm font-medium"
            style={{
              background: 'var(--color-success)',
              color: 'white',
              textDecoration: 'none',
            }}
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
            className="text-xs text-center py-1"
            style={{ color: 'var(--color-text-3)', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            Start over
          </button>
        </div>
      )}

      {/* Embed button */}
      {embedState !== 'done' && (
        <button
          type="button"
          onClick={handleEmbed}
          disabled={!canEmbed}
          className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg text-sm font-medium transition-all"
          style={{
            background: !canEmbed ? 'var(--color-border)' : 'var(--color-success)',
            color: !canEmbed ? 'var(--color-text-3)' : 'white',
            border: 'none',
            cursor: !canEmbed ? 'not-allowed' : 'pointer',
          }}
        >
          {embedState === 'processing' ? (
            <>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"
                className="animate-spin">
                <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" strokeDasharray="20 10" fill="none" />
              </svg>
              Embedding…
            </>
          ) : (
            'Embed & Download'
          )}
        </button>
      )}
    </div>
  )
}
