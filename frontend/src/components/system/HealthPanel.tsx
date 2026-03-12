import { useEffect, useRef } from 'react'
import type { HealthStatus } from '@/api/types'

interface Props {
  health: HealthStatus | null
  onClose: () => void
}

function StatBar({ label, value }: { label: string; value: number | undefined }) {
  const pct = Math.min(100, Math.round(value ?? 0))
  let barColor = 'var(--color-success)'
  if (pct > 85) barColor = 'var(--color-danger)'
  else if (pct > 65) barColor = 'var(--color-warning)'

  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between">
        <span className="text-xs" style={{ color: 'var(--color-text-2)' }}>{label}</span>
        <span className="text-xs font-medium" style={{ color: 'var(--color-text)' }}>{pct}%</span>
      </div>
      <div
        className="h-1 rounded-full overflow-hidden"
        style={{ background: 'var(--color-border)' }}
      >
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, background: barColor }}
        />
      </div>
    </div>
  )
}

function formatUptime(sec: number) {
  if (sec < 60) return `${Math.round(sec)}s`
  if (sec < 3600) return `${Math.floor(sec / 60)}m ${Math.round(sec % 60)}s`
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  return `${h}h ${m}m`
}

export function HealthPanel({ health, onClose }: Props) {
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        // If the tap is on the toggle button, let its onClick handle it instead
        if ((e.target as HTMLElement).closest?.('[data-health-toggle]')) return
        onClose()
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onClose])

  const isOk = health?.status === 'ok' || health?.status === 'healthy'
  const isWarn = health?.status === 'degraded' || health?.status === 'warning'
  const isCrit = health?.status === 'error' || health?.status === 'critical'

  const statusColor =
    isOk ? 'var(--color-success)' :
    isWarn ? 'var(--color-warning)' :
    isCrit ? 'var(--color-danger)' :
    'var(--color-text-3)'

  const statusBg =
    isOk ? 'var(--color-success-light)' :
    isWarn ? 'var(--color-warning-light)' :
    isCrit ? 'var(--color-danger-light)' :
    'var(--color-surface-2)'

  const statusLabel =
    health === null ? 'Connecting…' :
    isOk ? 'All systems operational' :
    isWarn ? 'Performance degraded' :
    'System error'

  return (
    <div
      ref={panelRef}
      className="fixed z-50 flex flex-col gap-4 rounded-xl p-4 left-2 right-2 sm:left-auto sm:right-4 sm:w-[280px]"
      style={{
        top: '60px',
        background: 'var(--color-surface)',
        boxShadow: 'var(--shadow-lg)',
        border: '1px solid var(--color-border)',
      }}
    >
      {/* Status badge */}
      <div
        className="flex items-center gap-2 px-3 py-2 rounded-lg"
        style={{ background: statusBg }}
      >
        <span
          className="inline-block w-2 h-2 rounded-full flex-shrink-0"
          style={{ background: statusColor }}
        />
        <span className="text-xs font-medium" style={{ color: statusColor }}>
          {statusLabel}
        </span>
      </div>

      {/* Uptime */}
      {health && (
        <div className="flex justify-between items-center">
          <span className="text-xs" style={{ color: 'var(--color-text-2)' }}>Uptime</span>
          <span className="text-xs font-medium" style={{ color: 'var(--color-text)' }}>
            {formatUptime(health.uptime_sec)}
          </span>
        </div>
      )}

      {/* Resource bars */}
      {health && (
        <div className="flex flex-col gap-3">
          <StatBar label="CPU" value={health.cpu_percent} />
          <StatBar label="RAM" value={health.ram_percent ?? health.memory_percent} />
          <div className="flex flex-col gap-0.5">
            <StatBar label="Disk" value={health.disk_percent} />
            {health.disk_free_gb != null && (
              <span className="text-right text-xs" style={{ color: health.disk_ok ? 'var(--color-text-3)' : 'var(--color-danger)', fontSize: '11px' }}>
                {health.disk_free_gb} GB free{!health.disk_ok ? ' — low' : ''}
              </span>
            )}
          </div>
        </div>
      )}

      {/* GPU status */}
      {health && health.gpu_available && (
        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <span className="text-xs" style={{ color: 'var(--color-text-2)' }}>GPU</span>
            <span className="text-xs font-medium" style={{ color: 'var(--color-success)' }}>
              {health.gpu_name ?? 'Available'}
            </span>
          </div>
          {health.gpu_vram_total != null && health.gpu_vram_used != null && (
            <div className="flex flex-col gap-1">
              <div className="flex justify-between">
                <span className="text-xs" style={{ color: 'var(--color-text-2)' }}>VRAM</span>
                <span className="text-xs font-medium" style={{ color: 'var(--color-text)' }}>
                  {health.gpu_vram_used.toFixed(1)} / {health.gpu_vram_total} GB
                </span>
              </div>
              <div className="h-1 rounded-full overflow-hidden" style={{ background: 'var(--color-border)' }}>
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.min(100, Math.round((health.gpu_vram_used / health.gpu_vram_total) * 100))}%`,
                    background: 'var(--color-primary)',
                  }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* No GPU warning */}
      {health && !health.gpu_available && (
        <div
          className="flex items-start gap-2 px-2.5 py-2.5 rounded-lg"
          style={{
            background: 'rgba(245,158,11,0.10)',
            border: '1px solid rgba(245,158,11,0.35)',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 12 12" fill="none" aria-hidden="true" className="mt-0.5 flex-shrink-0">
            <path d="M6 1.5L11 10.5H1L6 1.5Z" stroke="#F59E0B" strokeWidth="1.2" strokeLinejoin="round" />
            <path d="M6 5v2.5" stroke="#F59E0B" strokeWidth="1.2" strokeLinecap="round" />
            <circle cx="6" cy="9" r="0.5" fill="#F59E0B" />
          </svg>
          <div className="flex flex-col gap-0.5">
            <span className="text-xs font-semibold" style={{ color: '#F59E0B' }}>No GPU detected</span>
            <span className="text-xs" style={{ color: 'var(--color-text-2)' }}>
              Transcription runs on CPU — significantly slower. For best performance, use a server with an NVIDIA GPU.
            </span>
          </div>
        </div>
      )}

      {/* DB status */}
      {health && (
        <div className="flex justify-between items-center">
          <span className="text-xs" style={{ color: 'var(--color-text-2)' }}>Database</span>
          <span
            className="text-xs font-medium"
            style={{ color: health.db_ok ? 'var(--color-success)' : 'var(--color-danger)' }}
          >
            {health.db_ok ? 'Connected' : 'Error'}
          </span>
        </div>
      )}

      {/* Alerts */}
      {health?.alerts && health.alerts.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium" style={{ color: 'var(--color-text-2)' }}>
            ALERTS
          </span>
          {health.alerts.map((alert, i) => (
            <div
              key={i}
              className="flex items-start gap-2 px-2.5 py-2 rounded-lg text-xs"
              style={{
                background: 'var(--color-warning-light)',
                color: 'var(--color-warning)',
                border: '1px solid #FDE68A',
              }}
            >
              <span className="mt-0.5 flex-shrink-0">⚠</span>
              <span style={{ color: 'var(--color-text)' }}>{alert}</span>
            </div>
          ))}
        </div>
      )}

      {!health && (
        <div className="flex flex-col gap-3">
          {[1, 2, 3].map(i => (
            <div
              key={i}
              className="h-4 rounded animate-pulse"
              style={{ background: 'var(--color-surface-2)' }}
            />
          ))}
        </div>
      )}
    </div>
  )
}
