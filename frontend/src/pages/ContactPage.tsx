import { StaticPageLayout } from '@/components/layout/StaticPageLayout'

const C = {
  text: '#0F172A', text2: '#475569', text3: '#94A3B8',
  border: '#E2E8F0', border2: '#CBD5E1',
  surface: '#FFFFFF', surface2: '#F8FAFC',
  primary: '#863bff', primaryLight: '#f3eeff',
  success: '#10B981', successLight: '#ECFDF5', successBorder: '#A7F3D0',
  warning: '#F59E0B', warningLight: '#FFFBEB',
  blue: '#2563EB', blueLight: '#EFF6FF',
}

function SectionLabel({ children }: { children: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.67rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: C.text3, marginBottom: '12px' }}>
      {children}
      <div style={{ flex: 1, height: '1px', background: C.border }} />
    </div>
  )
}

const CHANNELS = [
  {
    href: 'https://github.com/volehuy1998/subtitle-generator/issues/new?template=bug_report.md',
    bg: C.blueLight, color: C.blue,
    icon: <><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.8"/><path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></>,
    title: 'Bug Report',
    badge: { label: 'GitHub Issues', style: { background: C.successLight, color: '#065F46', border: `1px solid ${C.successBorder}` } },
    desc: 'Found something broken? Open an issue with steps to reproduce. Include your OS, browser, and the file type you were processing.',
  },
  {
    href: 'https://github.com/volehuy1998/subtitle-generator/issues/new?template=feature_request.md',
    bg: C.primaryLight, color: C.primary,
    icon: <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>,
    title: 'Feature Request',
    badge: { label: 'GitHub Issues', style: { background: C.blueLight, color: '#1E40AF', border: '1px solid #BFDBFE' } },
    desc: 'Have an idea to improve SubForge? Describe the use case and the problem it solves. We prioritize requests with clear motivation.',
  },
  {
    href: 'https://github.com/volehuy1998/subtitle-generator/discussions',
    bg: C.successLight, color: C.success,
    icon: <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>,
    title: 'General Discussion',
    badge: null,
    desc: 'Questions, usage tips, or community discussion — GitHub Discussions is the place. Great for self-hosting questions and deployment advice.',
  },
]

const RT_ITEMS = [
  { label: 'Bug reports', value: '2–5 business days' },
  { label: 'Security issues', value: 'Within 48 hours' },
  { label: 'Feature requests', value: 'Reviewed weekly' },
  { label: 'Pull requests', value: 'Reviewed weekly' },
]

export default function ContactPage() {
  return (
    <StaticPageLayout>
      {/* Hero */}
      <div style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #064e3b 100%)',
        borderRadius: '16px', padding: '44px 40px', marginBottom: '32px',
        color: '#fff', display: 'flex', alignItems: 'flex-start', gap: '22px',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 50% 70% at 85% 50%, rgba(16,185,129,0.15) 0%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={{ width: '48px', height: '48px', background: 'rgba(16,185,129,0.18)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: '2px' }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" stroke="#6ee7b7" strokeWidth="1.8" strokeLinejoin="round"/>
          </svg>
        </div>
        <div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 700, letterSpacing: '-0.5px', marginBottom: '6px' }}>Contact SubForge</h1>
          <p style={{ fontSize: '0.875rem', color: 'rgba(255,255,255,0.65)', lineHeight: 1.6 }}>Bug reports, feature requests, questions — we're responsive and open to contributions.</p>
        </div>
      </div>

      {/* Channels */}
      <div style={{ marginBottom: '28px' }}>
        <SectionLabel>How to reach us</SectionLabel>
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '16px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.07)' }}>
          {CHANNELS.map((ch, i) => (
            <a key={i} href={ch.href} target="_blank" rel="noopener" style={{
              display: 'flex', alignItems: 'flex-start', gap: '16px', padding: '20px 22px',
              borderBottom: i < CHANNELS.length - 1 ? `1px solid ${C.border}` : 'none',
              textDecoration: 'none', transition: 'background 0.12s',
            }}
              onMouseEnter={e => (e.currentTarget.style.background = C.surface2)}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: ch.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: ch.color }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">{ch.icon}</svg>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: C.text, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  {ch.title}
                  {ch.badge && <span style={{ fontSize: '0.67rem', fontWeight: 700, padding: '2px 8px', borderRadius: '20px', ...ch.badge.style }}>{ch.badge.label}</span>}
                </div>
                <div style={{ fontSize: '0.78rem', color: C.text2, lineHeight: 1.55 }}>{ch.desc}</div>
              </div>
              <div style={{ color: C.text3, flexShrink: 0, alignSelf: 'center' }}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
              </div>
            </a>
          ))}
          {/* Security — separate since it has nested links */}
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', padding: '20px 22px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: C.warningLight, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: C.warning }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/></svg>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: C.text, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                Security Vulnerability
                <span style={{ fontSize: '0.67rem', fontWeight: 700, padding: '2px 8px', borderRadius: '20px', background: C.successLight, color: '#065F46', border: `1px solid ${C.successBorder}` }}>48h response</span>
              </div>
              <div style={{ fontSize: '0.78rem', color: C.text2, lineHeight: 1.55 }}>
                Please report security issues via{' '}
                <a href="https://github.com/volehuy1998/subtitle-generator/security/advisories/new" target="_blank" rel="noopener" style={{ color: C.primary }}>GitHub Security Advisories</a>
                , or open an issue with the <strong>security</strong> label. Do not disclose publicly before we respond. See our{' '}
                <a href="/security" style={{ color: C.primary }}>Security page</a> for details.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Response times */}
      <div style={{ marginBottom: '28px' }}>
        <SectionLabel>Response Times</SectionLabel>
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '16px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.07)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1px', background: C.border }}>
            {RT_ITEMS.map((item, i) => (
              <div key={i} style={{ background: C.surface, padding: '18px 22px' }}>
                <div style={{ fontSize: '0.76rem', color: C.text2, marginBottom: '5px' }}>{item.label}</div>
                <div style={{ fontSize: '0.88rem', fontWeight: 700, color: C.text }}>{item.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Note */}
      <div style={{ background: C.warningLight, border: '1px solid #FDE68A', borderRadius: '16px', padding: '18px 20px', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0, color: C.warning, marginTop: '1px' }}>
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>
          <path d="M12 9v4M12 17h.01" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
        </svg>
        <p style={{ fontSize: '0.79rem', color: C.text2, lineHeight: 1.55 }}>
          SubForge is maintained as an open-source project. There is no dedicated support team — responses come from maintainers on a best-effort basis. For production deployments requiring SLA guarantees, consider self-hosting with your own team support.
        </p>
      </div>
    </StaticPageLayout>
  )
}
