import { create } from 'zustand'
import type { Segment, SearchResult, EditorPhase, FileMetadata } from '../types'

interface ProgressData {
  percent: number
  segmentCount: number
  estimatedSegments: number
  eta: number | null
  elapsed: number
  speed: number | null
  pipelineStep: string
  message: string
}

interface CompleteData {
  segments: Segment[]
  language: string | null
  modelUsed: string | null
  timings: Record<string, number>
  isVideo: boolean
}

interface EditorState {
  taskId: string | null
  fileMetadata: FileMetadata | null
  phase: EditorPhase
  uploadPercent: number
  progress: ProgressData | null
  liveSegments: Segment[]
  segments: Segment[]
  language: string | null
  modelUsed: string | null
  timings: Record<string, number>
  isVideo: boolean
  errorMessage: string | null
  searchQuery: string
  searchResults: SearchResult[]
  editingSegmentIndex: number | null

  setTaskId: (id: string) => void
  setFileMetadata: (meta: FileMetadata) => void
  setPhase: (phase: EditorPhase) => void
  setUploadPercent: (percent: number) => void
  updateProgress: (data: ProgressData) => void
  addLiveSegment: (segment: Segment) => void
  setComplete: (data: CompleteData) => void
  setError: (message: string) => void
  updateSegment: (index: number, text: string) => void
  setSearchQuery: (query: string) => void
  setSearchResults: (results: SearchResult[]) => void
  setEditingSegment: (index: number | null) => void
  reset: () => void
}

const initial = {
  taskId: null as string | null,
  fileMetadata: null as FileMetadata | null,
  phase: 'idle' as EditorPhase,
  uploadPercent: 0,
  progress: null as ProgressData | null,
  liveSegments: [] as Segment[],
  segments: [] as Segment[],
  language: null as string | null,
  modelUsed: null as string | null,
  timings: {} as Record<string, number>,
  isVideo: false,
  errorMessage: null as string | null,
  searchQuery: '',
  searchResults: [] as SearchResult[],
  editingSegmentIndex: null as number | null,
}

export const useEditorStore = create<EditorState>((set) => ({
  ...initial,

  setTaskId: (id) => set({ taskId: id }),
  setFileMetadata: (meta) => set({ fileMetadata: meta }),
  setPhase: (phase) => set({ phase }),
  setUploadPercent: (percent) => set({ uploadPercent: percent }),

  updateProgress: (data) => set({ progress: data, phase: 'processing' }),

  addLiveSegment: (segment) => set(s => ({
    liveSegments: [...s.liveSegments, segment],
  })),

  setComplete: (data) => set({
    phase: 'editing',
    segments: data.segments,
    language: data.language,
    modelUsed: data.modelUsed,
    timings: data.timings,
    isVideo: data.isVideo,
    liveSegments: [],
    progress: null,
  }),

  setError: (message) => set({
    phase: 'error',
    errorMessage: message,
    progress: null,
  }),

  updateSegment: (index, text) => set(s => ({
    segments: s.segments.map((seg, i) => i === index ? { ...seg, text } : seg),
  })),

  setSearchQuery: (query) => set({ searchQuery: query }),
  setSearchResults: (results) => set({ searchResults: results }),
  setEditingSegment: (index) => set({ editingSegmentIndex: index }),

  reset: () => set(initial),
}))
