/**
 * LandingPage — Drop, See, Refine redesign entry point.
 * Users drop a file here; the page handles upload, progress, and navigation to the editor.
 *
 * — Pixel (Senior Frontend Engineer)
 */
import { useState, useEffect } from 'react'
import { AppShell } from '../components/layout/AppShell'
import { UploadZone } from '../components/landing/UploadZone'
import { UploadProgress } from '../components/landing/UploadProgress'
import { ProjectGrid } from '../components/landing/ProjectGrid'
import { AdvancedUploadOptions } from '../components/editor/AdvancedUploadOptions'
import type { UploadOptions } from '../components/editor/AdvancedUploadOptions'
import { Card } from '../components/ui/Card'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { useEditorStore } from '../store/editorStore'
import { useRecentProjectsStore } from '../store/recentProjectsStore'
import { usePreferencesStore } from '../store/preferencesStore'
import { useToastStore } from '../store/toastStore'
import { navigate } from '../navigation'
import { api } from '../api/client'

export function LandingPage() {
  const [uploading, setUploading] = useState(false)
  const [uploadPercent, setUploadPercent] = useState(0)
  const [uploadFilename, setUploadFilename] = useState('')
  const [duplicateDialogOpen, setDuplicateDialogOpen] = useState(false)
  const [duplicateResolve, setDuplicateResolve] = useState<((v: boolean) => void) | null>(null)
  const reset = useEditorStore(s => s.reset)
  const addProject = useRecentProjectsStore(s => s.addProject)
  const projects = useRecentProjectsStore(s => s.projects)
  const updateProject = useRecentProjectsStore(s => s.updateProject)
  const removeProject = useRecentProjectsStore(s => s.removeProject)
  const addToast = useToastStore(s => s.addToast)
  const prefs = usePreferencesStore()
  const [uploadOptions, setUploadOptions] = useState<UploadOptions>({
    model: prefs.defaultModel,
    language: prefs.defaultLanguage,
    diarize: prefs.diarizeByDefault,
    numSpeakers: prefs.numSpeakers,
    wordTimestamps: prefs.wordTimestamps,
    initialPrompt: prefs.initialPrompt,
    translateToEnglish: false,
  })

  // Validate recent projects on mount — stagger calls 100ms apart, max 3 concurrent
  useEffect(() => {
    if (projects.length === 0) return

    const BATCH_SIZE = 3
    const DELAY_MS = 100

    const timers: ReturnType<typeof setTimeout>[] = []

    projects.forEach((project, index) => {
      // Only validate processing ones (completed/failed are stable)
      if (project.status !== 'processing') return

      const delay = Math.floor(index / BATCH_SIZE) * DELAY_MS
      const timer = setTimeout(() => {
        api.progress(project.taskId).then(data => {
          if (data.status === 'done') {
            updateProject(project.taskId, { status: 'completed' })
          } else if (data.status === 'error' || data.status === 'cancelled') {
            updateProject(project.taskId, { status: 'failed' })
          }
        }).catch((err: unknown) => {
          // 404 means task was deleted
          if (err instanceof Error && err.message.includes('404')) {
            removeProject(project.taskId)
          }
        })
      }, delay)

      timers.push(timer)
    })

    return () => {
      timers.forEach(t => clearTimeout(t))
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleUpload = async (files: File | File[], type: string) => {
    reset()

    if (type === 'edit-srt') {
      // Client-side SRT editing — navigate to editor with local file
      navigate('/editor/local')
      return
    }

    const fileArray = Array.isArray(files) ? files : [files]
    const file = fileArray[0]
    setUploading(true)
    setUploadFilename(file.name)
    setUploadPercent(0)

    try {
      // Check for duplicates
      const dupeResult = await api.duplicates(file.name, file.size)
      if (dupeResult.duplicates_found) {
        const proceed = await new Promise<boolean>(resolve => {
          setDuplicateDialogOpen(true)
          setDuplicateResolve(() => resolve)
        })
        if (!proceed) {
          setUploading(false)
          return
        }
      }

      // Build FormData
      const fd = new FormData()

      let result: { task_id: string }

      if (type === 'combine') {
        const videoFile = fileArray.find(f => !f.name.match(/\.(srt|vtt)$/i))!
        const subFile = fileArray.find(f => f.name.match(/\.(srt|vtt)$/i))!
        fd.append('video', videoFile)
        fd.append('subtitle', subFile)
        result = await api.combineStart(fd)
      } else {
        fd.append('file', file)
        // Append advanced upload options
        if (uploadOptions.model !== 'auto') fd.append('model', uploadOptions.model)
        if (uploadOptions.language !== 'auto') fd.append('language', uploadOptions.language)
        if (uploadOptions.diarize) fd.append('diarize', 'true')
        if (uploadOptions.wordTimestamps) fd.append('word_timestamps', 'true')
        if (uploadOptions.initialPrompt) fd.append('initial_prompt', uploadOptions.initialPrompt)
        if (uploadOptions.translateToEnglish) fd.append('translate', 'true')
        const { promise } = api.uploadWithProgress(fd, setUploadPercent)
        result = await promise
      }

      addProject({
        taskId: result.task_id,
        filename: file.name,
        createdAt: new Date().toISOString(),
        status: 'processing',
        duration: null,
      })

      setUploading(false)
      navigate(`/editor/${result.task_id}`)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Upload failed'
      addToast({ type: 'error', title: 'Upload failed', description: message })
      setUploading(false)
    }
  }

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto py-8 px-4">
        <Card shadow padding="lg" className="mb-8">
          {uploading ? (
            <UploadProgress filename={uploadFilename} percent={uploadPercent} />
          ) : (
            <>
              <UploadZone
                onUpload={handleUpload}
                onError={(msg) => addToast({ type: 'error', title: 'Error', description: msg })}
              />
              <AdvancedUploadOptions
                options={uploadOptions}
                onChange={setUploadOptions}
              />
            </>
          )}
        </Card>
        <ProjectGrid />
      </div>
      <ConfirmDialog
        open={duplicateDialogOpen}
        title="Duplicate detected"
        description="A similar file has already been processed. Upload anyway?"
        confirmLabel="Upload anyway"
        cancelLabel="Cancel"
        onConfirm={() => { setDuplicateDialogOpen(false); duplicateResolve?.(true) }}
        onClose={() => { setDuplicateDialogOpen(false); duplicateResolve?.(false) }}
      />
    </AppShell>
  )
}
