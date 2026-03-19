/**
 * StatusPage — Enhanced system status dashboard with live metrics.
 *
 * Shows real-time CPU, memory, disk usage via the health stream SSE,
 * component health cards for each monitored service, loaded models,
 * and an auto-refresh indicator.
 *
 * — Pixel (Sr. Frontend Engineer), Task 13
 */

import { useState, useEffect } from 'react'
import { AppShell } from '../components/layout/AppShell'
import { PageLayout } from '../components/layout/PageLayout'
import { useUIStore } from '../store/uiStore'

/* ------------------------------------------------------------------ */
/*  MetricBar — percentage bar with color thresholds                   */
/* ------------------------------------------------------------------ */

function MetricBar({ label, value, max = 100, unit = '%' }: { label: string; value: number; max?: number; unit?: string }) {
  const pct = Math.min((value / max) * 100, 100)
  const color = pct > 90 ? 'var(--color-danger)' : pct > 70 ? 'var(--color-warning)' : 'var(--color-success)'
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-[var(--color-text-secondary)]">{label}</span>
        <span className="font-mono text-[var(--color-text)]">{value.toFixed(1)}{unit}</span>
      </div>
      <div className="h-2 bg-[var(--color-surface-raised)] rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  ComponentCard — status card for a monitored service                */
/* ------------------------------------------------------------------ */

const COMPONENTS = [
  { id: 'transcription', name: 'Transcription Engine', description: 'Whisper model inference' },
  { id: 'video_combine', name: 'Video Combine', description: 'FFmpeg subtitle embedding' },
  { id: 'web_app', name: 'Web Application', description: 'FastAPI server' },
  { id: 'database', name: 'Database', description: 'PostgreSQL / SQLite' },
  { id: 'file_storage', name: 'File Storage', description: 'Upload and output storage' },
] as const

function ComponentCard({ name, description, status }: { name: string; description: string; status: 'operational' | 'degraded' | 'down' }) {
  const statusConfig = {
    operational: { label: 'Operational', dotColor: 'var(--color-success)', textColor: 'var(--color-success)' },
    degraded: { label: 'Degraded', dotColor: 'var(--color-warning)', textColor: 'var(--color-warning)' },
    down: { label: 'Down', dotColor: 'var(--color-danger)', textColor: 'var(--color-danger)' },
  }
  const cfg = statusConfig[status]

  return (
    <div className="flex items-center justify-between p-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
      <div>
        <p className="text-sm font-medium text-[var(--color-text)]">{name}</p>
        <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{description}</p>
      </div>
      <div className="flex items-center gap-2">
        <span
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: cfg.dotColor }}
        />
        <span className="text-xs font-medium" style={{ color: cfg.textColor }}>
          {cfg.label}
        </span>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  StatusPage                                                         */
/* ------------------------------------------------------------------ */

export function StatusPage() {
  const systemHealth = useUIStore(s => s.systemHealth)
  const healthStreamConnected = useUIStore(s => s.healthStreamConnected)
  const healthMetrics = useUIStore(s => s.healthMetrics)
  const modelPreloadStatus = useUIStore(s => s.modelPreloadStatus)

  // Relative time since last update
  const [lastUpdatedText, setLastUpdatedText] = useState('--')

  useEffect(() => {
    const interval = setInterval(() => {
      if (!healthMetrics.lastUpdated) {
        setLastUpdatedText('--')
        return
      }
      const seconds = Math.floor((Date.now() - healthMetrics.lastUpdated) / 1000)
      if (seconds < 5) setLastUpdatedText('just now')
      else if (seconds < 60) setLastUpdatedText(`${seconds}s ago`)
      else setLastUpdatedText(`${Math.floor(seconds / 60)}m ago`)
    }, 1000)
    return () => clearInterval(interval)
  }, [healthMetrics.lastUpdated])

  // Derive component statuses from system health
  const componentStatus = (id: string): 'operational' | 'degraded' | 'down' => {
    if (systemHealth === 'critical') {
      if (id === 'web_app') return 'operational' // if we can see the page, web app works
      return 'down'
    }
    if (systemHealth === 'degraded') {
      if (id === 'file_storage' && healthMetrics.diskPercent !== null && healthMetrics.diskPercent > 90) return 'degraded'
      if (id === 'transcription' && healthMetrics.cpuPercent !== null && healthMetrics.cpuPercent > 95) return 'degraded'
      return 'operational'
    }
    return 'operational'
  }

  const overallLabel = systemHealth === 'critical' ? 'Major Outage' : systemHealth === 'degraded' ? 'Partial Degradation' : 'All Systems Operational'
  const overallColor = systemHealth === 'critical' ? 'var(--color-danger)' : systemHealth === 'degraded' ? 'var(--color-warning)' : 'var(--color-success)'

  const modelEntries = Object.entries(modelPreloadStatus)

  return (
    <AppShell>
      <PageLayout title="System Status" subtitle="Real-time service health">
        <div className="space-y-8">

          {/* Overall status banner */}
          <div
            className="flex items-center justify-between p-4 rounded-lg border"
            style={{ borderColor: overallColor, backgroundColor: `color-mix(in srgb, ${overallColor} 5%, transparent)` }}
          >
            <div className="flex items-center gap-3">
              <span
                className="relative flex h-3 w-3"
              >
                {healthStreamConnected && (
                  <span
                    className="absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping"
                    style={{ backgroundColor: overallColor }}
                  />
                )}
                <span
                  className="relative inline-flex rounded-full h-3 w-3"
                  style={{ backgroundColor: overallColor }}
                />
              </span>
              <span className="text-sm font-semibold" style={{ color: overallColor }}>
                {overallLabel}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
              <span>{healthStreamConnected ? 'Live' : 'Disconnected'}</span>
              <span className="text-[var(--color-text-muted)]">|</span>
              <span>Updated {lastUpdatedText}</span>
            </div>
          </div>

          {/* System metrics */}
          <section>
            <h2 className="text-sm font-semibold text-[var(--color-text)] mb-4 tracking-tight">System Metrics</h2>
            {healthMetrics.cpuPercent !== null ? (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <div className="p-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
                  <MetricBar label="CPU Usage" value={healthMetrics.cpuPercent ?? 0} />
                </div>
                <div className="p-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
                  <MetricBar label="Memory Usage" value={healthMetrics.memoryPercent ?? 0} />
                </div>
                <div className="p-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
                  <MetricBar label="Disk Usage" value={healthMetrics.diskPercent ?? 0} />
                  {healthMetrics.diskFreeGb !== null && (
                    <p className="text-xs text-[var(--color-text-muted)] mt-2">
                      {healthMetrics.diskFreeGb} GB free
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-[var(--color-text-muted)]">
                Waiting for health stream data...
              </p>
            )}
          </section>

          {/* Active tasks */}
          <section>
            <h2 className="text-sm font-semibold text-[var(--color-text)] mb-4 tracking-tight">Active Tasks</h2>
            <div className="p-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] inline-flex items-center gap-3">
              <span className="text-2xl font-mono font-bold text-[var(--color-text)]">
                {healthMetrics.activeTasks}
              </span>
              <span className="text-xs text-[var(--color-text-secondary)]">
                {healthMetrics.activeTasks === 1 ? 'task running' : 'tasks running'}
              </span>
            </div>
          </section>

          {/* Component status */}
          <section>
            <h2 className="text-sm font-semibold text-[var(--color-text)] mb-4 tracking-tight">Components</h2>
            <div className="space-y-2">
              {COMPONENTS.map(c => (
                <ComponentCard
                  key={c.id}
                  name={c.name}
                  description={c.description}
                  status={componentStatus(c.id)}
                />
              ))}
            </div>
          </section>

          {/* Loaded models */}
          {modelEntries.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-[var(--color-text)] mb-4 tracking-tight">Loaded Models</h2>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {modelEntries.map(([name, status]) => (
                  <div
                    key={name}
                    className="flex items-center justify-between p-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]"
                  >
                    <span className="text-sm font-mono text-[var(--color-text)]">{name}</span>
                    <span className={`text-xs font-medium ${status === 'ready' ? 'text-[var(--color-success)]' : 'text-[var(--color-warning)]'}`}>
                      {status}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Health endpoint link */}
          <p className="text-sm text-[var(--color-text-muted)]">
            For raw health data, visit{' '}
            <a href="/health" className="text-[var(--color-primary)] hover:underline">/health</a>
            {' '}or{' '}
            <a href="/api/status" className="text-[var(--color-primary)] hover:underline">/api/status</a>.
          </p>
        </div>
      </PageLayout>
    </AppShell>
  )
}
