// ── API types (hand-crafted from OpenAPI spec) ──

export interface SystemInfo {
  gpu_available: boolean
  gpu_name: string | null
  gpu_memory_gb: number | null
  recommended_device: 'cuda' | 'cpu'
  models: Record<string, ModelInfo>
  diarization_available: boolean
  ffmpeg_available: boolean
}

export interface ModelInfo {
  name: string
  parameters: string
  vram_required_gb: number | null
  speed: string
  accuracy: string
  recommended_for: string
  fits_gpu: boolean | null
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
  status: 'ok' | 'degraded' | 'error'
  uptime_sec: number
  cpu_percent?: number
  ram_percent?: number
  disk_percent?: number
  db_ok?: boolean
  alerts?: string[]
  load?: number
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
