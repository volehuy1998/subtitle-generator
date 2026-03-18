import { useEffect, useState } from 'react'
import { Download } from 'lucide-react'
import { Button } from '../ui/Button'
import { Select } from '../ui/Select'
import { ProgressBar } from '../ui/ProgressBar'
import { ConfirmDialog } from '../ui/ConfirmDialog'
import { api } from '../../api/client'
import { useEditorStore } from '../../store/editorStore'

type EmbedMode = 'soft' | 'hard'
type Status = 'idle' | 'loading' | 'running' | 'done' | 'error'

interface Preset {
  name: string
  label: string
  description: string
}

export function EmbedPanel() {
  const taskId = useEditorStore(s => s.taskId)

  const [mode, setMode] = useState<EmbedMode>('soft')
  const [preset, setPreset] = useState('default')
  const [presets, setPresets] = useState<Preset[]>([])
  const [status, setStatus] = useState<Status>('idle')
  const [progress, setProgress] = useState(0)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)

  useEffect(() => {
    api.embedPresets()
      .then(r => {
        const list = Object.entries(r.presets).map(([name, p]) => ({
          name,
          label: name.replace(/_/g, ' '),
          description: `${p.font_name} ${p.font_size}pt`,
        }))
        setPresets(list)
        if (list.length > 0) setPreset(list[0].name)
      })
      .catch(() => {/* silently ignore */})
  }, [])

  const presetOptions = presets.map(p => ({ value: p.name, label: p.label }))

  const handleEmbed = async () => {
    if (!taskId) return
    setConfirmOpen(false)
    setStatus('running')
    setProgress(0)
    setErrorMsg('')

    try {
      const fd = new FormData()
      fd.append('mode', mode)
      if (mode === 'hard') fd.append('preset', preset)

      const result = await api.embedQuick(taskId, fd)
      setStatus('done')
      setProgress(100)
      if (result.download_url) {
        setDownloadUrl(result.download_url)
      } else {
        setDownloadUrl(api.embedDownloadUrl(taskId))
      }
    } catch (err) {
      setStatus('error')
      setErrorMsg(err instanceof Error ? err.message : 'Embed failed')
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Mode selector */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-[--color-text]">Mode</label>
        <div className="grid grid-cols-2 gap-2">
          {(['soft', 'hard'] as EmbedMode[]).map(m => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={[
                'rounded-lg border p-2 text-left text-xs transition-colors',
                mode === m
                  ? 'border-[--color-primary] bg-[--color-primary-light] text-[--color-primary]'
                  : 'border-[--color-border] bg-[--color-surface] text-[--color-text-secondary] hover:bg-[--color-surface-raised]',
              ].join(' ')}
            >
              <p className="font-medium">
                {m === 'soft' ? 'Soft' : 'Hard Burn'}
              </p>
              <p className="opacity-70 mt-0.5">
                {m === 'soft' ? 'Fast, no re-encode' : 'Re-encodes video'}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Style preset — only for hard mode */}
      {mode === 'hard' && presetOptions.length > 0 && (
        <Select
          label="Style preset"
          value={preset}
          onChange={e => setPreset(e.target.value)}
          options={presetOptions}
        />
      )}

      {status === 'running' && (
        <ProgressBar value={progress} label="Embedding…" showPercent />
      )}

      {status === 'error' && (
        <p className="text-sm text-[--color-danger]">{errorMsg}</p>
      )}

      {status === 'done' && downloadUrl && (
        <a
          href={downloadUrl}
          download
          className="inline-flex items-center gap-2 text-sm text-[--color-primary] hover:underline"
        >
          <Download className="h-4 w-4" />
          Download embedded video
        </a>
      )}

      <Button
        variant="primary"
        size="sm"
        loading={status === 'running'}
        disabled={status === 'running'}
        onClick={() => setConfirmOpen(true)}
      >
        Embed Subtitles
      </Button>

      <ConfirmDialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleEmbed}
        title="Embed subtitles"
        description={
          mode === 'hard'
            ? 'This will burn subtitles into the video. This cannot be undone.'
            : 'This will mux the subtitle track into your video file.'
        }
        confirmLabel="Embed"
        danger={mode === 'hard'}
      />
    </div>
  )
}
