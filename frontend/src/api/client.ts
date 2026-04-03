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

// ── Stale-while-revalidate cache ──
interface CacheEntry<T> {
  data: T
  ts: number
}

/**
 * Return cached data immediately when fresh, or serve stale + revalidate in background.
 * Falls back to a live fetch when no cache exists.
 */
export async function cachedFetch<T>(key: string, fetcher: () => Promise<T>, maxAgeMs: number): Promise<T> {
  try {
    const raw = localStorage.getItem(key)
    if (raw) {
      const entry: CacheEntry<T> = JSON.parse(raw)
      if (Date.now() - entry.ts < maxAgeMs) {
        return entry.data
      }
      // Stale — return cached value but revalidate in background
      fetcher()
        .then((fresh) => localStorage.setItem(key, JSON.stringify({ data: fresh, ts: Date.now() })))
        .catch(() => { /* background revalidation failed, keep stale */ })
      return entry.data
    }
  } catch {
    // Corrupt cache entry — fall through to live fetch
  }

  const data = await fetcher()
  try {
    localStorage.setItem(key, JSON.stringify({ data, ts: Date.now() }))
  } catch {
    // localStorage full or unavailable
  }
  return data
}

const CACHE_5_MIN = 5 * 60 * 1000

export const api = {
  systemInfo: () =>
    cachedFetch<SystemInfo>('sg_cache_systemInfo', () => fetch('/system-info').then(r => json<SystemInfo>(r)), CACHE_5_MIN),

  languages: () =>
    cachedFetch<LanguagesResponse>('sg_cache_languages', () => fetch('/languages').then(r => json<LanguagesResponse>(r)), CACHE_5_MIN),

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
    cachedFetch<ModelPreloadStatus>(
      'sg_cache_modelStatus',
      () => fetch('/api/model-status').then(r => json<{ preload: ModelPreloadStatus }>(r)).then(d => d.preload),
      CACHE_5_MIN,
    ),

  tasksBySession: () =>
    fetch('/tasks?session_only=true').then(r => json<TasksResponse>(r)),

  deleteTask: (taskId: string) =>
    fetch(`/tasks/${taskId}`, { method: 'DELETE' }).then(r => json<{ message: string }>(r)),

  preview: (taskId: string, limit = 50) =>
    fetch(`/preview/${taskId}?limit=${limit}`).then(r => json<{
      task_id: string
      total_segments: number
      preview_limit: number
      segments: Array<{ start: number; end: number; text: string }>
    }>(r)),
}
