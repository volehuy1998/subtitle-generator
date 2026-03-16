// ── Typed API client ──
import type {
  SystemInfo, LanguagesResponse, UploadResponse,
  TaskProgress, TasksResponse, HealthStatus,
  EmbedResult, CombineStatus, SubtitlesResponse,
  TranslationLanguagesResponse, ModelPreloadStatus,
} from './types'

const json = async <T>(res: Response): Promise<T> => {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error((err as { detail?: string }).detail ?? res.statusText)
  }
  return res.json() as Promise<T>
}

export const api = {
  systemInfo: () =>
    fetch('/system-info').then(r => json<SystemInfo>(r)),

  languages: () =>
    fetch('/languages').then(r => json<LanguagesResponse>(r)),

  upload: (fd: FormData) =>
    fetch('/upload', { method: 'POST', body: fd }).then(r => json<UploadResponse>(r)),

  /** Upload with XHR for progress tracking. Returns a promise + abort handle. */
  uploadWithProgress: (fd: FormData, onProgress: (percent: number) => void) => {
    let rejectFn: (reason: Error) => void
    const promise = new Promise<UploadResponse>((resolve, reject) => {
      rejectFn = reject
      const xhr = new XMLHttpRequest()
      xhr.open('POST', '/upload')

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100))
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText))
        } else {
          try {
            const err = JSON.parse(xhr.responseText)
            reject(new Error(err.detail ?? xhr.statusText))
          } catch {
            reject(new Error(xhr.statusText))
          }
        }
      }

      xhr.onerror = () => reject(new Error('Network error'))
      xhr.onabort = () => reject(new Error('Upload cancelled'))
      xhr.send(fd)
    })
    return { promise, abort: () => rejectFn?.(new Error('Upload cancelled')) }
  },

  progress: (taskId: string) =>
    fetch(`/progress/${taskId}`).then(r => json<TaskProgress>(r)),

  tasks: () =>
    fetch('/tasks').then(r => json<TasksResponse>(r)),

  cancel: (taskId: string) =>
    fetch(`/cancel/${taskId}`, { method: 'POST' }).then(r => json<{ message: string }>(r)),

  pause: (taskId: string) =>
    fetch(`/pause/${taskId}`, { method: 'POST' }).then(r => json<{ message: string }>(r)),

  resume: (taskId: string) =>
    fetch(`/resume/${taskId}`, { method: 'POST' }).then(r => json<{ message: string }>(r)),

  health: () =>
    fetch('/api/status').then(r => json<HealthStatus>(r)),

  embedQuick: (taskId: string, fd: FormData) =>
    fetch(`/embed/${taskId}/quick`, { method: 'POST', body: fd }).then(r => json<EmbedResult>(r)),

  combineStart: (fd: FormData) =>
    fetch('/combine', { method: 'POST', body: fd }).then(r => json<{ task_id: string; message: string }>(r)),

  combineStatus: (taskId: string) =>
    fetch(`/combine/status/${taskId}`).then(r => json<CombineStatus>(r)),

  downloadUrl: (taskId: string, format: 'srt' | 'vtt' | 'json') =>
    `/download/${taskId}?format=${format}`,

  downloadAllUrl: (taskId: string) =>
    `/download/${taskId}/all`,

  embedDownloadUrl: (taskId: string) =>
    `/embed/download/${taskId}`,

  combineDownloadUrl: (taskId: string) =>
    `/combine/download/${taskId}`,

  subtitles: (taskId: string) =>
    fetch(`/subtitles/${taskId}`).then(r => json<SubtitlesResponse>(r)),

  translationLanguages: () =>
    fetch('/translation/languages').then(r => json<TranslationLanguagesResponse>(r)),

  modelStatus: () =>
    fetch('/api/model-status').then(r => json<ModelPreloadStatus>(r)),

  tasksBySession: () =>
    fetch('/tasks?session_only=true').then(r => json<TasksResponse>(r)),

  deleteTask: (taskId: string) =>
    fetch(`/tasks/${taskId}`, { method: 'DELETE' }).then(r => json<{ message: string }>(r)),
}
