import { useEditorStore } from '../../store/editorStore'
import { ProgressBar } from '../ui/ProgressBar'
import { Button } from '../ui/Button'
import { Tooltip, TooltipProvider } from '../ui/Tooltip'
import { PipelineSteps } from './PipelineSteps'
import { LivePreview } from './LivePreview'
import { api } from '../../api/client'
import { navigate } from '../../navigation'

interface ProgressViewProps {
  taskId: string
}

export function ProgressView({ taskId }: ProgressViewProps) {
  const fileMetadata = useEditorStore(s => s.fileMetadata)
  const progress = useEditorStore(s => s.progress)
  const modelUsed = useEditorStore(s => s.modelUsed)

  const handleCancel = async () => {
    try {
      await api.cancel(taskId)
    } catch {
      // best-effort cancel; navigate regardless
    }
    navigate('/')
  }

  const etaDisplay = progress?.eta != null ? `ETA: ${progress.eta}s` : null
  const speedDisplay = progress?.speed != null ? `${progress.speed.toFixed(1)}x speed` : null
  const segmentDisplay =
    progress != null
      ? `${progress.segmentCount} segment${progress.segmentCount !== 1 ? 's' : ''}`
      : null

  const statParts = [segmentDisplay, etaDisplay, speedDisplay].filter(Boolean)

  return (
    <TooltipProvider>
      <div className="flex flex-col gap-4 p-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
        {/* Header */}
        <div>
          <p className="text-sm font-medium text-[var(--color-text)] truncate">
            {fileMetadata?.filename ?? 'Processing...'}
          </p>
          {modelUsed && (
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
              Model: {modelUsed}
            </p>
          )}
        </div>

        {/* Progress bar */}
        <ProgressBar value={progress?.percent ?? 0} showPercent />

        {/* Stats */}
        {statParts.length > 0 && (
          <p className="text-xs text-[var(--color-text-secondary)]">
            {statParts.join(' | ')}
          </p>
        )}

        {/* Message */}
        {progress?.message && (
          <p className="text-xs text-[var(--color-text-muted)] italic">{progress.message}</p>
        )}

        {/* Pipeline steps */}
        <PipelineSteps currentStep={progress?.pipelineStep ?? null} />

        {/* Live preview */}
        <LivePreview />

        {/* Actions */}
        <div className="flex gap-2 mt-1">
          <Tooltip content="Coming soon" side="top">
            <span>
              <Button variant="secondary" size="sm" disabled>
                Pause
              </Button>
            </span>
          </Tooltip>
          <Button variant="danger" size="sm" onClick={handleCancel}>
            Cancel
          </Button>
        </div>
      </div>
    </TooltipProvider>
  )
}
