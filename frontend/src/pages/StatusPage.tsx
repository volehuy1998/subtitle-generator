import { useEffect, useState, useCallback } from 'react'
import { HealthPanel } from '@/components/system/HealthPanel'
import { useUIStore } from '@/store/uiStore'

// ── Design tokens (CSS variables) ──────────────────────────────────────────
const C = {
  text:    'var(--color-text)',
  text2:   'var(--color-text-2)',
  text3:   'var(--color-text-3)',
  border:  'var(--color-border)',
  border2: 'var(--color-border-2)',
  surface: 'var(--color-surface)',
  surface2:'var(--color-surface-2)',
  primary: 'var(--color-primary)',
  success: 'var(--color-success)',
  successLight: 'var(--color-success-light)',
  successBorder:'var(--color-success-border)',
  warning: 'var(--color-warning)',
  warningLight: 'var(--color-warning-light)',
  danger:  'var(--color-danger)',
  dangerLight:  'var(--color-danger-light)',
}

// ── Types ──────────────────────────────────────────────────────────────────

interface ComponentStatus {
  id: string
  name: string
  description: string
  status: 'operational' | 'degraded' | 'outage' | 'maintenance'
}

interface DayStatus {
  date: string
  status: 'operational' | 'degraded' | 'outage' | 'no_data'
}

interface UptimeHistory {
  uptime_pct: number | null
  downtime_min: number
  daily: DayStatus[]
}

interface IncidentUpdate {
  status: string
  message: string
  created_at: string
}

interface Incident {
  title: string
  severity: string
  status: string
  component: string
  created_at: string
  updates?: IncidentUpdate[]
}

interface StatusPage {
  overall: 'operational' | 'degraded' | 'outage'
  updated_at: string
  uptime_sec: number
  sla_target: number
  task_stats: { total_24h: number; completed_24h: number; failed_24h: number }
  components: ComponentStatus[]
  uptime_history: Record<string, UptimeHistory>
  incidents: Incident[]
}

interface CommitFile {
  path: string
  action: 'A' | 'M' | 'D'
}

interface Commit {
  sha: string
  sha_short: string
  subject: string
  body: string
  date: string
  files_count: number
  files: CommitFile[]
  ci_status: 'success' | 'failure' | 'in_progress' | 'unknown'
}

interface CommitsData {
  commits: Commit[]
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatUptime(sec: number): string {
  const d = Math.floor(sec / 86400)
  const h = Math.floor((sec % 86400) / 3600)
  const m = Math.floor((sec % 3600) / 60)
  if (d > 0) return `${d}d ${h}h`
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

function formatDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    })
  } catch { return iso }
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
  } catch { return iso }
}

function formatDowntime(min: number): string {
  if (!min || min === 0) return ''
  if (min < 1) return `${Math.round(min * 60)}s down`
  if (min < 60) return `${min.toFixed(1)}m down`
  const h = Math.floor(min / 60)
  const m = Math.round(min % 60)
  return `${h}h ${m}m down`
}

function formatUpPct(pct: number, downMin: number): string {
  if (pct === 100 && (!downMin || downMin === 0)) return '100'
  if (downMin < 1) return pct.toFixed(4)
  if (downMin < 10) return pct.toFixed(3)
  if (downMin < 60) return pct.toFixed(2)
  return pct.toFixed(1)
}

const STATUS_LABELS: Record<string, string> = {
  operational: 'Operational',
  degraded: 'Degraded',
  outage: 'Outage',
  maintenance: 'Maintenance',
  no_data: 'No Data',
}

const STATUS_COLOR: Record<string, string> = {
  operational: 'var(--color-success)',
  degraded: 'var(--color-warning)',
  outage: 'var(--color-danger)',
  maintenance: 'var(--color-primary)',
  no_data: 'var(--color-text-3)',
}

// ── Sub-components ─────────────────────────────────────────────────────────

