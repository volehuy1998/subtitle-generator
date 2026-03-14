import { useEffect } from 'react'
import { AppHeader } from '@/components/layout/AppHeader'
import { HealthPanel } from '@/components/system/HealthPanel'
import { ConnectionBanner } from '@/components/system/ConnectionBanner'
import { TaskQueuePanel } from '@/components/system/TaskQueuePanel'
import { TranscribeForm } from '@/components/transcribe/TranscribeForm'
import { ProgressView } from '@/components/progress/ProgressView'
import { OutputPanel } from '@/components/output/OutputPanel'
import { EmbedTab } from '@/components/embed/EmbedTab'
import { useTaskStore } from '@/store/taskStore'
import { useUIStore } from '@/store/uiStore'
import { api } from '@/api/client'

type AppTab = 'transcribe' | 'embed'

export default function App() {
  const { healthPanelOpen, setHealthPanelOpen, appMode, setAppMode, health } = useUIStore()
  const store = useTaskStore()

  // Session restore: if a task was in progress, try to reconnect
  useEffect(() => {
    const savedTaskId = localStorage.getItem('sg_currentTaskId')
    if (!savedTaskId) return

    api.progress(savedTaskId)
      .then((data) => {
        if (data.status === 'done') {
          store.setTaskId(savedTaskId)
          store.setComplete({
            filename: data.filename ?? null,
            fileSize: data.file_size ?? null,
            language: data.language ?? null,
            segments: data.segments ?? 0,
            totalTimeSec: data.total_time_sec ?? null,
            stepTimings: data.step_timings ?? {},
            isVideo: data.is_video ?? false,
            percent: 100,
          })
          // Restore live segment preview from saved SRT
          api.subtitles(savedTaskId)
            .then((sub) => {
              if (sub.segments?.length) {
                store.setLiveSegments(sub.segments.map((s) => ({
                  start: s.start,
                  end: s.end,
                  text: s.text,
                })))
              }
            })
            .catch(() => { /* SRT may not exist yet, ignore */ })
        } else if (
          data.status !== 'cancelled' &&
          data.status !== 'error'
        ) {
          store.setTaskId(savedTaskId)
          store.applyProgressData({
            filename: data.filename ?? null,
            fileSize: data.file_size ?? null,
            status: data.status,
            percent: data.percent,
            message: data.message,
          })
        }
      })
      .catch(() => {
        localStorage.removeItem('sg_currentTaskId')
      })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleUpload = async (file: File, opts: { device: string; model: string; language: string; format: string; translateTo?: string }) => {
    // Switch to progress screen immediately
    store.reset()
    store.setTaskId('uploading')
    store.setUploading(true, 0)
    store.applyProgressData({
      filename: file.name,
      fileSize: file.size,
      status: 'uploading',
      percent: 0,
      message: `Uploading ${file.name}…`,
    })

    const fd = new FormData()
    fd.append('file', file)
    fd.append('model_size', opts.model)
    fd.append('language', opts.language === 'auto' ? '' : opts.language)
    fd.append('device', opts.device)
    fd.append('format', opts.format)
    fd.append('enable_diarization', 'false')
    if (opts.translateTo) {
      fd.append('translate_to', opts.translateTo)
    }

    try {
      const { promise } = api.uploadWithProgress(fd, (pct) => {
        store.setUploadPercent(pct)
        store.applyProgressData({
          message: pct < 100 ? `Uploading… ${pct}%` : 'Upload complete, starting processing…',
          percent: pct,
        })
      })
      const result = await promise
      // Upload done — transition to real task tracking
      store.setUploading(false)
      store.setTaskId(result.task_id)
      store.applyProgressData({
        status: 'queued',
        percent: 0,
        message: 'Processing started…',
      })
      localStorage.setItem('sg_currentTaskId', result.task_id)
    } catch (err) {
      store.setUploading(false)
      store.setError(err instanceof Error ? err.message : 'Upload failed')
    }
  }

  const activeTaskId = store.taskId
  const isProcessing = activeTaskId !== null && !store.isComplete && store.status !== 'cancelled' && store.status !== 'error'

  const tabs: Array<{ id: AppTab; label: string; sub: string }> = [
    { id: 'transcribe', label: 'Transcribe', sub: 'AI-powered' },
    { id: 'embed', label: 'Embed Subtitles', sub: 'Local files' },
  ]

  return (
    <div
      className="min-h-screen"
      style={{ background: 'var(--color-bg)', fontFamily: 'var(--font-family-sans)' }}
    >
      <ConnectionBanner />
      <AppHeader />

      {healthPanelOpen && (
        <HealthPanel
          health={health}
          onClose={() => setHealthPanelOpen(false)}
        />
      )}

      {/* Main layout */}
      <main className="max-w-5xl mx-auto px-4 py-6 lg:py-8 flex flex-col lg:flex-row gap-5 lg:gap-6 items-start">
        {/* Left column: input */}
        <div className="flex-1 min-w-0 w-full">
          <div
            className="rounded-xl overflow-hidden"
            style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            {/* Tab header */}
            <div
              className="flex items-center gap-0 px-1 pt-1"
              style={{ borderBottom: '1px solid var(--color-border)' }}
            >
              {tabs.map((tab) => {
                const isActive = appMode === tab.id
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setAppMode(tab.id)}
                    className="relative flex flex-col px-4 py-2.5 rounded-t-lg transition-colors"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      borderBottom: isActive ? '2px solid var(--color-primary)' : '2px solid transparent',
                    }}
                  >
                    <span
                      className="text-sm font-medium"
                      style={{ color: isActive ? 'var(--color-primary)' : 'var(--color-text-2)' }}
                    >
                      {tab.label}
                    </span>
                    <span
                      className="text-xs"
                      style={{ color: 'var(--color-text-3)', fontSize: '11px' }}
                    >
                      {tab.sub}
                    </span>
                  </button>
                )
              })}
            </div>

            {/* Tab content */}
            <div className="p-4 md:p-5">
              {appMode === 'transcribe' ? (
                isProcessing && activeTaskId ? (
                  <ProgressView taskId={activeTaskId} />
                ) : store.isComplete && activeTaskId ? (
                  <ProgressView taskId={activeTaskId} />
                ) : (
                  <TranscribeForm onUpload={handleUpload} />
                )
              ) : (
                <EmbedTab />
              )}
            </div>
          </div>
        </div>

        {/* Right column: output panel — full width on mobile, sticky sidebar on desktop */}
        <div
          className="w-full lg:flex-shrink-0 lg:w-[300px] lg:sticky"
          style={{ top: '68px' }}
        >
          <OutputPanel />
        </div>
      </main>

      {/* Task Queue */}
      <TaskQueuePanel />

      {/* Footer */}
      <footer
        className="text-center py-6 text-xs"
        style={{ color: 'var(--color-text-3)' }}
      >
        ↑ SubForge · Python 3.12 · FastAPI · faster-whisper (CTranslate2) · pyannote.audio · FFmpeg · React 19 · TypeScript · Tailwind CSS · Open Source
      </footer>
    </div>
  )
}
