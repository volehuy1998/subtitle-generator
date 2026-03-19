import { useEffect, useState } from 'react'
import { Button } from '../ui/Button'
import { ProgressBar } from '../ui/ProgressBar'
import { Select } from '../ui/Select'
import { api } from '../../api/client'
import { useEditorStore } from '../../store/editorStore'
import type { TranslationPair } from '../../api/types'

type Engine = 'whisper' | 'argos'
type Status = 'idle' | 'running' | 'done' | 'error'

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

  const handleTranslate = async () => {
    if (!taskId) return
    setStatus('running')
    setErrorMsg('')

    if (engine === 'whisper') {
      // Whisper can only translate to English during re-transcription
      setStatus('done')
      return
    }

    // Argos translation — call the API and listen for SSE completion
    try {
      await api.translate(taskId, targetLanguage)

      // Listen for translate_done SSE event
      const baseUrl = window.location.origin
      const es = new EventSource(`${baseUrl}/events/${taskId}`)

      es.addEventListener('translate_done', () => {
        setStatus('done')
        setErrorMsg('')
        es.close()
      })

      es.addEventListener('translate_error', (e) => {
        try {
          const data = JSON.parse(e.data)
          setStatus('error')
          setErrorMsg(data.message || 'Translation failed')
        } catch {
          setStatus('error')
          setErrorMsg('Translation failed')
        }
        es.close()
      })

      // Safety timeout
      setTimeout(() => {
        if (es.readyState !== EventSource.CLOSED) {
          es.close()
          setStatus('done')
        }
      }, 300000) // 5 min timeout for large translations
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

      {status === 'running' && engine === 'argos' && (
        <ProgressBar label="Translating…" />
      )}

      {status === 'done' && engine === 'whisper' && (
        <div className="p-3 rounded-lg bg-[var(--color-primary-light)] text-sm text-[var(--color-text)]">
          <p className="font-medium mb-1">Use Re-transcribe</p>
          <p className="text-[var(--color-text-secondary)]">
            To translate to English, click the Re-transcribe button in the toolbar and enable &quot;Translate to English&quot; in the options.
          </p>
        </div>
      )}

      {status === 'done' && engine === 'argos' && (
        <div className="p-3 rounded-lg bg-[var(--color-success-light)] text-sm text-[var(--color-success)]">
          Translation complete! Subtitles translated to {targetLanguage}.
        </div>
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
        {status === 'done' ? 'Translate Again' : 'Begin Translation'}
      </Button>
    </div>
  )
}
