export interface FileMetadata {
  filename: string
  duration: number
  format: string
  resolution: string | null
  size: number
  codec: string
  isVideo: boolean
}

export interface Segment {
  index: number
  start: number
  end: number
  text: string
  speaker?: string
}

export interface SearchResult {
  segmentIndex: number
  text: string
  matchStart: number
  matchEnd: number
}

export interface RecentProject {
  taskId: string
  filename: string
  createdAt: string // ISO 8601 string
  status: 'processing' | 'completed' | 'failed'
  duration: number | null
}

export type EditorPhase = 'idle' | 'uploading' | 'processing' | 'editing' | 'error'

export function formatTimecode(seconds: number): string {
  const s = Math.max(0, seconds)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = Math.floor(s % 60)
  return [h, m, sec].map(v => String(v).padStart(2, '0')).join(':')
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

export function formatDuration(seconds: number): string {
  const s = Math.max(0, seconds)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = Math.floor(s % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
  return `${m}:${String(sec).padStart(2, '0')}`
}

export function detectUploadType(files: File[]): 'transcribe' | 'combine' | 'edit-srt' | 'unknown' {
  const mediaExts = ['.mp4', '.mkv', '.avi', '.webm', '.mov', '.mp3', '.wav', '.flac', '.ogg', '.m4a']
  const subtitleExts = ['.srt', '.vtt']
  const hasMedia = files.some(f => mediaExts.some(e => f.name.toLowerCase().endsWith(e)))
  const hasSubtitle = files.some(f => subtitleExts.some(e => f.name.toLowerCase().endsWith(e)))
  if (hasMedia && hasSubtitle) return 'combine'
  if (hasMedia) return 'transcribe'
  if (hasSubtitle) return 'edit-srt'
  return 'unknown'
}
