import { AppHeader } from './AppHeader'
import { HealthPanel } from '@/components/system/HealthPanel'
import { useUIStore } from '@/store/uiStore'

interface Props {
  children: React.ReactNode
}

export function StaticPageLayout({ children }: Props) {
  const { healthPanelOpen, setHealthPanelOpen, health } = useUIStore()

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--color-bg)',
      fontFamily: 'var(--font-family-sans)',
      fontSize: '14px',
      color: 'var(--color-text)',
      WebkitFontSmoothing: 'antialiased',
    }}>
      <AppHeader />
      {healthPanelOpen && (
        <HealthPanel health={health} onClose={() => setHealthPanelOpen(false)} />
      )}
      <main style={{ maxWidth: '860px', margin: '0 auto', padding: '40px 24px 80px' }}>
        {children}
      </main>
      <footer style={{
        borderTop: '1px solid var(--color-border)',
        marginTop: '64px',
        padding: '22px 24px',
        textAlign: 'center',
        fontSize: '0.73rem',
        color: 'var(--color-text-3)',
      }}>
        &copy; 2026 SubForge &mdash; Open-source subtitle generator &mdash;{' '}
        <a href="https://github.com/volehuy1998/subtitle-generator" target="_blank" rel="noopener"
          style={{ color: 'var(--color-text-3)' }}
          onMouseEnter={e => (e.currentTarget.style.color = 'var(--color-primary)')}
          onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-text-3)')}
        >GitHub</a>
      </footer>
    </div>
  )
}
