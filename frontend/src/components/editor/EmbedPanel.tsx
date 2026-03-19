import { useEffect, useState } from 'react'
import { Download } from 'lucide-react'
import { Button } from '../ui/Button'
import { Select } from '../ui/Select'
import { ProgressBar } from '../ui/ProgressBar'
import { ConfirmDialog } from '../ui/ConfirmDialog'
import { CustomEmbedStyler, type EmbedStyle } from './CustomEmbedStyler'
import { api } from '../../api/client'
import { useEditorStore } from '../../store/editorStore'
import { usePreferencesStore } from '../../store/preferencesStore'

type EmbedMode = 'soft' | 'hard'
type Status = 'idle' | 'loading' | 'running' | 'done' | 'error'

interface Preset {
  name: string
  label: string
  description: string
}

export function EmbedPanel() {
  const taskId = useEditorStore(s => s.taskId)

  const prefs = usePreferencesStore()

  const [mode, setMode] = useState<EmbedMode>(prefs.defaultEmbedMode)
  const [preset, setPreset] = useState(prefs.defaultEmbedPreset)
  const [useCustomStyle, setUseCustomStyle] = useState(false)
  const [customStyle, setCustomStyle] = useState<EmbedStyle>({
    fontName: prefs.customFontName,
    fontSize: prefs.customFontSize,
    fontColor: prefs.customFontColor,
    bold: prefs.customBold,
    position: prefs.customPosition,
    backgroundOpacity: prefs.customBackgroundOpacity,
  })
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
    setDownloadUrl(null)
    setStatus('running')
    setProgress(0)
    setErrorMsg('')

    try {
      const fd = new FormData()
      fd.append('mode', mode)
      if (mode === 'hard') {
        if (useCustomStyle) {
          fd.append('font_name', customStyle.fontName)
          fd.append('font_size', String(customStyle.fontSize))
          fd.append('font_color', customStyle.fontColor)
          fd.append('bold', String(customStyle.bold))
          fd.append('position', customStyle.position)
          fd.append('background_opacity', String(customStyle.backgroundOpacity))
        } else {
          fd.append('preset', preset)
        }
      }

      const result = await api.embedQuick(taskId, fd)
      setStatus('done')
      setProgress(100)
      if (result.download_url) {
        setDownloadUrl(result.download_url)
      } else {
        setDownloadUrl(api.embedDownloadUrl(taskId))
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Embed failed'
      if (msg.includes('409') || msg.toLowerCase().includes('already in progress')) {
        setStatus('error')
        setErrorMsg('An embed is already in progress. Please wait for it to finish.')
      } else {
        setStatus('error')
        setErrorMsg(msg)
      }
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Mode selector */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-[var(--color-text)]">Mode</label>
        <div className="grid grid-cols-2 gap-2">
          {(['soft', 'hard'] as EmbedMode[]).map(m => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={[
                'rounded-lg border p-2 text-left text-xs transition-colors',
                mode === m
                  ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)] text-[var(--color-primary)]'
                  : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-raised)]',
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

      {/* Style options — only for hard mode */}
      {mode === 'hard' && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setUseCustomStyle(false)}
              className={[
                'text-xs px-3 py-1.5 rounded-md border transition-colors',
                !useCustomStyle
                  ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)] text-[var(--color-primary)]'
                  : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-raised)]',
              ].join(' ')}
            >
              Preset
            </button>
            <button
              type="button"
              onClick={() => setUseCustomStyle(true)}
              className={[
                'text-xs px-3 py-1.5 rounded-md border transition-colors',
                useCustomStyle
                  ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)] text-[var(--color-primary)]'
                  : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-raised)]',
              ].join(' ')}
            >
              Custom
            </button>
          </div>

          {!useCustomStyle && presetOptions.length > 0 && (
            <Select
              label="Style preset"
              value={preset}
              onChange={e => setPreset(e.target.value)}
              options={presetOptions}
            />
          )}

          {useCustomStyle && (
            <CustomEmbedStyler style={customStyle} onChange={setCustomStyle} />
          )}
        </div>
      )}

      {status === 'running' && (
        <ProgressBar value={progress} label="Embedding…" showPercent />
      )}

      {status === 'error' && (
        <p className="text-sm text-[var(--color-danger)]">{errorMsg}</p>
      )}

      {status === 'done' && downloadUrl && (
        <a
          href={downloadUrl}
          download
          className="inline-flex items-center gap-2 text-sm text-[var(--color-primary)] hover:underline"
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
        onClick={() => { if (status !== 'running') setConfirmOpen(true) }}
      >
        Embed Subtitles
      </Button>

      <ConfirmDialog
        open={confirmOpen && status !== 'running'}
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
