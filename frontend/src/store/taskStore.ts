import { create } from 'zustand'
import type { TaskStatus, SegmentEvent, StepTimings } from '@/api/types'

export interface LiveSegment {
  start: number
  end: number
  text: string
  speaker?: string
}

export interface TaskState {
  // Identity
  taskId: string | null
  filename: string | null
  fileSize: number | null

  // Status
  status: TaskStatus | null
  percent: number
  message: string
  isPaused: boolean
  isPauseRequesting: boolean
  isCancelRequesting: boolean
  isComplete: boolean
  error: string | null

  // Pipeline steps (0=upload,1=extract,2=transcribe,3=done)
  activeStep: number
  stepTimings: StepTimings

  // Metadata (populated on done)
  language: string | null
  segments: number
  totalTimeSec: number | null
  audioDuration: number | null
  isVideo: boolean
  speedFactor: number | null

  // Live preview
  liveSegments: LiveSegment[]

  // Translation
  translatedTo: string | null

  // Upload tracking
  isUploading: boolean
  uploadPercent: number

  // Download
  downloadReady: boolean
  embedDownloadUrl: string | null

  // Warning
  warning: string | null

  // SSE transcription progress fields (populated by applyProgressData)
  processed_sec?: number
  total_sec?: number
  speed_x?: number
  eta?: string
  elapsed?: string

  // Phase Lumen: liveness tracking
  lastEventTime: number
}

interface TaskActions {
  setTaskId: (id: string) => void
  setUploading: (uploading: boolean, percent?: number) => void
  setUploadPercent: (percent: number) => void
  applyProgressData: (data: Partial<TaskState>) => void
  addSegment: (seg: SegmentEvent) => void
  setLiveSegments: (segs: LiveSegment[]) => void
  setStep: (step: number) => void
  setComplete: (data: Partial<TaskState>) => void
  setCancelled: () => void
  setError: (msg: string) => void
  setPaused: () => void
  setResumed: () => void
  setPauseRequesting: (v: boolean) => void
  setCancelRequesting: (v: boolean) => void
  setWarning: (msg: string) => void
  setEmbedDownload: (url: string) => void
  reset: () => void
}

const initial: TaskState = {
  taskId: null, filename: null, fileSize: null,
  status: null, percent: 0, message: '', isPaused: false, isPauseRequesting: false, isCancelRequesting: false, isComplete: false, error: null, isUploading: false, uploadPercent: 0,
  activeStep: -1, stepTimings: {},
  language: null, segments: 0, totalTimeSec: null, audioDuration: null,
  isVideo: false, speedFactor: null, translatedTo: null,
  liveSegments: [],
  downloadReady: false, embedDownloadUrl: null,
  warning: null,
  processed_sec: undefined, total_sec: undefined, speed_x: undefined, eta: undefined, elapsed: undefined,
  lastEventTime: Date.now(),
}

export const useTaskStore = create<TaskState & TaskActions>((set) => ({
  ...initial,

  setTaskId: (id) => set({ taskId: id }),

  setUploading: (uploading, percent) => set({ isUploading: uploading, uploadPercent: percent ?? 0 }),

  setUploadPercent: (percent) => set({ uploadPercent: percent }),

  applyProgressData: (data) => set((s) => ({ ...s, ...data, lastEventTime: Date.now() })),

  addSegment: (seg) => set((s) => ({
    liveSegments: [...s.liveSegments, seg],
  })),

  setLiveSegments: (segs) => set({ liveSegments: segs }),

  setStep: (step) => set({ activeStep: step }),

  setComplete: (data) => set((s) => ({
    ...s, ...data,
    status: 'done', percent: 100, isComplete: true, downloadReady: true,
    translatedTo: (data as Record<string, unknown>).translated_to as string ?? s.translatedTo,
  })),

  setCancelled: () => set({ status: 'cancelled', isPaused: false, isPauseRequesting: false, isCancelRequesting: false }),

  setError: (msg) => set({ status: 'error', error: msg }),

  setPaused: () => set({ isPaused: true, isPauseRequesting: false, status: 'paused' }),

  setResumed: () => set({ isPaused: false, isPauseRequesting: false, status: 'transcribing' }),

  setPauseRequesting: (v) => set({ isPauseRequesting: v }),

  setCancelRequesting: (v) => set({ isCancelRequesting: v }),

  setWarning: (msg) => set({ warning: msg }),

  setEmbedDownload: (url) => set({ embedDownloadUrl: url }),

  reset: () => {
    localStorage.removeItem('sg_currentTaskId')
    set(initial)
  },
}))
