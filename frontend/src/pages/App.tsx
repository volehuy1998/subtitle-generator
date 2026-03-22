import { useCallback, useEffect, useRef, useState } from 'react'
import { HealthPanel } from '@/components/system/HealthPanel'
import { TaskQueuePanel } from '@/components/system/TaskQueuePanel'
import { TranscribeForm } from '@/components/transcribe/TranscribeForm'
import { ProgressView } from '@/components/progress/ProgressView'
import { OutputPanel } from '@/components/output/OutputPanel'
import { TaskHistory } from '@/components/tasks/TaskHistory'
import { EmbedTab } from '@/components/embed/EmbedTab'
import { ConfirmationDialog } from '@/components/transcribe/ConfirmationDialog'
import { KeyboardShortcutsDialog } from '@/components/shortcuts/KeyboardShortcutsDialog'
import { useTaskStore } from '@/store/taskStore'
import { useUIStore } from '@/store/uiStore'
import { api } from '@/api/client'

type AppTab = 'transcribe' | 'embed'

export function App() {
  const { healthPanelOpen, setHealthPanelOpen, appMode, setAppMode, health } = useUIStore()
  const store = useTaskStore()

  // Phase Lumen: keyboard shortcuts dialog — Pixel (Sr. Frontend), Sprint L48
  const [shortcutsOpen, setShortcutsOpen] = useState(false)

  // Phase Lumen: completed tasks counter badge — Pixel (Sr. Frontend), Sprint L55
  const [completedCount, setCompletedCount] = useState(0)
  const prevIsComplete = useRef(false)

  // Phase Lumen: pending upload awaiting user confirmation
  const [pendingUpload, setPendingUpload] = useState<{
    file: File;
    opts: { device: string; model: string; language: string; format: string; translateTo?: string; modelLoaded: boolean; firstReadyModel: string | null };
  } | null>(null)

  // Track completed tasks when user is on Embed tab — Pixel (Sr. Frontend), Sprint L55
  useEffect(() => {
    if (store.isComplete && !prevIsComplete.current && appMode === 'embed') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setCompletedCount((c) => c + 1)
    }
    prevIsComplete.current = store.isComplete
  }, [store.isComplete, appMode])

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

  // Phase Lumen: user must confirm before transcription starts
  const handleFileSelected = (file: File, opts: { device: string; model: string; language: string; format: string; translateTo?: string; modelLoaded: boolean; firstReadyModel: string | null }) => {
    setPendingUpload({ file, opts })
  }

  const handleCancelUpload = () => {
    setPendingUpload(null)
  }

  const startUpload = async (file: File, opts: { device: string; model: string; language: string; format: string; translateTo?: string; modelLoaded?: boolean; firstReadyModel?: string | null }) => {
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

    const uploadStartTime = Date.now()
    try {
      const { promise } = api.uploadWithProgress(fd, (pct) => {
        store.setUploadPercent(pct)
        // Calculate upload ETA
        let etaText = ''
        if (pct > 0 && pct < 100) {
          const elapsed = (Date.now() - uploadStartTime) / 1000
          const speed = (pct / 100) / elapsed  // fraction per second
          if (speed > 0) {
            const remainingSec = Math.ceil(((100 - pct) / 100) / speed)
            etaText = remainingSec >= 60
              ? `~${Math.floor(remainingSec / 60)}m ${remainingSec % 60}s`
              : `~${remainingSec}s`
          }
        }
        store.setUploadEta(etaText)
        store.applyProgressData({
          message: pct < 100
            ? `Uploading… ${pct}%${etaText ? ` — ${etaText} remaining` : ''}`
            : 'Upload complete, starting processing…',
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
      // Increment session task counter — Pixel (Sr. Frontend), Sprint L50
      try {
        const count = parseInt(sessionStorage.getItem('sg_session_task_count') ?? '0', 10) || 0
        sessionStorage.setItem('sg_session_task_count', String(count + 1))
      } catch { /* sessionStorage unavailable */ }
    } catch (err) {
      store.setUploading(false)
      store.setError(err instanceof Error ? err.message : 'Upload failed')
    }
  }

  // Phase Lumen: global keyboard shortcuts — Pixel (Sr. Frontend), Sprint L16
  const handleKeyboard = useCallback((e: KeyboardEvent) => {
    // Don't trigger shortcuts when user is typing in form fields
    const tag = (e.target as HTMLElement).tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
    // Also skip if any modifier key is held (Ctrl+1 for browser tabs, etc.)
    if (e.metaKey || e.ctrlKey || e.altKey) return

    if (e.key === '1') {
      setAppMode('transcribe')
    } else if (e.key === '2') {
      setAppMode('embed')
    } else if (e.key === '?') {
      // Toggle keyboard shortcuts dialog — Pixel (Sr. Frontend), Sprint L48
      setShortcutsOpen((prev) => !prev)
    } else if (e.key === 'Escape') {
      // Close shortcuts dialog
      if (shortcutsOpen) {
        setShortcutsOpen(false)
        return
      }
      // Close pending upload confirmation dialog
      if (pendingUpload) {
        setPendingUpload(null)
      }
      // Close health panel
      if (healthPanelOpen) {
        setHealthPanelOpen(false)
      }
    }
  }, [pendingUpload, healthPanelOpen, shortcutsOpen, setAppMode, setHealthPanelOpen])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyboard)
    return () => window.removeEventListener('keydown', handleKeyboard)
  }, [handleKeyboard])

  const activeTaskId = store.taskId
  const isProcessing = activeTaskId !== null && !store.isComplete && store.status !== 'cancelled' && store.status !== 'error'

  const tabs: Array<{ id: AppTab; label: string; sub: string }> = [
    { id: 'transcribe', label: 'Transcribe', sub: 'AI-powered' },
    { id: 'embed', label: 'Embed Subtitles', sub: 'Local files' },
  ]

  return (
    <>
      {healthPanelOpen && (
        <HealthPanel
          health={health}
          onClose={() => setHealthPanelOpen(false)}
        />
      )}

      {/* Main layout */}
      <main id="main-content" className="max-w-6xl mx-auto px-3 sm:px-4 py-4 sm:py-6 lg:py-8 flex flex-col lg:flex-row gap-4 sm:gap-5 lg:gap-6 items-start">
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
              role="tablist"
              aria-label="Main sections"
              style={{ borderBottom: '1px solid var(--color-border)' }}
            >
              {tabs.map((tab) => {
                const isActive = appMode === tab.id
                return (
                  <button
                    key={tab.id}
                    type="button"
                    role="tab"
                    id={`tab-${tab.id}`}
                    aria-selected={isActive}
                    aria-controls={`tabpanel-${tab.id}`}
                    onClick={() => {
                      setAppMode(tab.id)
                      // Clear completed badge when switching to Transcribe — Sprint L55
                      if (tab.id === 'transcribe') setCompletedCount(0)
                    }}
                    className="relative flex flex-col px-3 sm:px-4 py-2 sm:py-2.5 rounded-t-lg transition-colors"
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
                      {/* Completed tasks badge — Sprint L55 */}
                      {tab.id === 'transcribe' && completedCount > 0 && (
                        <span
                          style={{
                            marginLeft: '6px',
                            background: 'var(--color-primary)',
                            color: 'white',
                            borderRadius: '9999px',
                            padding: '0 6px',
                            fontSize: '11px',
                            fontWeight: 600,
                            lineHeight: '18px',
                            display: 'inline-block',
                            minWidth: '18px',
                            textAlign: 'center',
                          }}
                        >
                          {completedCount}
                        </span>
                      )}
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
            <div key={appMode} className="p-4 md:p-5 animate-page-enter" role="tabpanel" id={`tabpanel-${appMode}`} aria-labelledby={`tab-${appMode}`}>
              {appMode === 'transcribe' ? (
                isProcessing && activeTaskId ? (
                  <ProgressView taskId={activeTaskId} />
                ) : store.isComplete && activeTaskId ? (
                  <ProgressView taskId={activeTaskId} />
                ) : (
                  <TranscribeForm onUpload={handleFileSelected} />
                )
              ) : (
                <EmbedTab />
              )}
            </div>
          </div>
        </div>

        {/* Right column: output panel + task history — full width on mobile, sticky sidebar on desktop */}
        <div
          className="w-full lg:flex-shrink-0 lg:w-[300px] lg:sticky flex flex-col gap-4"
          style={{ top: '68px' }}
        >
          <OutputPanel />
          <TaskHistory />
        </div>
      </main>

      {/* Task Queue */}
      <TaskQueuePanel />

      {/* Phase Lumen: Keyboard shortcuts dialog — Sprint L48 */}
      <KeyboardShortcutsDialog
        open={shortcutsOpen}
        onClose={() => setShortcutsOpen(false)}
      />

      {/* Phase Lumen: Confirmation dialog before transcription */}
      {pendingUpload && (
        <ConfirmationDialog
          file={pendingUpload.file}
          model={pendingUpload.opts.model}
          language={pendingUpload.opts.language}
          format={pendingUpload.opts.format}
          device={pendingUpload.opts.device}
          translateTo={pendingUpload.opts.translateTo}
          modelNotLoaded={!pendingUpload.opts.modelLoaded}
          readyModelName={pendingUpload.opts.firstReadyModel ?? undefined}
          onSwitchModel={(newModel) => {
            setPendingUpload((prev) => prev ? {
              ...prev,
              opts: { ...prev.opts, model: newModel, modelLoaded: true, firstReadyModel: null },
            } : null)
          }}
          onConfirm={() => {
            if (!pendingUpload) return
            const { file, opts } = pendingUpload
            setPendingUpload(null)
            startUpload(file, opts)
          }}
          onCancel={handleCancelUpload}
        />
      )}
    </>
  )
}
