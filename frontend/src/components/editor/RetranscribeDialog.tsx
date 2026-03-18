import { useState } from 'react'
import { Dialog } from '../ui/Dialog'
import { Button } from '../ui/Button'
import { Select } from '../ui/Select'
import { Input } from '../ui/Input'
import { api } from '../../api/client'
import { navigate } from '../../navigation'

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
  const [modelSize, setModelSize] = useState('large')
  const [language, setLanguage] = useState('')
  const [diarize, setDiarize] = useState(false)
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const handleSubmit = async () => {
    setLoading(true)
    setErrorMsg('')

    try {
      const opts: Record<string, unknown> = { model_size: modelSize, diarize }
      if (language.trim()) opts.language = language.trim()

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

        <label className="flex items-center gap-2 text-sm text-[var(--color-text)] cursor-pointer select-none">
          <input
            type="checkbox"
            checked={diarize}
            onChange={e => setDiarize(e.target.checked)}
            className="h-4 w-4 rounded border-[var(--color-border)] accent-[var(--color-primary)]"
          />
          Enable speaker diarization
        </label>

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