function Banner({ data }: { data: StatusPage }) {
  const config = {
    operational: { icon: '✓', label: 'All Systems Operational', bg: C.successLight, border: C.successBorder, color: C.success },
    degraded: { icon: '⚠', label: 'Some Systems Experiencing Issues', bg: C.warningLight, border: C.border2, color: C.warning },
    outage: { icon: '✕', label: 'Service Disruption Detected', bg: C.dangerLight, border: C.border2, color: C.danger },
  }[data.overall] ?? { icon: '✓', label: 'All Systems Operational', bg: C.successLight, border: C.successBorder, color: C.success }

  return (
    <div style={{
      background: config.bg, border: `1px solid ${config.border}`,
      borderRadius: '14px', padding: '20px 24px',
      display: 'flex', alignItems: 'center', gap: '16px',
      marginBottom: '24px',
    }}>
      <div style={{
        width: '44px', height: '44px', borderRadius: '50%',
        background: config.color, color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '20px', fontWeight: '700', flexShrink: 0,
      }}>{config.icon}</div>
      <div>
        <div style={{ fontWeight: '700', fontSize: '1.05rem', color: config.color }}>{config.label}</div>
        <div style={{ fontSize: '0.78rem', color: C.text2, marginTop: '2px' }}>
          Last updated: {formatDateTime(data.updated_at)}
        </div>
      </div>
    </div>
  )
}

function StatsRow({ data }: { data: StatusPage }) {
  const stats = [
    { label: 'Uptime', value: formatUptime(data.uptime_sec) },
    { label: 'Tasks (24h)', value: String(data.task_stats.total_24h) },
    { label: 'Completed', value: String(data.task_stats.completed_24h) },
    { label: 'Failed', value: String(data.task_stats.failed_24h) },
  ]
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '24px' }}>
      {stats.map((s) => (
        <div key={s.label} style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: '10px',
          padding: '14px 16px', textAlign: 'center',
        }}>
          <div style={{ fontSize: '1.4rem', fontWeight: '700', color: C.text }}>{s.value}</div>
          <div style={{ fontSize: '0.75rem', color: C.text2, marginTop: '2px' }}>{s.label}</div>
        </div>
      ))}
    </div>
  )
}

