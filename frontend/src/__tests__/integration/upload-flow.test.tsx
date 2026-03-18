/**
 * Integration: Upload flow — LandingPage renders, shows upload zone and empty state.
 *
 * — Scout (QA Lead), Task 41
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LandingPage } from '../../pages/LandingPage'
import { useEditorStore } from '../../store/editorStore'
import { useRecentProjectsStore } from '../../store/recentProjectsStore'
import { TooltipProvider } from '../../components/ui/Tooltip'

// Mock the API
vi.mock('../../api/client', () => ({
  api: {
    duplicates: vi.fn().mockResolvedValue({ duplicates: [] }),
    uploadWithProgress: vi.fn().mockReturnValue({
      promise: Promise.resolve({ task_id: 'task-integration-1' }),
      abort: vi.fn(),
    }),
    combineStart: vi.fn().mockResolvedValue({ task_id: 'task-combine-1' }),
    progress: vi.fn().mockResolvedValue({ status: 'processing' }),
  },
}))

// Mock navigate
vi.mock('../../navigation', () => ({
  navigate: vi.fn(),
  matchRoute: vi.fn().mockReturnValue({ page: 'landing', params: {} }),
}))

function renderWithProviders(ui: React.ReactElement) {
  return render(<TooltipProvider>{ui}</TooltipProvider>)
}

describe('Upload flow', () => {
  beforeEach(() => {
    useEditorStore.getState().reset()
    useRecentProjectsStore.getState().clearAll()
    vi.clearAllMocks()
  })

  it('renders LandingPage with upload zone', () => {
    renderWithProviders(<LandingPage />)
    expect(screen.getByText(/drop your file/i)).toBeDefined()
  })

  it('shows empty state when no projects', () => {
    renderWithProviders(<LandingPage />)
    expect(screen.getByText(/no recent projects/i)).toBeDefined()
  })

  it('renders upload zone button role', () => {
    renderWithProviders(<LandingPage />)
    expect(screen.getByRole('button', { name: /upload file/i })).toBeDefined()
  })

  it('shows accepted file formats', () => {
    renderWithProviders(<LandingPage />)
    expect(screen.getByText(/mp4.*mkv/i)).toBeDefined()
  })
})
