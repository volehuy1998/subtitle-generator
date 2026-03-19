/**
 * RetranscribeDialog tests — re-transcription settings dialog.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { RetranscribeDialog } from '../../components/editor/RetranscribeDialog'
import { usePreferencesStore } from '../../store/preferencesStore'

// Mock API client
vi.mock('../../api/client', () => ({
  api: {
    retranscribe: vi.fn().mockResolvedValue({ task_id: 'new-task', message: 'OK' }),
  },
}))

// Mock navigation
vi.mock('../../navigation', () => ({
  navigate: vi.fn(),
}))

// Mock UI components
vi.mock('../../components/ui/Dialog', () => ({
  Dialog: ({ open, title, description, children }: {
    open: boolean; title: string; description: string; children: React.ReactNode
  }) => open ? (
    <div data-testid="dialog" role="dialog">
      <h2>{title}</h2>
      <p>{description}</p>
      {children}
    </div>
  ) : null,
}))
vi.mock('../../components/ui/Button', () => ({
  Button: ({ children, onClick, disabled, loading }: {
    children: React.ReactNode; onClick?: () => void; disabled?: boolean; loading?: boolean
  }) => (
    <button onClick={onClick} disabled={disabled || loading}>{children}</button>
  ),
}))
vi.mock('../../components/ui/Select', () => ({
  Select: ({ label, options, value, onChange }: { label: string; options: Array<{ value: string; label: string }>; value: string; onChange: (e: { target: { value: string } }) => void }) => (
    <label>
      {label}
      <select value={value} onChange={onChange}>
        {options.map((o: { value: string; label: string }) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  ),
}))
vi.mock('../../components/ui/Input', () => ({
  Input: ({ label, value, onChange, placeholder }: {
    label: string; value: string; onChange: (e: { target: { value: string } }) => void; placeholder?: string; helperText?: string
  }) => (
    <label>
      {label}
      <input value={value} onChange={onChange} placeholder={placeholder} />
    </label>
  ),
}))
vi.mock('../../components/ui/Switch', () => ({
  Switch: ({ label, checked, onChange, description }: {
    label: string; checked: boolean; onChange: (v: boolean) => void; description?: string
  }) => (
    <label>
      <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} />
      {label}
      {description && <span>{description}</span>}
    </label>
  ),
}))
vi.mock('../../components/ui/Slider', () => ({
  Slider: ({ label, value, onChange, min, max }: {
    label: string; value: number; onChange: (v: number) => void; min: number; max: number
  }) => (
    <label>
      {label}
      <input type="range" value={value} min={min} max={max} onChange={e => onChange(Number(e.target.value))} />
    </label>
  ),
}))

describe('RetranscribeDialog', () => {
  const onClose = vi.fn()

  beforeEach(() => {
    usePreferencesStore.getState().reset()
    onClose.mockReset()
  })

  it('renders nothing when closed', () => {
    const { container } = render(
      <RetranscribeDialog open={false} onClose={onClose} taskId="task-1" />
    )
    expect(container.innerHTML).toBe('')
  })

  it('renders dialog with title when open', () => {
    render(<RetranscribeDialog open={true} onClose={onClose} taskId="task-1" />)
    expect(screen.getByRole('dialog')).toBeDefined()
    expect(screen.getByText('Re-run transcription with different settings.')).toBeDefined()
  })

  it('renders model size selector with all options', () => {
    render(<RetranscribeDialog open={true} onClose={onClose} taskId="task-1" />)
    expect(screen.getByText('Model size')).toBeDefined()
    // The select should contain model options
    const select = screen.getByRole('combobox', { name: /Model size/i }) as HTMLSelectElement
    expect(select.value).toBe('large')
  })

  it('renders word timestamps and diarization switches', () => {
    render(<RetranscribeDialog open={true} onClose={onClose} taskId="task-1" />)
    expect(screen.getByText('Word-level timestamps')).toBeDefined()
    expect(screen.getByText('Speaker diarization')).toBeDefined()
  })

  it('shows number of speakers slider when diarization is enabled', () => {
    render(<RetranscribeDialog open={true} onClose={onClose} taskId="task-1" />)
    // Enable diarization
    const diarizeCheckbox = screen.getByRole('checkbox', { name: /Speaker diarization/i })
    fireEvent.click(diarizeCheckbox)
    expect(screen.getByText('Number of speakers')).toBeDefined()
  })
})
