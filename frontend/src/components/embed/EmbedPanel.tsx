import { useState } from 'react'
import { api } from '@/api/client'

interface Props {
  taskId: string
}

type EmbedState = 'idle' | 'processing' | 'done' | 'error'

export function EmbedPanel({ taskId }: Props) {
  const [embedState, setEmbedState] = useState<EmbedState>('idle')
  const [progress, setProgress] = useState(0)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const handleEmbed = async () => {
    setEmbedState('processing')
    setProgress(10)
    setErrorMsg(null)

    try {
      const fd = new FormData()
      fd.append('mode', 'soft')

      const timer = setInterval(() => {
        setProgress((prev) => Math.min(prev + 6, 90))
      }, 500)

      const result = await api.embedQuick(taskId, fd)
      clearInterval(timer)
      setProgress(100)
      setDownloadUrl(result.download_url ?? api.embedDownloadUrl(taskId))
      setEmbedState('done')
    } catch (err) {
      setEmbedState('error')
      setErrorMsg(err instanceof Error ? err.message : 'Embedding failed')
    }
  }

  if (embedState === 'done' && downloadUrl) {
    return (
      <div className="flex flex-col gap-3">
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium"
          style={{ background: 'var(--color-success-light)', color: 'var(--color-success)', border: '1px solid var(--color-success-border)' }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.4" fill="none" />
            <path d="M4 7l2 2 4-4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Subtitles embedded — ready to download
        </div>
        <a
          href={downloadUrl}
          download
          className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg text-sm font-semibold"
          style={{ background: 'var(--color-primary)', color: 'white', textDecoration: 'none' }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M7 2v7M3.5 6.5l3.5 3.5 3.5-3.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M2 11h10" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          Download Video with Subtitles
        </a>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-start gap-3">
        <div
          className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: 'var(--color-primary-light)' }}
        >
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
            <rect x="1" y="2" width="13" height="9" rx="1.5" stroke="var(--color-primary)" strokeWidth="1.3" fill="none"/>
            <path d="M5 14h5M7.5 11v3" stroke="var(--color-primary)" strokeWidth="1.3" strokeLinecap="round"/>
            <path d="M4 6.5h7M4 8.5h4" stroke="var(--color-primary)" strokeWidth="1.1" strokeLinecap="round"/>
          </svg>
        </div>
        <div>
          <p className="text-xs font-semibold" style={{ color: 'var(--color-text)' }}>Embed subtitles into your video</p>
          <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>Soft mux — subtitles selectable in VLC, YouTube, etc.</p>
        </div>
      </div>

      {embedState === 'processing' && (
        <div className="flex flex-col gap-1">
          <div className="h-1 rounded-full overflow-hidden" style={{ background: 'var(--color-border)' }}>
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${progress}%`, background: 'var(--color-primary)' }}
            />
          </div>
          <span className="text-xs" style={{ color: 'var(--color-text-3)' }}>Embedding… {progress}%</span>
        </div>
      )}

      {embedState === 'error' && errorMsg && (
        <div
          className="px-3 py-2 rounded-lg text-xs"
          style={{ background: 'var(--color-danger-light)', color: 'var(--color-danger)', border: '1px solid #FECACA' }}
        >
          {errorMsg}
        </div>
      )}

      <button
        type="button"
        onClick={handleEmbed}
        disabled={embedState === 'processing'}
        className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg text-sm font-semibold transition-all"
        style={{
          background: embedState === 'processing' ? 'var(--color-border)' : 'var(--color-primary)',
          color: embedState === 'processing' ? 'var(--color-text-3)' : 'white',
          border: 'none',
          cursor: embedState === 'processing' ? 'not-allowed' : 'pointer',
        }}
      >
        {embedState === 'processing' ? (
          <>
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" className="animate-spin" aria-hidden="true">
              <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" strokeWidth="1.5" strokeDasharray="20 10" fill="none" />
            </svg>
            Embedding…
          </>
        ) : (
          <>
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <rect x="1" y="1.5" width="12" height="8" rx="1.5" stroke="white" strokeWidth="1.3" fill="none"/>
              <path d="M4 12.5h6M7 9.5v3" stroke="white" strokeWidth="1.3" strokeLinecap="round"/>
              <path d="M3.5 6h7M3.5 7.5h4" stroke="white" strokeWidth="1.1" strokeLinecap="round"/>
            </svg>
            Embed &amp; Download
          </>
        )}
      </button>
    </div>
  )
}
