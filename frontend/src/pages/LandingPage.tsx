/**
 * LandingPage — Drop, See, Refine redesign entry point.
 * Users drop a file here; the page handles upload, progress, and navigation to the editor.
 *
 * — Pixel (Senior Frontend Engineer)
 */
import { useState } from 'react'
import { AppShell } from '../components/layout/AppShell'
import { UploadZone } from '../components/landing/UploadZone'
import { UploadProgress } from '../components/landing/UploadProgress'
import { ProjectGrid } from '../components/landing/ProjectGrid'
import { Card } from '../components/ui/Card'
import { useEditorStore } from '../store/editorStore'
import { useRecentProjectsStore } from '../store/recentProjectsStore'
import { useToastStore } from '../store/toastStore'
import { navigate } from '../navigation'
import { api } from '../api/client'

export function LandingPage() {
  const [uploading, setUploading] = useState(false)
  const [uploadPercent, setUploadPercent] = useState(0)
  const [uploadFilename, setUploadFilename] = useState('')
  const reset = useEditorStore(s => s.reset)
  const addProject = useRecentProjectsStore(s => s.addProject)
  const addToast = useToastStore(s => s.addToast)

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
      if (dupeResult.duplicates.length > 0) {
        // TODO: show duplicate dialog (Task 40)
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
            <UploadZone
              onUpload={handleUpload}
              onError={(msg) => addToast({ type: 'error', title: 'Error', description: msg })}
            />
          )}
        </Card>
        <ProjectGrid />
      </div>
    </AppShell>
  )
}
