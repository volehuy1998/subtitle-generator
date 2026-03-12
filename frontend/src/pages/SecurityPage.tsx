import { useEffect, useState } from 'react'
import { StaticPageLayout } from '@/components/layout/StaticPageLayout'

const C = {
  text:          '#0F172A',
  text2:         '#475569',
  text3:         '#94A3B8',
  border:        '#E2E8F0',
  border2:       '#CBD5E1',
  surface:       '#FFFFFF',
  surface2:      '#F8FAFC',
  primary:       '#863bff',
  primaryLight:  '#f3eeff',
  primaryMid:    '#ddd6fe',
  success:       '#10B981',
  successLight:  '#ECFDF5',
  successBorder: '#A7F3D0',
  warning:       '#F59E0B',
  warningLight:  '#FFFBEB',
  errorLight:    '#FEF2F2',
  blue:          '#2563EB',
  blueLight:     '#EFF6FF',
  amber:         '#F59E0B',
}

interface Assertion {
  id: string
  owasp_label: string
  status: 'secure' | 'low_risk' | 'at_risk' | 'untested'
  tests_passed: number
  tests_total: number
  note?: string
}

interface AssertionsData {
  last_updated: string | null
  last_run_commit: string | null
  last_security_commit?: {
    sha: string
    sha_full: string
    datetime: string
    message: string
  } | null
  assertions: Assertion[]
}

function SectionLabel({ children }: { children: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.67rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: C.text3, marginBottom: '12px' }}>
      {children}
      <div style={{ flex: 1, height: '1px', background: C.border }} />
    </div>
  )
}

function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '16px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.07)', ...style }}>
      {children}
    </div>
  )
}

function BadgeStyle(status: string): React.CSSProperties {
  if (status === 'secure')   return { background: C.successLight, color: '#065F46', border: `1px solid ${C.successBorder}` }
  if (status === 'low_risk') return { background: C.blueLight, color: '#1E40AF', border: '1px solid #BFDBFE' }
  if (status === 'at_risk')  return { background: C.errorLight, color: '#991B1B', border: '1px solid #FECACA' }
  return { background: C.surface2, color: C.text3, border: `1px solid ${C.border2}` }
}
function BadgeLabel(status: string) {
  if (status === 'secure')   return 'Secure'
  if (status === 'low_risk') return 'Low Risk'
  if (status === 'at_risk')  return 'At Risk'
  return 'Untested'
}

