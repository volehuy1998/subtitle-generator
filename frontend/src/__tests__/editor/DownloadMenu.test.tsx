import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DownloadMenu } from '../../components/editor/DownloadMenu'
import { usePreferencesStore } from '../../store/preferencesStore'

describe('DownloadMenu', () => {
  beforeEach(() => {
    usePreferencesStore.getState().reset()
  })

  it('renders download button', () => {
    render(<DownloadMenu taskId="abc-123" />)
    expect(screen.getByText('Download')).toBeDefined()
  })

  it('opens menu on click and shows format options', () => {
    render(<DownloadMenu taskId="abc-123" />)
    fireEvent.click(screen.getByText('Download'))
    expect(screen.getByRole('menu')).toBeDefined()
    expect(screen.getByText('SRT')).toBeDefined()
    expect(screen.getByText('VTT')).toBeDefined()
    expect(screen.getByText('JSON')).toBeDefined()
  })

  it('builds correct download URLs with taskId and maxChars', () => {
    render(<DownloadMenu taskId="task-42" />)
    fireEvent.click(screen.getByText('Download'))
    const srtLink = screen.getByText('SRT').closest('a')
    expect(srtLink?.getAttribute('href')).toBe('/download/task-42?format=srt&max_line_chars=42')
    expect(srtLink?.hasAttribute('download')).toBe(true)
  })

  it('updates maxChars input and reflects in URLs', () => {
    render(<DownloadMenu taskId="task-42" />)
    fireEvent.click(screen.getByText('Download'))
    const input = screen.getByDisplayValue('42')
    fireEvent.change(input, { target: { value: '60' } })
    const vttLink = screen.getByText('VTT').closest('a')
    expect(vttLink?.getAttribute('href')).toBe('/download/task-42?format=vtt&max_line_chars=60')
  })

  it('sets aria-expanded correctly when toggling', () => {
    render(<DownloadMenu taskId="abc" />)
    const btn = screen.getByText('Download').closest('button')!
    expect(btn.getAttribute('aria-expanded')).toBe('false')
    fireEvent.click(btn)
    expect(btn.getAttribute('aria-expanded')).toBe('true')
    fireEvent.click(btn)
    expect(btn.getAttribute('aria-expanded')).toBe('false')
  })
})
