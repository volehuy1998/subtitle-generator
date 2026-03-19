/**
 * GeneralSettings — Default model, language, format, and line length preferences.
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { usePreferencesStore } from '../../store/preferencesStore'
import { Select } from '../ui/Select'
import { Slider } from '../ui/Slider'

const modelOptions = [
  { value: 'auto', label: 'Auto (recommended)' },
  { value: 'tiny', label: 'Tiny — fastest, lowest quality' },
  { value: 'base', label: 'Base — fast, basic quality' },
  { value: 'small', label: 'Small — balanced' },
  { value: 'medium', label: 'Medium — good quality' },
  { value: 'large', label: 'Large — best quality' },
]

const formatOptions = [
  { value: 'srt', label: 'SRT — SubRip' },
  { value: 'vtt', label: 'VTT — WebVTT' },
  { value: 'json', label: 'JSON — Structured' },
]

export function GeneralSettings() {
  const { defaultModel, defaultLanguage, preferredFormat, maxLineChars, setPreference } =
    usePreferencesStore()

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h3 className="text-sm font-semibold text-[var(--color-text)] mb-1">General</h3>
        <p className="text-xs text-[var(--color-text-muted)]">
          Configure default transcription and output settings.
        </p>
      </div>

      <Select
        label="Default model"
        options={modelOptions}
        value={defaultModel}
        onChange={(e) =>
          setPreference('defaultModel', e.target.value as typeof defaultModel)
        }
      />

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-[var(--color-text)]">
          Default language
        </label>
        <input
          type="text"
          value={defaultLanguage}
          onChange={(e) => setPreference('defaultLanguage', e.target.value)}
          placeholder="auto"
          className="w-full h-9 px-3 text-sm rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] focus:outline-none focus:border-[var(--color-border-focus)] focus:ring-1 focus:ring-[var(--color-border-focus)] transition-colors"
        />
        <p className="text-xs text-[var(--color-text-muted)]">
          ISO 639-1 code (e.g. en, fr, de) or &quot;auto&quot; for detection.
        </p>
      </div>

      <Select
        label="Preferred format"
        options={formatOptions}
        value={preferredFormat}
        onChange={(e) =>
          setPreference('preferredFormat', e.target.value as typeof preferredFormat)
        }
      />

      <Slider
        label="Max line characters"
        value={maxLineChars}
        onChange={(v) => setPreference('maxLineChars', v)}
        min={20}
        max={120}
        unit=" chars"
      />
    </div>
  )
}
