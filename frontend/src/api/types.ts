// ── API types (hand-crafted from OpenAPI spec) ──

export interface SystemInfo {
  cuda_available: boolean
  gpu_name: string | null
  gpu_vram: number | null
  gpu_vram_free: number | null
  model_recommendations: Record<string, 'ok' | 'tight' | 'too_large'>
  auto_model: string
  diarization?: { available: boolean }
}

export interface LanguagesResponse {
  languages: Record<string, string>
}

export interface UploadResponse {
  task_id: string
  model_size: string
  language: string
}

export type TaskStatus =
  | 'queued'
  | 'uploading'
  | 'probing'
  | 'extracting'
  | 'loading_model'
  | 'transcribing'
  | 'formatting'
  | 'writing'
  | 'done'
  | 'error'
  | 'cancelled'
  | 'paused'
  | 'combining'
  | 'translating'

export interface TaskProgress {
  task_id: string
  status: TaskStatus
  percent: number
  message: string
  filename?: string
  file_size?: number
  audio_duration?: number
  model?: string
  language?: string
  device?: string
  segments?: number
  total_time_sec?: number
  step_timings?: StepTimings
  is_video?: boolean
  error?: string
  download_url?: string
  embed_download_url?: string
}

export interface StepTimings {
  upload?: number
  extract?: number
  transcribe?: number
  translate?: number
  finalize?: number
}

export interface SegmentEvent {
  start: number
  end: number
  text: string
  speaker?: string
}

export interface TaskListItem {
  task_id: string
  status: TaskStatus
  filename?: string
  percent: number
  position?: number
  created_at?: string
}

export interface TasksResponse {
  tasks: TaskListItem[]
}

export interface HealthStatus {
  status: 'ok' | 'healthy' | 'degraded' | 'error' | 'critical' | 'warning'
  uptime_sec: number
  cpu_percent?: number
  ram_percent?: number
  memory_percent?: number
  disk_percent?: number
  disk_free_gb?: number
  disk_ok?: boolean
  db_ok?: boolean
  alerts?: string[]
  load?: number
  gpu_available?: boolean
  gpu_name?: string | null
  gpu_vram_total?: number | null
  gpu_vram_used?: number | null
  gpu_vram_free?: number | null
}

export interface EmbedResult {
  message: string
  output?: string
  mode?: string
  download_url?: string
}

export interface CombineStatus {
  task_id: string
  status: TaskStatus
  percent: number
  message: string
  combined_video?: string
}

export interface SubtitleSegment {
  start: number
  end: number
  text: string
}

export interface SubtitlesResponse {
  task_id: string
  segments: SubtitleSegment[]
}

export interface TranslationPair {
  source: string
  source_name: string
  target: string
  target_name: string
  installed: boolean
  method?: string
}

export interface TranslationLanguagesResponse {
  pairs: TranslationPair[]
  count: number
}

// ── SSE event payloads ──
export type SSEEventType =
  | 'state'
  | 'progress'
  | 'step_change'
  | 'segment'
  | 'warning'
  | 'done'
  | 'embed_progress'
  | 'embed_done'
  | 'embed_error'
  | 'cancelled'
  | 'critical_abort'
  | 'paused'
  | 'resumed'
  | 'heartbeat'
  | 'translate_progress'
