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

  // Download
  downloadReady: boolean
  embedDownloadUrl: string | null

  // Warning
  warning: string | null
}

interface TaskActions {
  setTaskId: (id: string) => void
  applyProgressData: (data: Partial<TaskState>) => void
  addSegment: (seg: SegmentEvent) => void
  setLiveSegments: (segs: LiveSegment[]) => void
  setStep: (step: number) => void
  setComplete: (data: Partial<TaskState>) => void
  setCancelled: () => void
  setError: (msg: string) => void
  setPaused: () => void
  setResumed: () => void
  setWarning: (msg: string) => void
  setEmbedDownload: (url: string) => void
  reset: () => void
}

const initial: TaskState = {
  taskId: null, filename: null, fileSize: null,
  status: null, percent: 0, message: '', isPaused: false, isComplete: false, error: null,
  activeStep: -1, stepTimings: {},
  language: null, segments: 0, totalTimeSec: null, audioDuration: null,
  isVideo: false, speedFactor: null,
  liveSegments: [],
  downloadReady: false, embedDownloadUrl: null,
  warning: null,
}

export const useTaskStore = create<TaskState & TaskActions>((set) => ({
  ...initial,

  setTaskId: (id) => set({ taskId: id }),

  applyProgressData: (data) => set((s) => ({ ...s, ...data })),

  addSegment: (seg) => set((s) => ({
    liveSegments: [...s.liveSegments, seg],
  })),

  setLiveSegments: (segs) => set({ liveSegments: segs }),

  setStep: (step) => set({ activeStep: step }),

  setComplete: (data) => set((s) => ({
    ...s, ...data,
    status: 'done', percent: 100, isComplete: true, downloadReady: true,
  })),

  setCancelled: () => set({ status: 'cancelled', isPaused: false }),

  setError: (msg) => set({ status: 'error', error: msg }),

  setPaused: () => set({ isPaused: true, status: 'paused' }),

  setResumed: () => set({ isPaused: false, status: 'transcribing' }),

  setWarning: (msg) => set({ warning: msg }),

  setEmbedDownload: (url) => set({ embedDownloadUrl: url }),

  reset: () => {
    localStorage.removeItem('sg_currentTaskId')
    set(initial)
  },
}))
