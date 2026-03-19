import { useEffect, useState } from 'react'
import { Button } from '../ui/Button'
import { Select } from '../ui/Select'
import { api } from '../../api/client'
import { useEditorStore } from '../../store/editorStore'
import type { TranslationPair } from '../../api/types'

type Engine = 'whisper' | 'argos'
type Status = 'idle' | 'done' | 'error'

export function TranslatePanel() {
  const taskId = useEditorStore(s => s.taskId)
  const sourceLanguage = useEditorStore(s => s.language)

  const [pairs, setPairs] = useState<TranslationPair[]>([])
  const [targetLanguage, setTargetLanguage] = useState('en')
  const [engine, setEngine] = useState<Engine>('whisper')
  const [status, setStatus] = useState<Status>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    api.translationLanguages()
      .then(r => setPairs(r.pairs))
      .catch(() => {/* silently ignore — API may not have any pairs */})
  }, [])

  const targetOptions = pairs
    .filter(p => p.target !== sourceLanguage)
    .map(p => ({ value: p.target, label: p.target_name }))

  // Deduplicate by value
  const uniqueTargets = targetOptions.filter(
    (opt, idx, arr) => arr.findIndex(o => o.value === opt.value) === idx
  )

  // No standalone translate API exists on the backend.
  // Whisper translate = re-transcribe with task="translate".
  // Argos translate = pipeline step during transcription.
  // Show guidance instead of a broken API call. — Pixel (Sr. Frontend Engineer)
  const handleTranslate = () => {
    if (!taskId) return

    if (engine === 'whisper') {
      setErrorMsg('')
      setStatus('done')
    } else {
      setStatus('error')
      setErrorMsg('Standalone Argos translation is not yet available. Use the Advanced Upload Options to enable translation during transcription.')
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-[var(--color-text)]">Source language</label>
        <div className="h-9 px-3 flex items-center text-sm text-[var(--color-text-secondary)] rounded-md border border-[var(--color-border)] bg-[var(--color-surface-raised)]">
          {sourceLanguage ?? 'Auto-detected'}
        </div>
      </div>

      <Select
        label="Target language"
        value={targetLanguage}
        onChange={e => setTargetLanguage(e.target.value)}
        options={uniqueTargets.length > 0 ? uniqueTargets : [{ value: 'en', label: 'English' }]}
      />

      {/* Engine selector */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-[var(--color-text)]">Engine</label>
        <div className="grid grid-cols-2 gap-2">
          {(['whisper', 'argos'] as Engine[]).map(e => (
            <button
              key={e}
              type="button"
              onClick={() => setEngine(e)}
              className={[
                'rounded-lg border p-2 text-left text-xs transition-colors',
                engine === e
                  ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)] text-[var(--color-primary)]'
                  : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-raised)]',
              ].join(' ')}
            >
              <p className="font-medium">
                {e === 'whisper' ? 'Whisper' : 'Argos'}
              </p>
              <p className="opacity-70 mt-0.5">
                {e === 'whisper' ? 'EN only' : 'Any language'}
              </p>
            </button>
          ))}
        </div>
      </div>

      {status === 'done' && engine === 'whisper' && (
        <div className="p-3 rounded-lg bg-[var(--color-primary-light)] text-sm text-[var(--color-text)]">
          <p className="font-medium mb-1">Use Re-transcribe</p>
          <p className="text-[var(--color-text-secondary)]">
            To translate to English, click the Re-transcribe button in the toolbar and enable &quot;Translate to English&quot; in the options.
          </p>
        </div>
      )}

      {status === 'error' && (
        <p className="text-sm text-[var(--color-danger)]">{errorMsg}</p>
      )}

      <Button
        variant="primary"
        size="sm"
        disabled={status === 'done'}
        onClick={handleTranslate}
      >
        Begin Translation
      </Button>
    </div>
  )
}
