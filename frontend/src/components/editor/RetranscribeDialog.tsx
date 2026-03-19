import { useState } from 'react'
import { Dialog } from '../ui/Dialog'
import { Button } from '../ui/Button'
import { Select } from '../ui/Select'
import { Input } from '../ui/Input'
import { Switch } from '../ui/Switch'
import { Slider } from '../ui/Slider'
import { api } from '../../api/client'
import { navigate } from '../../navigation'
import { usePreferencesStore } from '../../store/preferencesStore'

export interface RetranscribeDialogProps {
  open: boolean
  onClose: () => void
  taskId: string
}

const MODEL_OPTIONS = [
  { value: 'tiny', label: 'Tiny' },
  { value: 'base', label: 'Base' },
  { value: 'small', label: 'Small' },
  { value: 'medium', label: 'Medium' },
  { value: 'large', label: 'Large' },
]

export function RetranscribeDialog({ open, onClose, taskId }: RetranscribeDialogProps) {
  const prefs = usePreferencesStore()

  const [modelSize, setModelSize] = useState('large')
  const [language, setLanguage] = useState('')
  const [diarize, setDiarize] = useState(prefs.diarizeByDefault)
  const [wordTimestamps, setWordTimestamps] = useState(prefs.wordTimestamps)
  const [initialPrompt, setInitialPrompt] = useState(prefs.initialPrompt)
  const [numSpeakers, setNumSpeakers] = useState(prefs.numSpeakers ?? 2)
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const handleSubmit = async () => {
    setLoading(true)
    setErrorMsg('')

    try {
      const opts: Record<string, unknown> = {
        model_size: modelSize,
        diarize,
        word_timestamps: wordTimestamps,
      }
      if (language.trim()) opts.language = language.trim()
      if (initialPrompt.trim()) opts.initial_prompt = initialPrompt.trim()
      if (diarize) opts.num_speakers = numSpeakers

      const result = await api.retranscribe(taskId, opts)
      onClose()
      navigate(`/editor/${result.task_id}`)
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Re-transcription failed')
      setLoading(false)
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Re-transcribe"
      description="Re-run transcription with different settings."
      size="sm"
    >
      <div className="flex flex-col gap-4">
        <Select
          label="Model size"
          value={modelSize}
          onChange={e => setModelSize(e.target.value)}
          options={MODEL_OPTIONS}
        />

        <Input
          label="Language override"
          placeholder="Auto-detect"
          value={language}
          onChange={e => setLanguage(e.target.value)}
          helperText="Leave blank to auto-detect."
        />

        <Switch
          checked={wordTimestamps}
          onChange={setWordTimestamps}
          label="Word-level timestamps"
          description="Generate timestamps for each word, enabling precise highlighting."
        />

        <div className="space-y-1.5">
          <label className="text-sm font-medium text-[var(--color-text)]">
            Initial prompt
          </label>
          <textarea
            value={initialPrompt}
            onChange={e => setInitialPrompt(e.target.value.slice(0, 500))}
            placeholder="e.g. domain terms, acronyms, proper nouns..."
            rows={2}
            className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] resize-none"
            maxLength={500}
          />
          <p className="text-xs text-[var(--color-text-muted)]">
            Guide transcription with vocabulary hints. {initialPrompt.length}/500
          </p>
        </div>

        <Switch
          checked={diarize}
          onChange={setDiarize}
          label="Speaker diarization"
          description="Identify and label different speakers in the audio."
        />

        {diarize && (
          <Slider
            value={numSpeakers}
            onChange={setNumSpeakers}
            min={1}
            max={10}
            label="Number of speakers"
          />
        )}

        {errorMsg && (
          <p className="text-sm text-[var(--color-danger)]">{errorMsg}</p>
        )}

        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSubmit} loading={loading}>
            Re-transcribe
          </Button>
        </div>
      </div>
    </Dialog>
  )
}