function ComponentCard({ comp, history, sla }: { comp: ComponentStatus; history: UptimeHistory | undefined; sla: number }) {
  const pct = history?.uptime_pct ?? 100
  const downMin = history?.downtime_min ?? 0
  const daily = history?.daily ?? []
  const aboveSla = pct >= sla
  const downLabel = formatDowntime(downMin)
  const color = STATUS_COLOR[comp.status] ?? C.text3

  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`, borderRadius: '10px',
      padding: '16px 18px', marginBottom: '10px',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div>
          <div style={{ fontWeight: '600', fontSize: '0.9rem', color: C.text }}>{comp.name}</div>
          <div style={{ fontSize: '0.78rem', color: C.text2, marginTop: '2px' }}>{comp.description}</div>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          fontSize: '0.78rem', fontWeight: '600', color,
        }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: color, display: 'inline-block' }} />
          {STATUS_LABELS[comp.status] ?? comp.status}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ display: 'flex', gap: '2px', flex: 1 }}>
          {daily.map((d, i) => (
            <div
              key={i}
              title={`${formatDate(d.date)}: ${STATUS_LABELS[d.status] ?? d.status}`}
              style={{
                flex: 1, height: '24px', borderRadius: '2px',
                background: STATUS_COLOR[d.status] ?? C.text3,
                opacity: d.status === 'no_data' ? 0.3 : 1,
              }}
            />
          ))}
        </div>
        <div style={{
          textAlign: 'right', minWidth: '56px',
          fontSize: '0.8rem', fontWeight: '700',
          color: aboveSla ? C.success : C.danger,
        }}>
          {formatUpPct(pct, downMin)}%
          {downLabel && (
            <div style={{ fontSize: '0.63rem', color: C.text3, fontWeight: '400' }}>{downLabel}</div>
          )}
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: C.text3, marginTop: '4px' }}>
        <span>90 days ago</span>
        <span>Today · <span style={{ color: C.primary, fontWeight: '600' }}>SLA {sla.toFixed(1)}%</span></span>
      </div>
    </div>
  )
}

function IncidentsSection({ data }: { data: StatusPage }) {
  const incidents = data.incidents ?? []
  const compMap = Object.fromEntries(data.components.map((c) => [c.id, c.name]))

  if (incidents.length === 0) {
    return (
      <div style={{ color: C.text2, fontSize: '0.88rem', padding: '16px 0' }}>
        No incidents reported in the last 14 days. All systems have been operating normally.
      </div>
    )
  }

  // Group by date
  const groups: Record<string, Incident[]> = {}
  const order: string[] = []
  incidents.forEach((inc) => {
    const key = inc.created_at.split('T')[0]
    if (!groups[key]) { groups[key] = []; order.push(key) }
    groups[key].push(inc)
  })

  return (
    <div>
      {order.map((dateKey) => (
        <div key={dateKey} style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: '700', color: C.text2, marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {formatDate(dateKey + 'T00:00:00')}
          </div>
          {groups[dateKey].map((inc, i) => {
            const badgeColor = inc.status === 'resolved' ? C.success
              : inc.severity === 'critical' ? C.danger
              : inc.severity === 'major' ? C.warning : C.primary
            return (
              <div key={i} style={{
                background: C.surface, border: `1px solid ${C.border}`,
                borderRadius: '10px', padding: '14px 16px', marginBottom: '8px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <div style={{ fontWeight: '600', fontSize: '0.9rem', color: C.text }}>{inc.title}</div>
                  <span style={{
                    background: badgeColor, color: '#fff',
                    borderRadius: '4px', padding: '2px 8px',
                    fontSize: '0.72rem', fontWeight: '700', textTransform: 'capitalize',
                    flexShrink: 0, marginLeft: '8px',
                  }}>
                    {inc.status === 'resolved' ? 'Resolved' : inc.severity}
                  </span>
                </div>
                <div style={{ fontSize: '0.78rem', color: C.text2, marginBottom: '8px' }}>
                  Affected: {compMap[inc.component] ?? inc.component}
                </div>
                {inc.updates && inc.updates.length > 0 && (
                  <div style={{ borderLeft: `2px solid ${C.border}`, paddingLeft: '12px' }}>
                    {inc.updates.map((u, j) => (
                      <div key={j} style={{ marginBottom: '8px' }}>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '2px' }}>
                          <span style={{
                            fontSize: '0.7rem', fontWeight: '700', textTransform: 'capitalize',
                            color: STATUS_COLOR[u.status] ?? C.text2,
                          }}>{u.status}</span>
                          <span style={{ fontSize: '0.72rem', color: C.text3 }}>{formatDateTime(u.created_at)}</span>
                        </div>
                        <div style={{ fontSize: '0.82rem', color: C.text2 }}>{u.message}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}

function CommitCard({ commit, idx, expanded, onToggle }: {
  commit: Commit; idx: number; expanded: boolean; onToggle: (idx: number) => void
}) {
  const ciConfig = {
    success: { label: 'Passed', color: C.success, bg: C.successLight },
    failure: { label: 'Failed', color: C.danger, bg: C.dangerLight },
    in_progress: { label: 'Running', color: C.warning, bg: C.warningLight },
    unknown: { label: 'N/A', color: C.text3, bg: C.surface2 },
  }[commit.ci_status] ?? { label: 'N/A', color: C.text3, bg: C.surface2 }

  const dateStr = (() => {
    try {
      return new Date(commit.date).toLocaleString(undefined, {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: '2-digit', minute: '2-digit', timeZoneName: 'short',
      })
    }
    catch { return commit.date }
  })()

  const body = commit.body.replace(/Co-Authored-By:.*$/gm, '').trim()

  return (
    <button
      type="button"
      onClick={() => onToggle(idx)}
      style={{
        background: C.surface, border: `1px solid ${C.border}`, borderRadius: '10px',
        padding: '12px 16px', marginBottom: '8px', cursor: 'pointer',
        transition: 'border-color 0.15s',
        width: '100%', textAlign: 'left', font: 'inherit', color: 'inherit',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        <span style={{
          background: ciConfig.bg, color: ciConfig.color,
          borderRadius: '4px', padding: '2px 8px',
          fontSize: '0.72rem', fontWeight: '700', flexShrink: 0,
        }}>{ciConfig.label}</span>
        <span style={{ flex: 1, fontWeight: '500', fontSize: '0.88rem', color: C.text, minWidth: 0 }}>
          {commit.subject}
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          <span style={{ fontSize: '0.75rem', color: C.text3 }}>
            {commit.files_count} file{commit.files_count !== 1 ? 's' : ''}
          </span>
          <a
            href={`https://github.com/volehuy1998/subtitle-generator/commit/${commit.sha}`}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            style={{
              fontFamily: 'monospace', fontSize: '0.75rem',
              color: C.primary, fontWeight: '700',
              padding: '1px 6px', borderRadius: '4px',
              background: 'var(--color-primary-light)', textDecoration: 'none',
            }}
          >{commit.sha_short}</a>
          <span style={{ fontSize: '0.75rem', color: C.text3 }}>{dateStr}</span>
          <span style={{ color: C.text3, transform: expanded ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s' }}>▶</span>
        </span>
      </div>

      {expanded && (
        <div
          onClick={(e) => e.stopPropagation()}
          style={{ marginTop: '12px', paddingTop: '12px', borderTop: `1px solid ${C.border}` }}
        >
          {body && (
            <pre style={{
              fontFamily: 'inherit', fontSize: '0.82rem', color: C.text2,
              whiteSpace: 'pre-wrap', marginBottom: '10px',
            }}>{body}</pre>
          )}
          {commit.files.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '10px' }}>
              {commit.files.map((f, fi) => (
                <span key={fi} style={{
                  fontSize: '0.73rem', padding: '2px 7px', borderRadius: '4px',
                  background: f.action === 'A' ? C.successLight : f.action === 'D' ? C.dangerLight : C.surface2,
                  color: f.action === 'A' ? C.success : f.action === 'D' ? C.danger : C.text2,
                  fontFamily: 'monospace',
                }}>{f.path}</span>
              ))}
            </div>
          )}
          <a
            href={`https://github.com/volehuy1998/subtitle-generator/commit/${commit.sha}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ fontSize: '0.78rem', color: C.primary }}
          >
            View on GitHub ↗
          </a>
        </div>
      )}
    </button>
  )
}

// ── Main Component ─────────────────────────────────────────────────────────

export function StatusPage() {
  const [statusData, setStatusData] = useState<StatusPage | null>(null)
  const [commitsData, setCommitsData] = useState<CommitsData | null>(null)
  const [expandedCommits, setExpandedCommits] = useState<Set<number>>(new Set())
  const { healthPanelOpen, setHealthPanelOpen, health } = useUIStore()

  const loadStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/status/page')
      if (res.ok) setStatusData(await res.json())
    } catch { /* ignore */ }
  }, [])

  const loadCommits = useCallback(async () => {
    try {
      const res = await fetch('/api/status/commits')
      if (res.ok) setCommitsData(await res.json())
    } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- async fetch-then-setState is intentional; no external data source to subscribe to
    void loadStatus()
    void loadCommits()
    const si = setInterval(() => { void loadStatus() }, 30000)
    const ci = setInterval(() => { void loadCommits() }, 60000)
    return () => { clearInterval(si); clearInterval(ci) }
  }, [loadStatus, loadCommits])

  const toggleCommit = (idx: number) => {
    setExpandedCommits((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) { next.delete(idx) } else { next.add(idx) }
      return next
    })
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-bg)', fontFamily: 'var(--font-family-sans)', fontSize: '14px', color: C.text }}>
      {healthPanelOpen && <HealthPanel health={health} onClose={() => setHealthPanelOpen(false)} />}

      {/* Body */}
      <main style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 24px' }}>
        {statusData ? (
          <>
            <Banner data={statusData} />
            <StatsRow data={statusData} />

            <Section title="Components">
              {statusData.components.map((comp) => (
                <ComponentCard
                  key={comp.id}
                  comp={comp}
                  history={statusData.uptime_history[comp.id]}
                  sla={statusData.sla_target ?? 99.9}
                />
              ))}
            </Section>

            <Section title="Recent Incidents">
              <IncidentsSection data={statusData} />
            </Section>
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '60px', color: C.text3 }}>Loading…</div>
        )}

        <Section title="Deployment History">
          {commitsData ? (
            commitsData.commits.length > 0 ? (
              commitsData.commits.map((c, i) => (
                <CommitCard
                  key={c.sha}
                  commit={c}
                  idx={i}
                  expanded={expandedCommits.has(i)}
                  onToggle={toggleCommit}
                />
              ))
            ) : (
              <div style={{ color: C.text2, fontSize: '0.88rem', padding: '16px 0' }}>No commit history available.</div>
            )
          ) : (
            <div style={{ color: C.text3, fontSize: '0.88rem', padding: '16px 0' }}>Loading…</div>
          )}
        </Section>
      </main>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginBottom: '32px' }}>
      <h2 style={{ fontSize: '0.85rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.07em', color: C.text2, marginBottom: '12px' }}>
        {title}
      </h2>
      {children}
    </section>
  )
}
