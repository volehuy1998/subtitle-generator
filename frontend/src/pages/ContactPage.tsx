/**
 * ContactPage — Contact information for SubForge.
 *
 * — Pixel (Sr. Frontend Engineer), Task 39
 */

import { AppShell } from '../components/layout/AppShell'
import { PageLayout } from '../components/layout/PageLayout'

export function ContactPage() {
  return (
    <AppShell>
      <PageLayout title="Contact" subtitle="Get in touch">
        <div className="space-y-4 text-[var(--color-text-secondary)]">
          <p>For support or feedback, open an issue on{' '}
            <a href="https://github.com/volehuy1998/subtitle-generator" className="text-[var(--color-primary)] hover:underline" target="_blank" rel="noreferrer">GitHub</a>.
          </p>
        </div>
      </PageLayout>
    </AppShell>
  )
}
