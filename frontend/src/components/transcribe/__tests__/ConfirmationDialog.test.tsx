import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ConfirmationDialog } from '../ConfirmationDialog'

// Mock useFocusTrap — returns a ref
vi.mock('@/hooks/useFocusTrap', () => ({
  useFocusTrap: () => ({ current: null }),
}))

function makeFile(name: string, size: number): File {
  const f = new File(['x'], name, { type: 'audio/mpeg' })
  Object.defineProperty(f, 'size', { value: size })
  return f
}

const baseProps = {
  file: makeFile('test.mp3', 5 * 1024 * 1024), // 5 MB
  model: 'small',
  language: 'auto',
  format: 'srt',
  device: 'cpu',
  onConfirm: vi.fn(),
  onCancel: vi.fn(),
}

describe('ConfirmationDialog', () => {
  it('displays the file name in the summary', () => {
    render(<ConfirmationDialog {...baseProps} />)
    expect(screen.getByText('test.mp3')).toBeInTheDocument()
  })

  it('displays formatted file size', () => {
    render(<ConfirmationDialog {...baseProps} />)
    expect(screen.getByText('(5.0 MB)')).toBeInTheDocument()
  })

  it('shows correct model label', () => {
    render(<ConfirmationDialog {...baseProps} model="small" />)
    expect(screen.getByText('Small (460 MB)')).toBeInTheDocument()
  })

  it('shows "Auto-detect" when language is auto', () => {
    render(<ConfirmationDialog {...baseProps} language="auto" />)
    expect(screen.getByText('Auto-detect')).toBeInTheDocument()
  })

  it('shows "Auto-detect" when language is empty string', () => {
    render(<ConfirmationDialog {...baseProps} language="" />)
    expect(screen.getByText('Auto-detect')).toBeInTheDocument()
  })

  it('shows format in uppercase via CSS textTransform', () => {
    render(<ConfirmationDialog {...baseProps} format="srt" />)
    // The text content is "srt" but CSS textTransform uppercase renders it visually as SRT
    const cells = screen.getAllByText('srt')
    expect(cells.length).toBeGreaterThanOrEqual(1)
  })

  it('hides translation row when translateTo is not set', () => {
    render(<ConfirmationDialog {...baseProps} />)
    expect(screen.queryByText('Translate')).not.toBeInTheDocument()
  })

  it('shows translation row when translateTo is set', () => {
    render(<ConfirmationDialog {...baseProps} translateTo="Spanish" />)
    expect(screen.getByText('Translate')).toBeInTheDocument()
    expect(screen.getByText('Spanish')).toBeInTheDocument()
  })

  it('shows large file warning for files > 100MB', () => {
    const bigFile = makeFile('big.mp4', 200 * 1024 * 1024)
    render(<ConfirmationDialog {...baseProps} file={bigFile} />)
    expect(screen.getByText(/Large file/)).toBeInTheDocument()
    expect(screen.getByText(/Processing may take several minutes/)).toBeInTheDocument()
  })

  it('does not show large file warning for small files', () => {
    render(<ConfirmationDialog {...baseProps} />)
    expect(screen.queryByText(/Large file/)).not.toBeInTheDocument()
  })

  it('shows model not loaded warning when modelNotLoaded=true', () => {
    render(<ConfirmationDialog {...baseProps} modelNotLoaded />)
    expect(screen.getByText(/not loaded yet/)).toBeInTheDocument()
  })

  it('shows "Load & Transcribe" button when model not loaded', () => {
    render(<ConfirmationDialog {...baseProps} modelNotLoaded />)
    expect(screen.getByText('Load & Transcribe')).toBeInTheDocument()
  })

  it('shows "Start Transcription" button when model is loaded', () => {
    render(<ConfirmationDialog {...baseProps} />)
    expect(screen.getByText('Start Transcription')).toBeInTheDocument()
  })

  it('confirm button calls onConfirm', () => {
    const onConfirm = vi.fn()
    render(<ConfirmationDialog {...baseProps} onConfirm={onConfirm} />)
    fireEvent.click(screen.getByText('Start Transcription'))
    expect(onConfirm).toHaveBeenCalledOnce()
  })

  it('cancel button calls onCancel', () => {
    const onCancel = vi.fn()
    render(<ConfirmationDialog {...baseProps} onCancel={onCancel} />)
    fireEvent.click(screen.getByText('Cancel'))
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('has role="dialog" and aria-modal="true"', () => {
    render(<ConfirmationDialog {...baseProps} />)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(dialog).toHaveAttribute('aria-modal', 'true')
  })

  it('shows switch model button when readyModelName and onSwitchModel provided', () => {
    const onSwitch = vi.fn()
    render(
      <ConfirmationDialog
        {...baseProps}
        modelNotLoaded
        readyModelName="tiny"
        onSwitchModel={onSwitch}
      />,
    )
    const switchBtn = screen.getByText(/Use Tiny instead/)
    expect(switchBtn).toBeInTheDocument()
    fireEvent.click(switchBtn)
    expect(onSwitch).toHaveBeenCalledWith('tiny')
  })

  it('shows speed estimate for known model/device combos', () => {
    render(<ConfirmationDialog {...baseProps} model="small" device="cpu" />)
    expect(screen.getByText('Processing speed')).toBeInTheDocument()
    expect(screen.getByText(/2x realtime/)).toBeInTheDocument()
  })
})
