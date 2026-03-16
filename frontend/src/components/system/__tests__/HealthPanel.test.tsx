import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { HealthPanel } from '../HealthPanel'
import type { HealthStatus } from '@/api/types'

const baseHealth: HealthStatus = {
  status: 'healthy',
  uptime_sec: 3600,
  cpu_percent: 25,
  ram_percent: 40,
  disk_percent: 55,
  disk_free_gb: 120,
  disk_ok: true,
  gpu_available: false,
  db_ok: true,
  alerts: [],
} as HealthStatus

const onClose = vi.fn()

describe('HealthPanel', () => {
  it('shows loading skeletons when health is null', () => {
    const { container } = render(<HealthPanel health={null} onClose={onClose} />)
    // Loading skeletons use animate-pulse class
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThanOrEqual(3)
  })

  it('shows "Connecting..." label when health is null', () => {
    render(<HealthPanel health={null} onClose={onClose} />)
    expect(screen.getByText('Connecting…')).toBeInTheDocument()
  })

  it('shows "All systems operational" when status is healthy', () => {
    render(<HealthPanel health={baseHealth} onClose={onClose} />)
    expect(screen.getByText('All systems operational')).toBeInTheDocument()
  })

  it('displays CPU stat', () => {
    render(<HealthPanel health={baseHealth} onClose={onClose} />)
    expect(screen.getByText('CPU')).toBeInTheDocument()
    expect(screen.getByText('25%')).toBeInTheDocument()
  })

  it('displays RAM stat', () => {
    render(<HealthPanel health={baseHealth} onClose={onClose} />)
    expect(screen.getByText('RAM')).toBeInTheDocument()
    expect(screen.getByText('40%')).toBeInTheDocument()
  })

  it('displays Disk stat', () => {
    render(<HealthPanel health={baseHealth} onClose={onClose} />)
    expect(screen.getByText('Disk')).toBeInTheDocument()
    expect(screen.getByText('55%')).toBeInTheDocument()
  })

  it('shows GPU section when gpu_available=true', () => {
    const health = { ...baseHealth, gpu_available: true, gpu_name: 'RTX 4090' }
    render(<HealthPanel health={health} onClose={onClose} />)
    expect(screen.getByText('GPU')).toBeInTheDocument()
    expect(screen.getByText('RTX 4090')).toBeInTheDocument()
  })

  it('hides GPU row and shows "No GPU detected" when gpu_available=false', () => {
    render(<HealthPanel health={baseHealth} onClose={onClose} />)
    expect(screen.getByText('No GPU detected')).toBeInTheDocument()
  })

  it('shows DB connected when db_ok is true', () => {
    render(<HealthPanel health={baseHealth} onClose={onClose} />)
    expect(screen.getByText('Database')).toBeInTheDocument()
    expect(screen.getByText('Connected')).toBeInTheDocument()
  })

  it('shows DB error when db_ok is false', () => {
    const health = { ...baseHealth, db_ok: false }
    render(<HealthPanel health={health} onClose={onClose} />)
    expect(screen.getByText('Error')).toBeInTheDocument()
  })

  it('shows uptime', () => {
    render(<HealthPanel health={baseHealth} onClose={onClose} />)
    expect(screen.getByText('Uptime')).toBeInTheDocument()
    expect(screen.getByText('1h 0m')).toBeInTheDocument()
  })

  it('shows "Performance degraded" for warning status', () => {
    const health = { ...baseHealth, status: 'degraded' as HealthStatus['status'] }
    render(<HealthPanel health={health} onClose={onClose} />)
    expect(screen.getByText('Performance degraded')).toBeInTheDocument()
  })
})
