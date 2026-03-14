import { StaticPageLayout } from '@/components/layout/StaticPageLayout'

const C = {
  text: 'var(--color-text)', text2: 'var(--color-text-2)', text3: 'var(--color-text-3)',
  border: 'var(--color-border)', border2: 'var(--color-border-2)',
  surface: 'var(--color-surface)', surface2: 'var(--color-surface-2)',
  primary: 'var(--color-primary)', primaryLight: 'var(--color-primary-light)', primaryMid: 'var(--color-primary-border)',
  success: 'var(--color-success)', successLight: 'var(--color-success-light)', successBorder: 'var(--color-success-border)',
  blue: 'var(--color-primary)', blueLight: 'var(--color-primary-light)',
}

function SectionLabel({ children }: { children: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.67rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: C.text3, marginBottom: '12px' }}>
      {children}
      <div style={{ flex: 1, height: '1px', background: C.border }} />
    </div>
  )
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '16px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.07)' }}>
      {children}
    </div>
  )
}

const TAG_STYLE: React.CSSProperties = {
  display: 'inline-block', padding: '2px 8px', borderRadius: '5px',
  fontSize: '0.69rem', fontWeight: 600,
  background: C.primaryLight, color: C.primary,
  marginRight: '4px', marginBottom: '2px',
  border: `1px solid ${C.primaryMid}`,
}

const FEATURES = [
  {
    bg: C.primaryLight, color: C.primary,
    icon: <><path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" stroke="currentColor" strokeWidth="1.8"/><path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v3M8 22h8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></>,
    title: 'Multi-language', desc: 'Transcribes and translates 90+ languages. Auto-detect or specify language manually.',
  },
  {
    bg: C.successLight, color: C.success,
    icon: <><rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" strokeWidth="1.8"/><path d="M8 21h8M12 17v4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></>,
    title: 'Subtitle Embedding', desc: 'Soft-mux generated subtitles into your video in one click — no re-upload needed.',
  },
  {
    bg: C.blueLight, color: C.blue,
    icon: <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>,
    title: 'GPU Accelerated', desc: 'Uses NVIDIA CUDA when available for 10–20× faster transcription. Falls back to CPU.',
  },
  {
    bg: C.primaryLight, color: C.primary,
    icon: <><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.8"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10A15.3 15.3 0 0 1 8 12 15.3 15.3 0 0 1 12 2z" stroke="currentColor" strokeWidth="1.8"/></>,
    title: 'Multiple Formats', desc: 'Export as SRT, WebVTT, or JSON. All formats include word-level timestamps.',
  },
  {
    bg: C.successLight, color: C.success,
    icon: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" strokeWidth="1.8"/>,
    title: 'Private by Design', desc: 'Files deleted within 24 hours. No accounts. No telemetry. Sessions are anonymous.',
  },
  {
    bg: C.blueLight, color: C.blue,
    icon: <><rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" strokeWidth="1.8"/><path d="M7 8h10M7 11h7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></>,
    title: 'Real-time Progress', desc: 'Live updates via Server-Sent Events. See exactly which step the pipeline is on.',
  },
]

const STACK = [
  ['Transcription',    [['faster-whisper', 'CTranslate2'], 'quantized Whisper models, 4× faster than reference']],
  ['Backend',         [['FastAPI', 'Python 3.12', 'asyncio'], 'async REST API with real-time SSE']],
  ['Frontend',        [['React 19', 'TypeScript', 'Vite 6', 'Zustand'], 'single-page app']],
  ['Database',        [['PostgreSQL', 'SQLite'], 'via SQLAlchemy async']],
  ['Media',           [['ffmpeg', 'ffprobe'], 'audio extraction and subtitle embedding']],
  ['Deployment',      [['Docker', 'Redis', 'Celery'], 'distributed workers, S3-compatible storage']],
] as const

