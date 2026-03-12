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
        onClose()
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onClose])

  const statusColor =
    health?.status === 'ok' ? 'var(--color-success)' :
    health?.status === 'degraded' ? 'var(--color-warning)' :
    health?.status === 'error' ? 'var(--color-danger)' :
    'var(--color-text-3)'

  const statusBg =
    health?.status === 'ok' ? 'var(--color-success-light)' :
    health?.status === 'degraded' ? 'var(--color-warning-light)' :
    health?.status === 'error' ? 'var(--color-danger-light)' :
    'var(--color-surface-2)'

  const statusLabel =
    health === null ? 'Connecting…' :
    health.status === 'ok' ? 'All systems operational' :
    health.status === 'degraded' ? 'Performance degraded' :
    'System error'

  return (
    <div
      ref={panelRef}
      className="fixed z-50 flex flex-col gap-4 rounded-xl p-4"
      style={{
        top: '60px',
        right: '16px',
        width: '280px',
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
          <StatBar label="RAM" value={health.ram_percent} />
          <StatBar label="Disk" value={health.disk_percent} />
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
