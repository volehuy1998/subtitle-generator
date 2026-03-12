import { useState } from 'react'
import { api } from '@/api/client'
import { ModeSelector } from './ModeSelector'
import { StyleOptions } from './StyleOptions'
import type { EmbedMode } from '@/store/uiStore'

interface Props {
  taskId: string
}

type EmbedState = 'idle' | 'processing' | 'done' | 'error'

export function EmbedPanel({ taskId }: Props) {
  const [mode, setMode] = useState<EmbedMode>('soft')
  const [color, setColor] = useState('#FFFFFF')
  const [size, setSize] = useState(24)
  const [embedState, setEmbedState] = useState<EmbedState>('idle')
  const [progress, setProgress] = useState(0)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const handleStyleChange = (newColor: string, newSize: number) => {
    setColor(newColor)
    setSize(newSize)
  }

  const handleEmbed = async () => {
    setEmbedState('processing')
    setProgress(10)
    setErrorMsg(null)

    try {
      const fd = new FormData()
      fd.append('mode', mode)
      if (mode === 'hard') {
        fd.append('font_color', color.replace('#', ''))
        fd.append('font_size', String(size))
      }

      // Simulate progress while waiting
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 5, 90))
      }, 500)

      const result = await api.embedQuick(taskId, fd)

      clearInterval(progressInterval)
      setProgress(100)

      if (result.download_url) {
        setDownloadUrl(result.download_url)
      } else {
        setDownloadUrl(api.embedDownloadUrl(taskId))
      }
      setEmbedState('done')
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
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h3
          className="text-sm font-semibold"
          style={{ color: 'var(--color-text)' }}
        >
          Embed Subtitles into Video
        </h3>
        <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>
          Mux the generated subtitles back into your video file
        </p>
      </div>

      {embedState === 'done' ? (
        /* Result block */
        <div className="flex flex-col gap-3">
          <div
            className="flex items-center gap-2.5 px-3 py-3 rounded-lg"
            style={{
              background: 'var(--color-success-light)',
              border: '1px solid var(--color-success-border)',
            }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <circle cx="8" cy="8" r="7" stroke="var(--color-success)" strokeWidth="1.5" fill="none" />
              <path d="M4.5 8l2.5 2.5 4.5-4.5"
                stroke="var(--color-success)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="text-xs font-medium" style={{ color: 'var(--color-success)' }}>
              Embedding complete
            </span>
          </div>

          {downloadUrl && (
            <a
              href={downloadUrl}
              download
              className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg text-sm font-medium transition-all"
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
          )}

          <button
            type="button"
            onClick={handleReset}
            className="text-xs text-center py-1 transition-colors"
            style={{ color: 'var(--color-text-3)', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            Embed again with different settings
          </button>
        </div>
      ) : (
        <>
          {/* Mode selector */}
          <ModeSelector value={mode} onChange={setMode} />

          {/* Style options (hard burn only) */}
          {mode === 'hard' && (
            <StyleOptions color={color} size={size} onChange={handleStyleChange} />
          )}

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

          {/* Progress bar (during processing) */}
          {embedState === 'processing' && (
            <div className="flex flex-col gap-1.5">
              <div
                className="h-1 rounded-full overflow-hidden"
                style={{ background: 'var(--color-border)' }}
              >
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${progress}%`,
                    background: 'var(--color-primary)',
                  }}
                />
              </div>
              <span className="text-xs" style={{ color: 'var(--color-text-3)' }}>
                Embedding… {progress}%
              </span>
            </div>
          )}

          {/* Embed button */}
          <button
            type="button"
            onClick={handleEmbed}
            disabled={embedState === 'processing'}
            className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg text-sm font-medium transition-all"
            style={{
              background: embedState === 'processing' ? 'var(--color-border)' : 'var(--color-success)',
              color: embedState === 'processing' ? 'var(--color-text-3)' : 'white',
              border: 'none',
              cursor: embedState === 'processing' ? 'not-allowed' : 'pointer',
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
              <>
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="M7 2v7M3.5 6.5l3.5 3.5 3.5-3.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M2 11h10" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
                Embed &amp; Download
              </>
            )}
          </button>
        </>
      )}
    </div>
  )
}