export function AboutPage() {
  return (
    <StaticPageLayout>
      {/* Hero */}
      <div style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 55%, #312e81 100%)',
        borderRadius: '16px', padding: '44px 40px', marginBottom: '32px',
        color: '#fff', display: 'flex', alignItems: 'flex-start', gap: '22px',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 50% 80% at 90% 50%, rgba(59,130,246,0.18) 0%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={{ width: '48px', height: '48px', background: 'rgba(59,130,246,0.20)', border: '1px solid rgba(59,130,246,0.30)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: '2px' }}>
          <svg width="24" height="24" viewBox="0 0 48 46" fill="none">
            <path d="M25.946 44.938c-.664.845-2.021.375-2.021-.698V33.937a2.26 2.26 0 0 0-2.262-2.262H10.287c-.92 0-1.456-1.04-.92-1.788l7.48-10.471c1.07-1.497 0-3.578-1.842-3.578H1.237c-.92 0-1.456-1.04-.92-1.788L10.013.474c.214-.297.556-.474.92-.474h28.894c.92 0 1.456 1.04.92 1.788l-7.48 10.471c-1.07 1.498 0 3.579 1.842 3.579h11.377c.943 0 1.473 1.088.89 1.83L25.947 44.94z" fill="#a78bfa"/>
          </svg>
        </div>
        <div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 700, letterSpacing: '-0.5px', marginBottom: '6px' }}>About SubForge</h1>
          <p style={{ fontSize: '0.875rem', color: 'rgba(255,255,255,0.65)', lineHeight: 1.6 }}>Open-source AI subtitle generation — fast, private, and free to self-host.</p>
        </div>
      </div>

      {/* AI + Free highlight strip */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '28px',
      }}>
        <div style={{
          background: 'var(--color-primary-light)',
          border: `1px solid var(--color-primary-border)`, borderRadius: '14px', padding: '22px 24px',
          display: 'flex', gap: '16px', alignItems: 'flex-start',
        }}>
          <div style={{ width: '42px', height: '42px', background: 'var(--color-primary)', borderRadius: '11px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="white" strokeWidth="1.8" strokeLinejoin="round"/>
              <path d="M2 17l10 5 10-5M2 12l10 5 10-5" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--color-primary)', marginBottom: '5px', letterSpacing: '-0.2px' }}>AI-Powered Processing</div>
            <div style={{ fontSize: '0.77rem', color: 'var(--color-text-2)', lineHeight: 1.6 }}>Every subtitle is generated by a state-of-the-art AI model (OpenAI Whisper) running entirely on your infrastructure — no cloud, no third-party APIs.</div>
          </div>
        </div>
        <div style={{
          background: 'var(--color-success-light)',
          border: `1px solid var(--color-success-border)`, borderRadius: '14px', padding: '22px 24px',
          display: 'flex', gap: '16px', alignItems: 'flex-start',
        }}>
          <div style={{ width: '42px', height: '42px', background: 'var(--color-success)', borderRadius: '11px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M20 12V22H4V12" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 7H2v5h20V7z" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M12 22V7M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7zM12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--color-success)', marginBottom: '5px', letterSpacing: '-0.2px' }}>Completely Free</div>
            <div style={{ fontSize: '0.77rem', color: 'var(--color-text-2)', lineHeight: 1.6 }}>SubForge is MIT-licensed and free forever — no plans, no subscriptions, no usage caps. Self-host it on any machine and keep 100% of the value.</div>
          </div>
        </div>
      </div>

      {/* What is it */}
      <div style={{ marginBottom: '28px' }}>
        <SectionLabel>What is SubForge?</SectionLabel>
        <Card>
          {[
            { bg: C.primaryLight, color: C.primary, icon: <><path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" stroke="currentColor" strokeWidth="1.8"/><path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v3M8 22h8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></>, title: 'AI-powered transcription', desc: 'Upload any audio or video file and receive accurate subtitles in SRT, VTT, or JSON format. Powered by OpenAI\'s Whisper model via the faster-whisper (CTranslate2) runtime — the same AI used by professionals worldwide.' },
            { bg: C.successLight, color: C.success, icon: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>, title: '100% on-premise', desc: 'Nothing is sent to external APIs. The AI model runs entirely on your server using open-source weights. Your media files never leave the machine.' },
            { bg: C.blueLight, color: C.blue, icon: <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>, title: 'Free and open source', desc: 'SubForge is MIT-licensed. Inspect every line of code, self-host on your own infrastructure, or contribute improvements back to the project. No cost, ever.' },
          ].map((item, i, arr) => (
            <div key={i} style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', padding: '20px 24px', borderBottom: i < arr.length - 1 ? `1px solid ${C.border}` : 'none' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '9px', background: item.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: item.color }}>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none">{item.icon}</svg>
              </div>
              <div>
                <div style={{ fontSize: '0.84rem', fontWeight: 600, marginBottom: '4px' }}>{item.title}</div>
                <div style={{ fontSize: '0.78rem', color: C.text2, lineHeight: 1.6 }}>{item.desc}</div>
              </div>
            </div>
          ))}
        </Card>
      </div>

      {/* Features */}
      <div style={{ marginBottom: '28px' }}>
        <SectionLabel>Capabilities</SectionLabel>
        <Card>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1px', background: C.border }}>
            {FEATURES.map((f, i) => (
              <div key={i} style={{ background: C.surface, padding: '22px 20px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '9px', background: f.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '12px', color: f.color }}>
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none">{f.icon}</svg>
                </div>
                <div style={{ fontSize: '0.83rem', fontWeight: 600, marginBottom: '5px' }}>{f.title}</div>
                <div style={{ fontSize: '0.76rem', color: C.text2, lineHeight: 1.55 }}>{f.desc}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Stack */}
      <div style={{ marginBottom: '28px' }}>
        <SectionLabel>Technology Stack</SectionLabel>
        <Card>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {STACK.map(([layer, [tags, desc]], i) => (
                <tr key={i} style={{ borderBottom: i < STACK.length - 1 ? `1px solid ${C.border}` : 'none', background: i % 2 === 1 ? C.surface2 : C.surface }}>
                  <td style={{ padding: '12px 20px', width: '28%', fontWeight: 600, fontSize: '0.79rem' }}>{layer}</td>
                  <td style={{ padding: '12px 20px', fontSize: '0.8rem', color: C.text2 }}>
                    {(tags as readonly string[]).map(t => <span key={t} style={TAG_STYLE}>{t}</span>)}
                    {' '}{desc}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>

      {/* CTA */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '16px', padding: '36px', textAlign: 'center', boxShadow: '0 1px 3px rgba(0,0,0,0.07)' }}>
        <div style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '8px', letterSpacing: '-0.3px' }}>Ready to get started?</div>
        <div style={{ fontSize: '0.83rem', color: C.text2, marginBottom: '20px' }}>Drop an audio or video file to generate subtitles instantly — no sign-up required.</div>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <a href="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', padding: '9px 20px', borderRadius: '10px', fontSize: '0.82rem', fontWeight: 600, textDecoration: 'none', background: 'var(--color-primary)', color: '#fff', boxShadow: '0 4px 20px rgba(59,130,246,0.35)' }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 3l14 9-14 9V3z" fill="white"/></svg>
            Open SubForge
          </a>
          <a href="https://github.com/volehuy1998/subtitle-generator" target="_blank" rel="noopener" style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', padding: '9px 20px', borderRadius: '10px', fontSize: '0.82rem', fontWeight: 600, textDecoration: 'none', background: C.surface, color: C.text, border: `1px solid ${C.border2}` }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            View on GitHub
          </a>
          <a href="/contact" style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', padding: '9px 20px', borderRadius: '10px', fontSize: '0.82rem', fontWeight: 600, textDecoration: 'none', background: C.surface, color: C.text, border: `1px solid ${C.border2}` }}>
            Contact us
          </a>
        </div>
      </div>
    </StaticPageLayout>
  )
}
