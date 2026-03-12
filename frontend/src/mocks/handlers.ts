/**
 * MSW request handlers — realistic stubs for every API endpoint.
 *
 * These are used in two places:
 *   1. Vitest (node) — via src/mocks/server.ts loaded in test setup
 *   2. Dev browser — via src/mocks/browser.ts when VITE_MOCK=true
 *
 * Keep handler shapes in sync with app/schemas.py.
 * When the backend adds a new endpoint, add a handler here so FE devs
 * can work offline without waiting for the BE to stabilise.
 */

import { http, HttpResponse } from 'msw'
import type {
  SystemInfo, LanguagesResponse, UploadResponse,
  TaskProgress, HealthStatus, TasksResponse, SubtitlesResponse,
} from '@/api/types'

// Stable mock task id used across handlers so chained calls are consistent
export const MOCK_TASK_ID = 'mock-task-00000000-0000-0000-0000-000000000000'

// ── System ────────────────────────────────────────────────────────────────────

export const handlers = [
  http.get('/system-info', () =>
    HttpResponse.json<SystemInfo>({
      cuda_available: false,
      gpu_name: null,
      gpu_vram: null,
      gpu_vram_free: null,
      model_recommendations: {
        tiny: 'ok', base: 'ok', small: 'ok', medium: 'ok', large: 'too_large',
      },
      auto_model: 'small',
      diarization: { available: false },
    })
  ),

  http.get('/languages', () =>
    HttpResponse.json<LanguagesResponse>({
      languages: {
        auto: 'Auto-detect',
        en: 'English',
        fr: 'French',
        de: 'German',
        es: 'Spanish',
        ja: 'Japanese',
        zh: 'Chinese',
      },
    })
  ),

  http.get('/health', () =>
    HttpResponse.json({ status: 'healthy', uptime_sec: 3600 })
  ),

  http.get('/ready', () =>
    HttpResponse.json({ status: 'ready', checks: {}, uptime_sec: 3600 })
  ),

  http.get('/api/status', () =>
    HttpResponse.json<HealthStatus>({
      status: 'healthy',
      uptime_sec: 3600,
      cpu_percent: 12,
      memory_percent: 45,
      disk_free_gb: 32,
      db_ok: true,
      alerts: [],
      gpu_available: false,
      gpu_name: null,
    })
  ),

  http.get('/api/capabilities', () =>
    HttpResponse.json({
      ffmpeg: true,
      ffprobe: true,
      features: {
        transcribe_audio: true,
        transcribe_video: true,
        combine: true,
        embed_soft: true,
        embed_hard: true,
        media_probe: true,
      },
      accepted_extensions: ['.mp4', '.mkv', '.mp3', '.wav', '.flac'],
    })
  ),

  // ── Upload & progress ──────────────────────────────────────────────────────

  http.post('/upload', async () => {
    await delay(150)
    return HttpResponse.json<UploadResponse>({
      task_id: MOCK_TASK_ID,
      model_size: 'small',
      language: 'auto',
      word_timestamps: false,
      diarize: false,
    })
  }),

  http.get('/progress/:taskId', ({ params }) =>
    HttpResponse.json<TaskProgress>({
      task_id: params.taskId as string,
      status: 'done',
      percent: 100,
      message: 'Transcription complete',
      filename: 'sample.mp3',
      segments: 12,
      total_time_sec: 4.2,
      download_url: `/download/${params.taskId}?format=srt`,
      step_timings: { upload: 0.3, extract: 0.5, transcribe: 3.1, finalize: 0.3 },
    })
  ),

  http.get('/tasks', () =>
    HttpResponse.json<TasksResponse>({ tasks: [] })
  ),

  // ── Task control ──────────────────────────────────────────────────────────

  http.post('/cancel/:taskId', () =>
    HttpResponse.json({ message: 'Task cancelled' })
  ),

  http.post('/pause/:taskId', () =>
    HttpResponse.json({ message: 'Task paused' })
  ),

  http.post('/resume/:taskId', () =>
    HttpResponse.json({ message: 'Task resumed' })
  ),

  // ── Subtitles ─────────────────────────────────────────────────────────────

  http.get('/subtitles/:taskId', ({ params }) =>
    HttpResponse.json<SubtitlesResponse>({
      task_id: params.taskId as string,
      segments: [
        { start: 0.0, end: 2.5, text: 'Hello, this is a mock subtitle.' },
        { start: 2.5, end: 5.0, text: 'Generated for offline testing.' },
        { start: 5.0, end: 7.8, text: 'Add more segments in src/mocks/handlers.ts.' },
      ],
    })
  ),

  // ── Embed ─────────────────────────────────────────────────────────────────

  http.post('/embed/:taskId/quick', ({ params }) =>
    HttpResponse.json({
      message: 'Embedding complete',
      mode: 'soft',
      download_url: `/embed/download/${params.taskId}`,
    })
  ),

  // ── Combine ───────────────────────────────────────────────────────────────

  http.post('/combine', async () => {
    await delay(100)
    return HttpResponse.json({ task_id: MOCK_TASK_ID, message: 'Combine started' })
  }),

  http.get('/combine/status/:taskId', ({ params }) =>
    HttpResponse.json({
      task_id: params.taskId,
      status: 'done',
      percent: 100,
      message: 'Combine complete',
      combined_video: `/combine/download/${params.taskId}`,
    })
  ),
]

// ── Helpers ───────────────────────────────────────────────────────────────────

function delay(ms: number) {
  return new Promise(r => setTimeout(r, ms))
}
