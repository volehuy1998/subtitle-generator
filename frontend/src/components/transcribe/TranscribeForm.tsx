import { useState, useEffect, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { api } from '@/api/client'
import type { SystemInfo } from '@/api/types'

export interface UploadOptions {
  device: string
  model: string
  language: string
  format: string
}

interface Props {
  onUpload: (file: File, opts: UploadOptions) => void
}

const MODELS = ['tiny', 'base', 'small', 'medium', 'large'] as const

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
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null)
  const [languages, setLanguages] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)

  const [device, setDevice] = useState<string>('cpu')
  const [model, setModel] = useState<string>('base')
  const [language, setLanguage] = useState<string>('auto')
  const [format, setFormat] = useState<string>('srt')

  useEffect(() => {
    Promise.all([api.systemInfo(), api.languages()])
      .then(([info, langs]) => {
        setSystemInfo(info)
        setLanguages(langs.languages)
        setDevice(info.recommended_device)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const onDrop = useCallback((accepted: File[]) => {
    const file = accepted[0]
    if (!file) return
    onUpload(file, { device, model, language, format })
  }, [onUpload, device, model, language, format])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/*': [], 'audio/*': [] },
    multiple: false,
    maxSize: 500 * 1024 * 1024,
  })

  const modelFitsGpu = (m: string) =>
    systemInfo?.models[m]?.fits_gpu ?? null

  const chipBase = 'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer select-none'

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
            {systemInfo?.gpu_available && (
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
          <div className="flex gap-2 flex-wrap">
            {MODELS.map(m => <Skeleton key={m} className="h-7 w-14" />)}
          </div>
        ) : (
          <div className="flex gap-2 flex-wrap">
            {MODELS.map((m) => {
              const fits = modelFitsGpu(m)
              const isActive = model === m
              return (
                <button
                  key={m}
                  type="button"
                  onClick={() => setModel(m)}
                  className={chipBase}
                  style={{
                    background: isActive ? 'var(--color-primary-light)' : 'var(--color-surface)',
                    borderColor: isActive ? 'var(--color-primary)' : 'var(--color-border)',
                    color: isActive ? 'var(--color-primary)' : 'var(--color-text)',
                  }}
                >
                  <span className="flex items-center gap-1.5">
                    {fits === true && (
                      <span
                        className="inline-block w-1.5 h-1.5 rounded-full"
                        style={{ background: 'var(--color-success)' }}
                        title="Fits GPU"
                      />
                    )}
                    {m.charAt(0).toUpperCase() + m.slice(1)}
                  </span>
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
            {Object.entries(languages).map(([code, name]) => (
              <option key={code} value={code}>{name}</option>
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
        className="flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 cursor-pointer transition-all"
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
