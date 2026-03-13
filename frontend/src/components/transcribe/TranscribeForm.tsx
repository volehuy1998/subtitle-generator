import { useState, useEffect, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { api } from '@/api/client'
import { useUIStore } from '@/store/uiStore'
import type { SystemInfo, TranslationPair } from '@/api/types'

export interface UploadOptions {
  device: string
  model: string
  language: string
  format: string
  translateTo: string
}

interface Props {
  onUpload: (file: File, opts: UploadOptions) => void
}

const MODELS = ['tiny', 'base', 'small', 'medium', 'large'] as const

const MODEL_INFO: Record<string, { speed: string; accuracy: string; vram: string; bestFor: string; pro: string; con: string }> = {
  tiny:   { speed: '⚡⚡⚡⚡', accuracy: '★☆☆☆☆', vram: '0.5 GB', bestFor: 'Quick drafts',    pro: 'Fastest, minimal RAM',      con: 'Many errors, misses words' },
  base:   { speed: '⚡⚡⚡',  accuracy: '★★☆☆☆', vram: '0.8 GB', bestFor: 'Short clips',      pro: 'Fast, CPU-friendly',        con: 'Struggles with accents'    },
  small:  { speed: '⚡⚡',   accuracy: '★★★☆☆', vram: '1.5 GB', bestFor: 'General use',       pro: 'Good balance of speed/quality', con: 'Moderate GPU VRAM needed' },
  medium: { speed: '⚡',     accuracy: '★★★★☆', vram: '3.0 GB', bestFor: 'Long recordings',   pro: 'High accuracy, multilingual',   con: 'Slow on CPU'              },
  large:  { speed: '·',      accuracy: '★★★★★', vram: '5.5 GB', bestFor: 'Final output',      pro: 'Best accuracy, all languages',  con: 'Needs GPU; very slow on CPU' },
}

const FORMAT_OPTIONS = [
  { value: 'srt', label: 'SRT' },
  { value: 'vtt', label: 'VTT' },
]

function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded ${className ?? ''}`}
      style={{ background: 'var(--color-surface-2)' }}
    />
  )
}

export function TranscribeForm({ onUpload }: Props) {
  const { dbOk } = useUIStore()
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null)
  const [languages, setLanguages] = useState<Record<string, string>>({})
  const [translationTargets, setTranslationTargets] = useState<TranslationPair[]>([])
  const [loading, setLoading] = useState(true)

  const [device, setDevice] = useState<string>('cpu')
  const [model, setModel] = useState<string>('base')
  const [language, setLanguage] = useState<string>('auto')
  const [format, setFormat] = useState<string>('srt')
  const [translateTo, setTranslateTo] = useState<string>('')

  useEffect(() => {
    Promise.all([api.systemInfo(), api.languages(), api.translationLanguages()])
      .then(([info, langs, transLangs]) => {
        setSystemInfo(info)
        setLanguages(langs.languages)
        setTranslationTargets(transLangs.pairs)
        setDevice(info.cuda_available ? 'cuda' : 'cpu')
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const onDrop = useCallback((accepted: File[]) => {
    const file = accepted[0]
    if (!file) return
    onUpload(file, { device, model, language, format, translateTo })
  }, [onUpload, device, model, language, format, translateTo])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/*': [], 'audio/*': [] },
    multiple: false,
    maxSize: 500 * 1024 * 1024,
  })

  const modelFitsGpu = (m: string) => {
    const rec = systemInfo?.model_recommendations?.[m]
    return rec === 'ok' || rec === 'tight' ? true : rec === 'too_large' ? false : null
  }

  const chipBase = 'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer select-none'

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
          Uploads are disabled until the database connection is restored.
          No new transcription tasks can be started.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-5">
      {/* Device selector */}
      <div className="flex flex-col gap-2">
        <label
          className="text-xs font-semibold tracking-wider"
          style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
        >
          DEVICE
        </label>
        {loading ? (
          <div className="flex gap-2">
            <Skeleton className="h-7 w-16" />
            <Skeleton className="h-7 w-14" />
          </div>
        ) : (
          <div className="flex gap-2">
            {systemInfo?.cuda_available && (
              <button
                type="button"
                onClick={() => setDevice('cuda')}
                className={chipBase}
                style={{
                  background: device === 'cuda' ? 'var(--color-primary-light)' : 'var(--color-surface)',
                  borderColor: device === 'cuda' ? 'var(--color-primary)' : 'var(--color-border)',
                  color: device === 'cuda' ? 'var(--color-primary)' : 'var(--color-text)',
                }}
              >
                <span className="flex items-center gap-1.5">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                    <rect x="1" y="3" width="10" height="6" rx="1.5"
                      stroke="currentColor" strokeWidth="1.2" fill="none" />
                    <path d="M4 3V1.5M8 3V1.5M4 9v1.5M8 9v1.5"
                      stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                  </svg>
                  GPU
                </span>
              </button>
            )}
            <button
              type="button"
              onClick={() => setDevice('cpu')}
              className={chipBase}
              style={{
                background: device === 'cpu' ? 'var(--color-primary-light)' : 'var(--color-surface)',
                borderColor: device === 'cpu' ? 'var(--color-primary)' : 'var(--color-border)',
                color: device === 'cpu' ? 'var(--color-primary)' : 'var(--color-text)',
              }}
            >
              <span className="flex items-center gap-1.5">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                  <rect x="2" y="2" width="8" height="8" rx="1.5"
                    stroke="currentColor" strokeWidth="1.2" fill="none" />
                  <rect x="4" y="4" width="4" height="4" rx="0.5"
                    stroke="currentColor" strokeWidth="1" fill="none" />
                </svg>
                CPU
              </span>
            </button>
          </div>
        )}
      </div>

      {/* Model selector */}
      <div className="flex flex-col gap-2">
        <label
          className="text-xs font-semibold tracking-wider"
          style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
        >
          MODEL
        </label>
        {loading ? (
          <Skeleton className="h-48 w-full" />
        ) : (
          <div
            className="rounded-xl overflow-hidden"
            style={{ border: '1px solid var(--color-border)' }}
          >
            {/* Table header */}
            <div
              className="model-grid grid text-xs font-semibold"
              style={{
                gridTemplateColumns: '90px 1fr 1fr 72px',
                padding: '6px 10px',
                background: 'var(--color-surface-2)',
                color: 'var(--color-text-3)',
                letterSpacing: '0.06em',
                borderBottom: '1px solid var(--color-border)',
              }}
            >
              <span>MODEL</span>
              <span className="model-col-speed">SPEED / ACCURACY</span>
              <span className="model-col-pros">PROS &amp; CONS</span>
              <span style={{ textAlign: 'right' }}>VRAM</span>
            </div>

            {MODELS.map((m, idx) => {
              const info = MODEL_INFO[m]
              const fits = modelFitsGpu(m)
              const isActive = model === m
              const gpuFit =
                systemInfo?.cuda_available
                  ? fits === true
                    ? { label: 'Fits', color: 'var(--color-success)' }
                    : fits === false
                      ? { label: '✕', color: 'var(--color-danger)' }
                      : null
                  : null

              return (
                <button
                  key={m}
                  type="button"
                  onClick={() => setModel(m)}
                  className="model-grid w-full text-left grid transition-colors"
                  style={{
                    gridTemplateColumns: '90px 1fr 1fr 72px',
                    padding: '8px 10px',
                    gap: '0',
                    background: isActive ? 'var(--color-primary-light)' : 'var(--color-surface)',
                    borderBottom: idx < MODELS.length - 1 ? '1px solid var(--color-border)' : 'none',
                    borderLeft: `3px solid ${isActive ? 'var(--color-primary)' : 'transparent'}`,
                    cursor: 'pointer',
                  }}
                >
                  {/* Name + GPU fit */}
                  <div className="flex items-center gap-1.5">
                    <span
                      className="text-xs font-semibold"
                      style={{ color: isActive ? 'var(--color-primary)' : 'var(--color-text)' }}
                    >
                      {m.charAt(0).toUpperCase() + m.slice(1)}
                    </span>
                    {gpuFit && (
                      <span className="text-xs" style={{ color: gpuFit.color, fontSize: '10px' }}>
                        {gpuFit.label}
                      </span>
                    )}
                  </div>

                  {/* Speed + accuracy */}
                  <div className="model-col-speed flex flex-col gap-0.5">
                    <span className="text-xs" style={{ color: 'var(--color-text-2)', fontSize: '10px', letterSpacing: '0' }}>
                      {info.speed}
                    </span>
                    <span className="text-xs" style={{ color: '#F59E0B', fontSize: '10px' }}>
                      {info.accuracy}
                    </span>
                  </div>

                  {/* Pros & cons */}
                  <div className="model-col-pros flex flex-col gap-0.5 pr-1">
                    <span className="text-xs" style={{ color: 'var(--color-success)', fontSize: '10px', lineHeight: '1.3' }}>
                      + {info.pro}
                    </span>
                    <span className="text-xs" style={{ color: 'var(--color-danger)', fontSize: '10px', lineHeight: '1.3' }}>
                      − {info.con}
                    </span>
                  </div>

                  {/* VRAM */}
                  <div className="flex flex-col items-end gap-0.5">
                    <span className="text-xs font-medium" style={{ color: 'var(--color-text-2)', fontSize: '10px' }}>
                      {info.vram}
                    </span>
                    <span className="text-xs" style={{ color: 'var(--color-text-3)', fontSize: '10px' }}>
                      {info.bestFor}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* Language dropdown */}
      <div className="flex flex-col gap-2">
        <label
          htmlFor="language-select"
          className="text-xs font-semibold tracking-wider"
          style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
        >
          LANGUAGE
        </label>
        {loading ? (
          <Skeleton className="h-8 w-full" />
        ) : (
          <select
            id="language-select"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-3 py-2 rounded-lg text-sm border appearance-none"
            style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text)',
              outline: 'none',
            }}
          >
            <option value="auto">Auto-detect</option>
            {Object.entries(languages).filter(([code]) => code !== 'auto').map(([code, name]) => (
              <option key={code} value={code}>{name}</option>
            ))}
          </select>
        )}
      </div>

      {/* Translate to dropdown */}
      <div className="flex flex-col gap-2">
        <label
          htmlFor="translate-select"
          className="text-xs font-semibold tracking-wider"
          style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
        >
          TRANSLATE TO
        </label>
        {loading ? (
          <Skeleton className="h-8 w-full" />
        ) : (
          <select
            id="translate-select"
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
            {/* Deduplicate target languages */}
            {[...new Map(translationTargets.map(p => [p.target, p])).values()].map((pair) => (
              <option key={pair.target} value={pair.target}>
                {pair.target_name}{pair.method === 'whisper_translate' ? ' (Whisper)' : ''}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Format selector */}
      <div className="flex flex-col gap-2">
        <label
          className="text-xs font-semibold tracking-wider"
          style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
        >
          FORMAT
        </label>
        <div className="flex gap-2">
          {FORMAT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setFormat(opt.value)}
              className={chipBase}
              style={{
                background: format === opt.value ? 'var(--color-primary-light)' : 'var(--color-surface)',
                borderColor: format === opt.value ? 'var(--color-primary)' : 'var(--color-border)',
                color: format === opt.value ? 'var(--color-primary)' : 'var(--color-text)',
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className="flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-6 sm:p-8 cursor-pointer transition-all"
        style={{
          borderColor: isDragActive ? 'var(--color-primary)' : 'var(--color-border)',
          background: isDragActive ? 'var(--color-primary-light)' : 'var(--color-surface-2)',
        }}
      >
        <input {...getInputProps()} />
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: isDragActive ? 'var(--color-primary)' : 'var(--color-border)' }}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path
              d="M10 13V4M6 8l4-4 4 4"
              stroke={isDragActive ? 'white' : 'var(--color-text-2)'}
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M3 14v1a2 2 0 002 2h10a2 2 0 002-2v-1"
              stroke={isDragActive ? 'white' : 'var(--color-text-2)'}
              strokeWidth="1.75"
              strokeLinecap="round"
            />
          </svg>
        </div>

        <div className="flex flex-col items-center gap-1 text-center">
          <span
            className="text-sm font-medium"
            style={{ color: isDragActive ? 'var(--color-primary)' : 'var(--color-text)' }}
          >
            {isDragActive ? 'Release to upload' : 'Drop a file here or click to browse'}
          </span>
          <span
            className="text-xs"
            style={{ color: 'var(--color-text-3)' }}
          >
            MP4 · MKV · MOV · AVI · MP3 · WAV · M4A · up to 500 MB
          </span>
        </div>
      </div>
    </div>
  )
}
