/**
 * CombineView — progress + download view for video+SRT combine operations.
 * Shows combine progress via SSE embed_progress events, then a download button.
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { useEditorStore } from '../../store/editorStore'
import { ProgressBar } from '../ui/ProgressBar'
import { api } from '../../api/client'

interface CombineViewProps {
  taskId: string
}

export function CombineView({ taskId }: CombineViewProps) {
  const phase = useEditorStore(s => s.phase)
  const progress = useEditorStore(s => s.progress)

  const isDone = phase === 'editing'
  const percent = progress?.percent ?? 0

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 gap-6">
      <div className="w-full max-w-md flex flex-col gap-4">
        <h2 className="text-base font-semibold text-[var(--color-text)] text-center">
          {isDone ? 'Ready to download!' : 'Combining subtitles with video...'}
        </h2>

        {!isDone && (
          <ProgressBar value={percent} showPercent />
        )}

        {isDone && (
          <div className="flex justify-center">
            <a
              href={api.combineDownloadUrl(taskId)}
              download
              className="inline-flex items-center justify-center gap-2 font-medium rounded-md transition-colors focus-ring select-none h-9 px-4 text-sm bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] active:bg-[var(--color-primary-hover)]"
            >
              Download video
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
