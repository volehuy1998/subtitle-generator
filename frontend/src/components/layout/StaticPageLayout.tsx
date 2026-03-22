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
      {healthPanelOpen && (
        <HealthPanel health={health} onClose={() => setHealthPanelOpen(false)} />
      )}
      <main style={{ maxWidth: '860px', margin: '0 auto', padding: '40px 24px 80px' }}>
        {children}
      </main>
    </div>
  )
}
