/**
 * AdvancedUploadOptions — Collapsible panel for transcription settings
 * before upload. Model, language, diarization, timestamps, prompt, translate.
 *
 * — Pixel (Senior Frontend Engineer)
 */
import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '../ui/cn'
import { Select } from '../ui/Select'
import { Switch } from '../ui/Switch'
import { Input } from '../ui/Input'

export interface UploadOptions {
  model: string
  language: string
  diarize: boolean
  numSpeakers: number | null
  wordTimestamps: boolean
  initialPrompt: string
  translateToEnglish: boolean
}

interface Props {
  options: UploadOptions
  onChange: (options: UploadOptions) => void
}

const MODEL_OPTIONS = [
  { value: 'auto', label: 'Auto (recommended)' },
  { value: 'tiny', label: 'Tiny — fastest, least accurate' },
  { value: 'base', label: 'Base — fast, basic accuracy' },
  { value: 'small', label: 'Small — balanced' },
  { value: 'medium', label: 'Medium — slower, more accurate' },
  { value: 'large', label: 'Large — slowest, best accuracy' },
]

export function AdvancedUploadOptions({ options, onChange }: Props) {
  const [expanded, setExpanded] = useState(false)

  const update = <K extends keyof UploadOptions>(key: K, value: UploadOptions[K]) => {
    onChange({ ...options, [key]: value })
  }

  return (
    <div className="mt-4" data-testid="advanced-upload-options">
      <button
        type="button"
        onClick={() => setExpanded(prev => !prev)}
        className={cn(
          'flex items-center gap-1.5 text-sm font-medium transition-colors',
          'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
        )}
        aria-expanded={expanded}
        aria-controls="advanced-options-panel"
      >
        <ChevronDown
          className={cn(
            'h-4 w-4 transition-transform',
            expanded && 'rotate-180'
          )}
        />
        Advanced options
      </button>

      {expanded && (
        <div
          id="advanced-options-panel"
          className="mt-3 space-y-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-4"
        >
          <Select
            label="Model"
            options={MODEL_OPTIONS}
            value={options.model}
            onChange={e => update('model', e.target.value)}
          />

          <Input
            label="Language"
            placeholder="auto"
            value={options.language === 'auto' ? '' : options.language}
            onChange={e => update('language', e.target.value || 'auto')}
            helperText="ISO code (e.g. en, fr, de) or leave empty for auto-detection"
          />

          <Switch
            label="Speaker diarization"
            description="Identify and label different speakers"
            checked={options.diarize}
            onChange={checked => update('diarize', checked)}
          />

          <Switch
            label="Word-level timestamps"
            description="Generate timestamps for each word"
            checked={options.wordTimestamps}
            onChange={checked => update('wordTimestamps', checked)}
          />

          <Switch
            label="Translate to English"
            description="Use Whisper's built-in translation (any language to English)"
            checked={options.translateToEnglish}
            onChange={checked => update('translateToEnglish', checked)}
          />

          <Input
            label="Initial prompt"
            placeholder="Optional context for the model..."
            value={options.initialPrompt}
            onChange={e => update('initialPrompt', e.target.value)}
            helperText="Provide context or vocabulary hints to improve accuracy"
          />
        </div>
      )}
    </div>
  )
}
