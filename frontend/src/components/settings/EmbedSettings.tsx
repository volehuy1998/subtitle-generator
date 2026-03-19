/**
 * EmbedSettings — Subtitle embedding mode, style preset, and custom overrides.
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { usePreferencesStore } from '../../store/preferencesStore'
import { Select } from '../ui/Select'
import { Slider } from '../ui/Slider'
import { Switch } from '../ui/Switch'
import { ColorPicker } from '../ui/ColorPicker'

const modeOptions = [
  { value: 'soft', label: 'Soft — mux track (fast, no re-encode)' },
  { value: 'hard', label: 'Hard — burn into video (slow, permanent)' },
]

const presetOptions = [
  { value: 'default', label: 'Default' },
  { value: 'youtube_white', label: 'YouTube White' },
  { value: 'youtube_yellow', label: 'YouTube Yellow' },
  { value: 'cinema', label: 'Cinema' },
  { value: 'large_bold', label: 'Large Bold' },
  { value: 'top', label: 'Top Position' },
]

const positionOptions = [
  { value: 'top', label: 'Top' },
  { value: 'center', label: 'Center' },
  { value: 'bottom', label: 'Bottom' },
]

export function EmbedSettings() {
  const {
    defaultEmbedMode,
    defaultEmbedPreset,
    customFontName,
    customFontSize,
    customFontColor,
    customBold,
    customPosition,
    customBackgroundOpacity,
    setPreference,
  } = usePreferencesStore()

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h3 className="text-sm font-semibold text-[var(--color-text)] mb-1">Embedding</h3>
        <p className="text-xs text-[var(--color-text-muted)]">
          Configure how subtitles are embedded into video files.
        </p>
      </div>

      <Select
        label="Embed mode"
        options={modeOptions}
        value={defaultEmbedMode}
        onChange={(e) =>
          setPreference('defaultEmbedMode', e.target.value as typeof defaultEmbedMode)
        }
      />

      <Select
        label="Style preset"
        options={presetOptions}
        value={defaultEmbedPreset}
        onChange={(e) => setPreference('defaultEmbedPreset', e.target.value)}
      />

      <div className="border-t border-[var(--color-border)] pt-4">
        <h4 className="text-sm font-medium text-[var(--color-text)] mb-4">Custom overrides</h4>
        <div className="space-y-4">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-[var(--color-text)]">Font name</label>
            <input
              type="text"
              value={customFontName}
              onChange={(e) => setPreference('customFontName', e.target.value)}
              placeholder="Arial"
              className="w-full h-9 px-3 text-sm rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] focus:outline-none focus:border-[var(--color-border-focus)] focus:ring-1 focus:ring-[var(--color-border-focus)] transition-colors"
            />
          </div>

          <Slider
            label="Font size"
            value={customFontSize}
            onChange={(v) => setPreference('customFontSize', v)}
            min={8}
            max={72}
            unit="px"
          />

          <ColorPicker
            label="Font color"
            value={customFontColor}
            onChange={(v) => setPreference('customFontColor', v)}
          />

          <Switch
            label="Bold"
            checked={customBold}
            onChange={(v) => setPreference('customBold', v)}
          />

          <Select
            label="Position"
            options={positionOptions}
            value={customPosition}
            onChange={(e) =>
              setPreference('customPosition', e.target.value as typeof customPosition)
            }
          />

          <Slider
            label="Background opacity"
            value={customBackgroundOpacity}
            onChange={(v) => setPreference('customBackgroundOpacity', v)}
            min={0}
            max={1}
            step={0.05}
          />
        </div>
      </div>
    </div>
  )
}