const DEFENSE_ITEMS = [
  { color: C.success, bg: C.successLight, title: 'File Upload Security', desc: 'Validated by extension, magic bytes (MIME), 2 GB size limit, filename sanitization. Mismatched types rejected. ClamAV scanning available.', icon: <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>, icon2: <path d="M9 13l2 2 4-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/> },
  { color: C.blue, bg: C.blueLight, title: 'Rate Limiting', desc: 'Uploads: 5 req/min per IP. API: 60 req/min. Brute-force protection blocks IPs after 10 failed auth attempts for 10 minutes.', icon: <><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.8"/><path d="M12 8v4l3 3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></> },
  { color: C.primary, bg: C.primaryLight, title: 'No Shell Injection', desc: <>All ffmpeg/ffprobe commands use list-based args (no <code style={{ background: C.surface2, border: `1px solid ${C.border}`, borderRadius: '4px', padding: '1px 5px', fontFamily: 'monospace', fontSize: '0.85em', color: C.primary }}>shell=True</code>). Filenames replaced with UUIDs.</>, icon: <><rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" strokeWidth="1.8"/><path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></> },
  { color: C.success, bg: C.successLight, title: 'No SQL Injection', desc: 'All database access uses SQLAlchemy ORM with parameterized queries. Raw SQL uses named bindings. No string concatenation in queries.', icon: <path d="M4 7h16M4 12h16M4 17h10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/> },
  { color: C.amber, bg: C.warningLight, title: 'Path Traversal Blocked', desc: 'Upload filenames replaced with UUIDs. Download paths verified within the output directory. No user-controlled path segments accepted.', icon: <><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/><path d="M9 22V12h6v10" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/></> },
  { color: C.blue, bg: C.blueLight, title: 'IDOR Prevention', desc: 'Each task is bound to the session that created it via a secure httponly cookie. Cross-session access returns HTTP 403.', icon: <><circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.8"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></> },
  { color: C.success, bg: C.successLight, title: 'Authentication', desc: 'Optional API key auth enforces all non-public endpoints when configured. JWT tokens with HS256 signing. Timing-safe key comparison.', icon: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/> },
  { color: C.primary, bg: C.primaryLight, title: 'Secrets Management', desc: 'No hardcoded secrets. All credentials loaded exclusively from environment variables. Never committed to source control.', icon: <><rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" strokeWidth="1.8"/><path d="M8 21h8M12 17v4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></> },
]

const HEADERS = [
  ['X-Content-Type-Options', 'nosniff — prevents MIME type sniffing attacks'],
  ['X-Frame-Options', 'DENY — blocks clickjacking via iframes'],
  ['X-XSS-Protection', '1; mode=block'],
  ['Referrer-Policy', 'strict-origin-when-cross-origin'],
  ['Permissions-Policy', 'camera=(), microphone=(), geolocation=()'],
  ['Content-Security-Policy', "default-src 'self'; connect-src 'self'; media-src 'self' blob:"],
  ['Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload (production only)'],
]

const TIMELINE = [
  { color: C.success, bg: C.successLight, icon: <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>, title: 'Uploaded files are temporary', desc: 'Files are deleted automatically within 24 hours. They are never used for training or shared with third parties.' },
  { color: C.success, bg: C.successLight, icon: <><circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.8"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></>, title: 'No account required', desc: 'No personal information is collected. Sessions are anonymous, identified only by a random cookie.' },
  { color: C.amber, bg: C.warningLight, icon: <><path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8"/></>, title: 'Access logs retained for security', desc: 'Request logs (IP, endpoint, timestamp) kept for abuse detection. Logs do not contain file contents or transcript text.' },
  { color: C.success, bg: C.successLight, icon: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>, title: 'No third-party data sharing', desc: 'Transcription runs entirely on-server using open-source models (faster-whisper / CTranslate2). Nothing leaves the server.' },
]

export default function SecurityPage() {
  const [assertions, setAssertions] = useState<AssertionsData | null>(null)

  useEffect(() => {
    fetch('/api/security/assertions').then(r => r.json()).then(setAssertions).catch(() => {})
  }, [])

  return (
    <StaticPageLayout>
      {/* Hero */}
      <div style={{
        background: 'linear-gradient(135deg, #0f0c29 0%, #1e1b4b 45%, #312e81 100%)',
        borderRadius: '16px', padding: '44px 40px', marginBottom: '32px',
        color: '#fff', display: 'flex', alignItems: 'flex-start', gap: '22px',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 60% 60% at 80% 50%, rgba(134,59,255,0.18) 0%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={{ width: '48px', height: '48px', background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.14)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: '2px' }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.25C17.25 22.15 21 17.25 21 12V7L12 2z" stroke="white" strokeWidth="1.7" strokeLinejoin="round" fill="rgba(255,255,255,0.12)"/>
            <path d="M9 12l2 2 4-4" stroke="white" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 700, letterSpacing: '-0.5px', marginBottom: '6px' }}>Security</h1>
          <p style={{ fontSize: '0.875rem', color: 'rgba(255,255,255,0.65)', lineHeight: 1.6 }}>How SubForge protects your uploads, prevents attacks, and keeps the service safe.</p>
          {assertions?.last_security_commit && (
            <p style={{ marginTop: '10px', fontSize: '0.775rem', color: 'rgba(255,255,255,0.45)' }}>
              Last security update:{' '}
              <strong style={{ color: 'rgba(255,255,255,0.75)' }}>{assertions.last_security_commit.datetime.slice(0, 10)}</strong>
              {' \u2014 '}
              <em>{assertions.last_security_commit.message}</em>
              {' '}
              <a
                href={`https://github.com/volehuy1998/subtitle-generator/commit/${assertions.last_security_commit.sha_full}`}
                target="_blank" rel="noopener noreferrer"
                style={{ color: 'rgba(134,59,255,0.8)', marginLeft: '4px', fontStyle: 'normal', fontFamily: 'monospace', fontSize: '0.72rem' }}
              >
                {assertions.last_security_commit.sha_full?.slice(0, 12)}
              </a>
            </p>
          )}
        </div>
        <div style={{ marginLeft: 'auto', flexShrink: 0, background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.35)', color: '#6ee7b7', borderRadius: '20px', padding: '5px 14px', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#34d399', display: 'inline-block' }} />
          Risk Level: Low
        </div>
      </div>

      {/* Defenses */}
      <div style={{ marginBottom: '28px' }}>
        <SectionLabel>Attack Prevention</SectionLabel>
        <Card>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1px', background: C.border }}>
            {DEFENSE_ITEMS.map((item, i) => (
              <div key={i} style={{ background: C.surface, padding: '20px 22px', display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: item.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: item.color }}>
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none">{item.icon}{item.icon2}</svg>
                </div>
                <div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 600, marginBottom: '4px', color: C.text }}>{item.title}</div>
                  <div style={{ fontSize: '0.76rem', color: C.text2, lineHeight: 1.55 }}>{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* HTTP Headers */}
      <div style={{ marginBottom: '28px' }}>
        <SectionLabel>HTTP Security Headers</SectionLabel>
        <Card>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {HEADERS.map(([name, desc], i) => (
                <tr key={i} style={{ borderBottom: i < HEADERS.length - 1 ? `1px solid ${C.border}` : 'none' }}>
                  <td style={{ padding: '11px 20px', width: '34%' }}>
                    <span style={{ display: 'inline-block', fontFamily: 'monospace', fontSize: '0.72rem', color: C.primary, background: C.primaryLight, padding: '2px 8px', borderRadius: '4px', whiteSpace: 'nowrap' }}>{name}</span>
                  </td>
                  <td style={{ padding: '11px 20px', fontSize: '0.79rem', color: C.text2, background: i % 2 === 1 ? C.surface2 : C.surface }}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>

      {/* OWASP */}
      <div style={{ marginBottom: '28px' }}>
        <SectionLabel>OWASP Top 10 Coverage</SectionLabel>
        <Card>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1px', background: C.border }}>
            {(assertions?.assertions ?? []).map((a) => (
              <div key={a.id} style={{ background: C.surface, padding: '16px 12px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 500, color: C.text2, marginBottom: '7px' }}>{a.owasp_label}</div>
                <span style={{ display: 'inline-block', padding: '3px 10px', borderRadius: '20px', fontSize: '0.69rem', fontWeight: 700, ...BadgeStyle(a.status) }}>
                  {BadgeLabel(a.status)}
                </span>
                {a.tests_total > 0 && (
                  <div style={{ fontSize: '0.62rem', color: C.text3, marginTop: '5px' }}>{a.tests_passed}/{a.tests_total} tests</div>
                )}
              </div>
            ))}
          </div>
          {assertions?.last_updated && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 20px', borderTop: `1px solid ${C.border}`, background: C.surface2, fontSize: '0.72rem', color: C.text3 }}>
              <span>Last verified: <strong style={{ color: C.text2 }}>{assertions.last_updated.slice(0, 10)}</strong></span>
              {assertions.last_run_commit && <span>Commit: <strong style={{ color: C.text2 }}>{assertions.last_run_commit}</strong></span>}
            </div>
          )}
        </Card>
      </div>

      {/* Data retention */}
      <div style={{ marginBottom: '28px' }}>
        <SectionLabel>Data Handling &amp; Retention</SectionLabel>
        <Card>
          <div style={{ padding: '0 24px' }}>
            {TIMELINE.map((item, i) => (
              <div key={i} style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', padding: '14px 0', borderBottom: i < TIMELINE.length - 1 ? `1px solid ${C.border}` : 'none' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: item.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: item.color }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">{item.icon}</svg>
                </div>
                <div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 600, marginBottom: '3px', color: C.text }}>{item.title}</div>
                  <div style={{ fontSize: '0.77rem', color: C.text2, lineHeight: 1.55 }}>{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Disclosure */}
      <div style={{ marginBottom: '28px' }}>
        <SectionLabel>Responsible Disclosure</SectionLabel>
        <Card>
          <div style={{ background: `linear-gradient(135deg, ${C.primaryLight}, #fff)`, borderBottom: `1px solid ${C.primaryMid}`, padding: '24px 28px', display: 'flex', gap: '16px', alignItems: 'center' }}>
            <div style={{ width: '42px', height: '42px', background: C.primary, borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" stroke="white" strokeWidth="1.8" strokeLinejoin="round"/>
              </svg>
            </div>
            <div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '3px' }}>Found a vulnerability? Let us know.</div>
              <div style={{ fontSize: '0.8rem', color: C.text2 }}>We aim to respond within 48 hours. Please do not disclose publicly before we've had a chance to fix it.</div>
            </div>
          </div>
          <div style={{ padding: '20px 28px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {[
              <>Open a <a href="https://github.com/volehuy1998/subtitle-generator/issues/new?labels=security&title=[Security]+" target="_blank" rel="noopener" style={{ color: C.primary }}>GitHub issue</a> with the <strong>security</strong> label, or use GitHub Security Advisories for private reports.</>,
              'Include: affected endpoint, reproduction steps, and potential impact.',
              'We will acknowledge within 48 hours and credit you in the release notes if you wish.',
            ].map((step, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', fontSize: '0.8rem', color: C.text2, lineHeight: 1.55 }}>
                <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: C.primary, color: '#fff', fontSize: '0.65rem', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: '1px' }}>{i + 1}</div>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </StaticPageLayout>
  )
}
