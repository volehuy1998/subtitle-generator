/**
 * PreferencesPanel — slide-out settings panel from the right.
 * Allows configuring default model, output format, language, and auto-copy.
 *
 * — Pixel (Sr. Frontend), Sprint L47
 */

import { usePreferencesStore } from '@/store/preferencesStore'

interface Props {
  open: boolean
  onClose: () => void
}

const MODELS = [
  { value: 'tiny', label: 'Tiny', desc: 'Fastest, lower accuracy' },
  { value: 'base', label: 'Base', desc: 'Good balance' },
  { value: 'small', label: 'Small', desc: 'Better accuracy' },
  { value: 'medium', label: 'Medium', desc: 'High accuracy' },
  { value: 'large', label: 'Large', desc: 'Best accuracy, slowest' },
]

const FORMATS = [
  { value: 'srt', label: 'SRT', desc: 'Universal subtitle format' },
  { value: 'vtt', label: 'VTT', desc: 'Web Video Text Tracks' },
  { value: 'json', label: 'JSON', desc: 'Structured data' },
]

const LANGUAGES = [
  { value: 'auto', label: 'Auto-detect' },
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'ja', label: 'Japanese' },
  { value: 'ko', label: 'Korean' },
  { value: 'zh', label: 'Chinese' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'ru', label: 'Russian' },
  { value: 'ar', label: 'Arabic' },
  { value: 'hi', label: 'Hindi' },
]

function SelectField({ label, value, onChange, options, description }: {
  label: string
  value: string
  onChange: (v: string) => void
  options: Array<{ value: string; label: string; desc?: string }>
  description?: string
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label
        className="text-xs font-semibold"
        style={{ color: 'var(--color-text)' }}
      >
        {label}
      </label>
      {description && (
        <span className="text-xs" style={{ color: 'var(--color-text-3)', marginTop: '-4px' }}>
          {description}
        </span>
      )}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="px-3 py-2 rounded-lg text-sm"
        style={{
          background: 'var(--color-surface-2)',
          border: '1px solid var(--color-border)',
          color: 'var(--color-text)',
          cursor: 'pointer',
          outline: 'none',
        }}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}{opt.desc ? ` — ${opt.desc}` : ''}
          </option>
        ))}
      </select>
    </div>
  )
}

function ToggleField({ label, description, checked, onChange }: {
  label: string
  description: string
  checked: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <div className="flex flex-col gap-0.5">
        <span className="text-xs font-semibold" style={{ color: 'var(--color-text)' }}>
          {label}
        </span>
        <span className="text-xs" style={{ color: 'var(--color-text-3)' }}>
          {description}
        </span>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className="flex-shrink-0 relative rounded-full transition-colors"
        style={{
          width: '36px',
          height: '20px',
          background: checked ? 'var(--color-primary)' : 'var(--color-border-2)',
          border: 'none',
          cursor: 'pointer',
          padding: 0,
        }}
      >
        <span
          className="block rounded-full transition-transform"
          style={{
            width: '16px',
            height: '16px',
            background: 'white',
            transform: checked ? 'translateX(18px)' : 'translateX(2px)',
            marginTop: '2px',
            boxShadow: '0 1px 2px rgba(0,0,0,0.15)',
          }}
        />
      </button>
    </div>
  )
}

export function PreferencesPanel({ open, onClose }: Props) {
  const prefs = usePreferencesStore()

  if (!open) return null

  return (
    <>
      {/* Overlay */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.3)',
          zIndex: 50,
        }}
        onClick={onClose}
        onKeyDown={(e) => { if (e.key === 'Escape') onClose() }}
      />

      {/* Slide-out panel */}
      <div
        className="animate-slide-in-right flex flex-col"
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: '320px',
          maxWidth: '90vw',
          background: 'var(--color-bg)',
          borderLeft: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow-lg)',
          zIndex: 51,
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-4 py-3"
          style={{ borderBottom: '1px solid var(--color-border)' }}
        >
          <h2
            className="text-sm font-semibold"
            style={{ color: 'var(--color-text)' }}
          >
            Preferences
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close preferences"
            className="flex items-center justify-center rounded-lg transition-colors"
            style={{
              width: '28px',
              height: '28px',
              background: 'transparent',
              border: 'none',
              color: 'var(--color-text-2)',
              cursor: 'pointer',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = 'var(--color-surface-2)' }}
            onMouseLeave={e => { e.currentTarget.style.background = 'transparent' }}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-5">
          <SelectField
            label="Default Model"
            description="Used when starting a new transcription"
            value={prefs.defaultModel}
            onChange={(v) => prefs.setPreference('defaultModel', v)}
            options={MODELS}
          />

          <SelectField
            label="Default Output Format"
            description="Preferred download format"
            value={prefs.defaultFormat}
            onChange={(v) => prefs.setPreference('defaultFormat', v)}
            options={FORMATS}
          />

          <SelectField
            label="Default Language"
            description="Source language for transcription"
            value={prefs.defaultLanguage}
            onChange={(v) => prefs.setPreference('defaultLanguage', v)}
            options={LANGUAGES}
          />

          <div style={{ height: '1px', background: 'var(--color-border)' }} />

          <ToggleField
            label="Auto-copy on completion"
            description="Copy all segment text to clipboard when transcription finishes"
            checked={prefs.autoCopy}
            onChange={(v) => prefs.setPreference('autoCopy', v)}
          />
        </div>

        {/* Footer */}
        <div
          className="px-4 py-3 flex items-center justify-between"
          style={{ borderTop: '1px solid var(--color-border)' }}
        >
          <button
            type="button"
            onClick={() => prefs.resetPreferences()}
            className="text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
            style={{
              background: 'transparent',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-2)',
              cursor: 'pointer',
            }}
          >
            Reset to Defaults
          </button>
          <span className="text-xs" style={{ color: 'var(--color-text-3)' }}>
            Saved automatically
          </span>
        </div>
      </div>
    </>
  )
}
