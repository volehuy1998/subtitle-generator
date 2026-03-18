/**
 * EditorPage — full editor experience with session restore, progress,
 * combine, editing, and error states.
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { useEffect } from 'react'
import { AppShell } from '../components/layout/AppShell'
import { ProgressView } from '../components/editor/ProgressView'
import { EditorToolbar } from '../components/editor/EditorToolbar'
import { SegmentList } from '../components/editor/SegmentList'
import { ContextPanel } from '../components/editor/ContextPanel'
import { CombineView } from '../components/editor/CombineView'
import { Spinner } from '../components/ui/Spinner'
import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'
import { useEditorStore } from '../store/editorStore'
import { useSSE } from '../hooks/useSSE'
import { api } from '../api/client'
import { navigate } from '../navigation'

export function EditorPage({ taskId }: { taskId: string }) {
  const phase = useEditorStore(s => s.phase)
  const storedTaskId = useEditorStore(s => s.taskId)
  const setTaskId = useEditorStore(s => s.setTaskId)
  const setComplete = useEditorStore(s => s.setComplete)
  const setError = useEditorStore(s => s.setError)
  const setPhase = useEditorStore(s => s.setPhase)
  const setFileMetadata = useEditorStore(s => s.setFileMetadata)
  const fileMetadata = useEditorStore(s => s.fileMetadata)

  // Session restore: on mount, if task not already loaded, fetch its status
  useEffect(() => {
    if (taskId === 'local') return
    if (storedTaskId === taskId && phase !== 'idle') return

    setTaskId(taskId)
    setPhase('processing')

    api.progress(taskId).then(data => {
      if (data.filename) {
        setFileMetadata({ filename: data.filename, duration: data.audio_duration ?? 0 })
      }
      if (data.status === 'done') {
        api.subtitles(taskId).then(subs => {
          setComplete({
            segments: (subs.segments || []).map((seg, i) => ({ ...seg, index: i })),
            language: data.language || null,
            modelUsed: data.model || null,
            timings: { ...(data.step_timings || {}) } as Record<string, number>,
            isVideo: data.is_video ?? false,
          })
        }).catch(() => setError('Failed to load subtitles'))
      } else if (data.status === 'error' || data.status === 'cancelled') {
        setError(data.error || data.message || 'Task failed')
      }
      // else: still processing — SSE will handle updates
    }).catch(() => {
      setError('Project not found or deleted')
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId])

  // Connect SSE for in-progress tasks
  useSSE(taskId === 'local' ? null : taskId)

  // Loading state (taskId just set, fetching status)
  if (phase === 'idle' && taskId !== 'local') {
    return (
      <AppShell>
        <div className="flex justify-center py-20">
          <Spinner size="lg" />
        </div>
      </AppShell>
    )
  }

  // Error state
  if (phase === 'error') {
    return (
      <AppShell>
        <div className="max-w-2xl mx-auto py-8 px-4">
          <Alert type="error" title="Something went wrong">
            <p className="mb-4">The project could not be loaded. It may have been deleted or the server is unavailable.</p>
            <div className="flex gap-3">
              <Button variant="secondary" onClick={() => navigate('/')}>Back to Home</Button>
              <Button variant="primary" onClick={() => { setPhase('processing') }}>Retry</Button>
            </div>
          </Alert>
        </div>
      </AppShell>
    )
  }

  // Processing / uploading state
  if (phase === 'uploading' || phase === 'processing') {
    // Check if this is a combine task (no fileMetadata or filename ends in .srt/.vtt)
    const isCombine = fileMetadata?.filename?.match(/\.(srt|vtt)$/i)
    if (isCombine) {
      return <AppShell><CombineView taskId={taskId} /></AppShell>
    }
    return <AppShell><ProgressView taskId={taskId} /></AppShell>
  }

  // Editing state
  return (
    <AppShell>
      <div className="max-w-[1280px] mx-auto px-4 py-4">
        <EditorToolbar />
        <div className="flex gap-6 flex-col lg:flex-row mt-4">
          <div className="flex-1 min-w-0">
            <SegmentList taskId={taskId} />
          </div>
          <div className="w-full lg:w-[360px] shrink-0">
            <ContextPanel />
          </div>
        </div>
      </div>
    </AppShell>
  )
}
