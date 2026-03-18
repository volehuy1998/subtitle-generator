import { useEffect, useState } from 'react'
import { Button } from '../ui/Button'
import { Select } from '../ui/Select'
import { ProgressBar } from '../ui/ProgressBar'
import { ConfirmDialog } from '../ui/ConfirmDialog'
import { api } from '../../api/client'
import { useEditorStore } from '../../store/editorStore'
import type { TranslationPair } from '../../api/types'

type Engine = 'whisper' | 'argos'
type Status = 'idle' | 'loading' | 'running' | 'done' | 'error'

export function TranslatePanel() {
  const taskId = useEditorStore(s => s.taskId)
  const sourceLanguage = useEditorStore(s => s.language)

  const [pairs, setPairs] = useState<TranslationPair[]>([])
  const [targetLanguage, setTargetLanguage] = useState('en')
  const [engine, setEngine] = useState<Engine>('whisper')
  const [status, setStatus] = useState<Status>('idle')
  const [progress, setProgress] = useState(0)
  const [errorMsg, setErrorMsg] = useState('')
  const [showNoApiDialog, setShowNoApiDialog] = useState(false)

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

  const handleTranslate = async () => {
    if (!taskId) return

    // Check if api.translate exists
    if (typeof (api as Record<string, unknown>)['translate'] !== 'function') {
      setShowNoApiDialog(true)
      return
    }

    setStatus('running')
    setProgress(0)
    setErrorMsg('')

    try {
      await (api as unknown as { translate: (id: string, opts: Record<string, unknown>) => Promise<unknown> })
        .translate(taskId, { target_language: targetLanguage, engine })
      setStatus('done')
      setProgress(100)
    } catch (err) {
      setStatus('error')
      setErrorMsg(err instanceof Error ? err.message : 'Translation failed')
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

      {status === 'running' && (
        <ProgressBar value={progress} label="Translating…" showPercent />
      )}

      {status === 'done' && (
        <p className="text-sm text-[var(--color-success)]">Translation complete.</p>
      )}

      {status === 'error' && (
        <p className="text-sm text-[var(--color-danger)]">{errorMsg}</p>
      )}

      <Button
        variant="primary"
        size="sm"
        loading={status === 'running'}
        disabled={status === 'running'}
        onClick={handleTranslate}
      >
        Begin Translation
      </Button>

      <ConfirmDialog
        open={showNoApiDialog}
        onClose={() => setShowNoApiDialog(false)}
        onConfirm={() => setShowNoApiDialog(false)}
        title="Translation not available"
        description="Translation API is not yet available. Try re-transcribing with Whisper translate mode instead."
        confirmLabel="OK"
      />
    </div>
  )
}
