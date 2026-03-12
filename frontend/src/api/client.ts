// ── Typed API client ──
import type {
  SystemInfo, LanguagesResponse, UploadResponse,
  TaskProgress, TasksResponse, HealthStatus,
  EmbedResult, CombineStatus, SubtitlesResponse,
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

  embedDownloadUrl: (taskId: string) =>
    `/embed/download/${taskId}`,

  combineDownloadUrl: (taskId: string) =>
    `/combine/download/${taskId}`,

  subtitles: (taskId: string) =>
    fetch(`/subtitles/${taskId}`).then(r => json<SubtitlesResponse>(r)),
}
