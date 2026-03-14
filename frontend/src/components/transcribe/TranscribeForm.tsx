import { useState, useEffect, useCallback, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import { api } from '@/api/client'
import { useUIStore } from '@/store/uiStore'
import type { SystemInfo, TranslationPair, ModelPreloadStatus } from '@/api/types'

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

const MODEL_INFO: Record<string, {
  params: string; vram: string; speed: string; wer: string;
  desc: string; tag?: string; tagColor?: string;
}> = {
  tiny:   { params: '39M',   vram: '~1 GB',  speed: '~10x',  wer: '~7.6%', desc: 'Fastest. Good for quick drafts and testing.' },
  base:   { params: '74M',   vram: '~1 GB',  speed: '~7x',   wer: '~5.0%', desc: 'Fast and light. Solid for clear English audio.' },
  small:  { params: '244M',  vram: '~2 GB',  speed: '~4x',   wer: '~3.4%', desc: 'Balanced speed and quality for most tasks.', tag: 'Popular', tagColor: 'var(--color-primary)' },
  medium: { params: '769M',  vram: '~5 GB',  speed: '~2x',   wer: '~2.9%', desc: 'High accuracy. Handles accents and multilingual well.' },
  large:  { params: '1.55B', vram: '~10 GB', speed: '~1x',   wer: '~2.4%', desc: 'Best quality. Ideal for final production output.', tag: 'Best accuracy', tagColor: 'var(--color-success)' },
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
  const [preload, setPreload] = useState<ModelPreloadStatus | null>(null)
  const preloadPoll = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    Promise.all([api.systemInfo(), api.languages(), api.translationLanguages()])
      .then(([info, langs, transLangs]) => {
        setSystemInfo(info)
        setLanguages(langs.languages)
        setTranslationTargets(transLangs.pairs)
        setDevice(info.cuda_available ? 'cuda' : 'cpu')
        // Initialize preload state from system info
        if (info.model_preload) {
          setPreload(info.model_preload)
          // If still loading, auto-select the model being preloaded
          if (info.model_preload.status === 'loading' && info.model_preload.models?.length) {
            setModel(info.model_preload.models[0])
          } else if (info.model_preload.status === 'ready' && info.model_preload.loaded?.length) {
            setModel(info.model_preload.loaded[0])
          }
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // Poll model preload status while loading
  useEffect(() => {
    if (preload?.status !== 'loading') {
      if (preloadPoll.current) clearInterval(preloadPoll.current)
      return
    }
    preloadPoll.current = setInterval(() => {
      api.modelStatus()
        .then((status) => {
          setPreload(status)
          if (status.status !== 'loading' && preloadPoll.current) {
            clearInterval(preloadPoll.current)
          }
        })
        .catch(() => {})
    }, 3000)
    return () => { if (preloadPoll.current) clearInterval(preloadPoll.current) }
  }, [preload?.status])

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

  const modelPreloadState = (m: string): 'ready' | 'loading' | null => {
    if (!preload) return null
    if (preload.loaded?.includes(m)) return 'ready'
    if (preload.status === 'loading' && preload.current_model === m) return 'loading'
    return null
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
          <div className="flex gap-2" role="radiogroup" aria-label="Select device">
            {systemInfo?.cuda_available && (
              <button
                type="button"
                role="radio"
                aria-checked={device === 'cuda'}
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
              role="radio"
              aria-checked={device === 'cpu'}
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
          <div className="flex flex-col gap-2" role="radiogroup" aria-label="Select transcription model">
            {MODELS.map((m) => {
              const info = MODEL_INFO[m]
              const isActive = model === m
              const preloadState = modelPreloadState(m)
              const fits = modelFitsGpu(m)

              // Accuracy bar: tiny=1, base=2, small=3, medium=4, large=5
              const accuracyLevel = MODELS.indexOf(m) + 1
              // Speed bar: tiny=5, base=4, small=3, medium=2, large=1
              const speedLevel = MODELS.length - MODELS.indexOf(m)

              return (
                <button
                  key={m}
                  type="button"
                  role="radio"
                  aria-checked={isActive}
                  onClick={() => setModel(m)}
                  className="w-full text-left rounded-lg border transition-all"
                  style={{
                    padding: '10px 12px',
                    background: isActive ? 'var(--color-primary-light)' : 'var(--color-surface)',
                    borderColor: isActive ? 'var(--color-primary)' : 'var(--color-border)',
                    cursor: 'pointer',
                  }}
                >
                  {/* Row 1: Name + badges */}
                  <div className="flex items-center gap-2 mb-1.5">
                    {/* Radio dot */}
                    <div
                      className="w-3.5 h-3.5 rounded-full border-2 flex-shrink-0 flex items-center justify-center"
                      style={{ borderColor: isActive ? 'var(--color-primary)' : 'var(--color-border-2)' }}
                    >
                      {isActive && (
                        <div className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--color-primary)' }} />
                      )}
                    </div>

                    <span
                      className="text-sm font-semibold"
                      style={{ color: isActive ? 'var(--color-primary)' : 'var(--color-text)' }}
                    >
                      {m.charAt(0).toUpperCase() + m.slice(1)}
                    </span>

                    <span
                      className="text-xs"
                      style={{ color: 'var(--color-text-3)', fontSize: '10px' }}
                    >
                      {info.params} params
                    </span>

                    {/* Tag badge */}
                    {info.tag && (
                      <span
                        className="text-xs font-medium px-1.5 rounded-full"
                        style={{
                          background: isActive ? 'var(--color-primary)' : (info.tagColor ?? 'var(--color-text-3)'),
                          color: 'white',
                          fontSize: '9px',
                          lineHeight: '16px',
                        }}
                      >
                        {info.tag}
                      </span>
                    )}

                    {/* Preload status */}
                    {preloadState === 'ready' && (
                      <span
                        className="inline-flex items-center gap-0.5 text-xs font-medium px-1.5 rounded-full"
                        style={{
                          background: 'var(--color-success-light, #D1FAE5)',
                          color: 'var(--color-success)',
                          fontSize: '9px',
                          lineHeight: '16px',
                        }}
                      >
                        <svg width="8" height="8" viewBox="0 0 8 8" fill="none" aria-hidden="true">
                          <path d="M1.5 4l2 2 3-3.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        Ready
                      </span>
                    )}
                    {preloadState === 'loading' && (
                      <svg className="animate-spin flex-shrink-0" width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true" aria-label="Loading model">
                        <circle cx="6" cy="6" r="4.5" stroke="var(--color-primary)" strokeWidth="1.5" opacity="0.25" />
                        <path d="M10.5 6a4.5 4.5 0 00-4.5-4.5" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round" />
                      </svg>
                    )}

                    {/* GPU fit */}
                    {systemInfo?.cuda_available && fits === false && (
                      <span className="text-xs" style={{ color: 'var(--color-danger)', fontSize: '10px' }}>VRAM</span>
                    )}
                  </div>

                  {/* Row 2: Description */}
                  <p
                    className="text-xs mb-2"
                    style={{ color: 'var(--color-text-2)', marginLeft: '22px', lineHeight: '1.4' }}
                  >
                    {info.desc}
                  </p>

                  {/* Row 3: Stat bars */}
                  <div className="flex gap-4" style={{ marginLeft: '22px' }}>
                    {/* Speed */}
                    <div className="flex items-center gap-1.5 flex-1">
                      <span className="text-xs flex-shrink-0" style={{ color: 'var(--color-text-3)', fontSize: '10px', width: '42px' }}>Speed</span>
                      <div className="flex gap-0.5 flex-1">
                        {[1, 2, 3, 4, 5].map((i) => (
                          <div
                            key={i}
                            className="h-1 rounded-full flex-1"
                            style={{
                              background: i <= speedLevel ? 'var(--color-primary)' : 'var(--color-border)',
                              opacity: i <= speedLevel ? (0.4 + (i / 5) * 0.6) : 1,
                            }}
                          />
                        ))}
                      </div>
                      <span className="text-xs flex-shrink-0" style={{ color: 'var(--color-text-3)', fontSize: '10px', width: '28px', textAlign: 'right', cursor: 'help' }} title="Speed relative to the Large model. 10x means this model processes audio 10 times faster than Large.">{info.speed}</span>
                    </div>

                    {/* Accuracy */}
                    <div className="flex items-center gap-1.5 flex-1">
                      <span className="text-xs flex-shrink-0" style={{ color: 'var(--color-text-3)', fontSize: '10px', width: '52px' }}>Accuracy</span>
                      <div className="flex gap-0.5 flex-1">
                        {[1, 2, 3, 4, 5].map((i) => (
                          <div
                            key={i}
                            className="h-1 rounded-full flex-1"
                            style={{
                              background: i <= accuracyLevel ? 'var(--color-success)' : 'var(--color-border)',
                              opacity: i <= accuracyLevel ? (0.4 + (i / 5) * 0.6) : 1,
                            }}
                          />
                        ))}
                      </div>
                      <span className="text-xs flex-shrink-0" style={{ color: 'var(--color-text-3)', fontSize: '10px', width: '36px', textAlign: 'right', cursor: 'help' }} title="Word Error Rate — percentage of words transcribed incorrectly. Lower is better.">{info.wer} WER</span>
                    </div>
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
        <div className="flex gap-2" role="radiogroup" aria-label="Select output format">
          {FORMAT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              role="radio"
              aria-checked={format === opt.value}
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
