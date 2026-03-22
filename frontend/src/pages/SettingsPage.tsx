/**
 * SettingsPage — Tabbed settings interface with general, transcription,
 * embedding, and appearance panels.
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { useState } from 'react'
import { Tabs } from '../components/ui/Tabs'
import { GeneralSettings } from '../components/settings/GeneralSettings'
import { TranscriptionSettings } from '../components/settings/TranscriptionSettings'
import { EmbedSettings } from '../components/settings/EmbedSettings'
import { AppearanceSettings } from '../components/settings/AppearanceSettings'
import { usePreferencesStore } from '../store/preferencesStore'
import { Settings, Mic, Palette, Subtitles } from 'lucide-react'

const tabs = [
  { id: 'general', label: 'General', icon: <Settings className="h-4 w-4" /> },
  { id: 'transcription', label: 'Transcription', icon: <Mic className="h-4 w-4" /> },
  { id: 'embedding', label: 'Embedding', icon: <Subtitles className="h-4 w-4" /> },
  { id: 'appearance', label: 'Appearance', icon: <Palette className="h-4 w-4" /> },
]

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general')
  const reset = usePreferencesStore((s) => s.reset)

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-[var(--color-text)]">Settings</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
            Manage your preferences and defaults.
          </p>
        </div>
        <button
          onClick={reset}
          className="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors"
        >
          Reset all
        </button>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      <div className="mt-6">
        {activeTab === 'general' && <GeneralSettings />}
        {activeTab === 'transcription' && <TranscriptionSettings />}
        {activeTab === 'embedding' && <EmbedSettings />}
        {activeTab === 'appearance' && <AppearanceSettings />}
      </div>
    </div>
  )
}
