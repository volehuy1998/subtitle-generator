/**
 * TranscriptionSettings — Word timestamps, initial prompt, diarization preferences.
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { usePreferencesStore } from '../../store/preferencesStore'
import { Switch } from '../ui/Switch'
import { Slider } from '../ui/Slider'

export function TranscriptionSettings() {
  const {
    wordTimestamps,
    initialPrompt,
    diarizeByDefault,
    numSpeakers,
    setPreference,
  } = usePreferencesStore()

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h3 className="text-sm font-semibold text-[var(--color-text)] mb-1">Transcription</h3>
        <p className="text-xs text-[var(--color-text-muted)]">
          Fine-tune how audio is transcribed.
        </p>
      </div>

      <Switch
        label="Word-level timestamps"
        description="Enable per-word timing for precise subtitle alignment."
        checked={wordTimestamps}
        onChange={(v) => setPreference('wordTimestamps', v)}
      />

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-[var(--color-text)]">
          Initial prompt
        </label>
        <textarea
          value={initialPrompt}
          onChange={(e) => {
            if (e.target.value.length <= 500) {
              setPreference('initialPrompt', e.target.value)
            }
          }}
          placeholder="Optional context to guide transcription accuracy..."
          rows={3}
          maxLength={500}
          className="w-full px-3 py-2 text-sm rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] focus:outline-none focus:border-[var(--color-border-focus)] focus:ring-1 focus:ring-[var(--color-border-focus)] transition-colors resize-none"
        />
        <p className="text-xs text-[var(--color-text-muted)] text-right">
          {initialPrompt.length}/500
        </p>
      </div>

      <Switch
        label="Speaker diarization"
        description="Identify and label different speakers in the transcript."
        checked={diarizeByDefault}
        onChange={(v) => setPreference('diarizeByDefault', v)}
      />

      {diarizeByDefault && (
        <Slider
          label="Number of speakers"
          value={numSpeakers ?? 2}
          onChange={(v) => setPreference('numSpeakers', v)}
          min={1}
          max={10}
        />
      )}
    </div>
  )
}
