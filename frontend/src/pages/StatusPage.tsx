/**
 * StatusPage — System status overview.
 *
 * — Pixel (Sr. Frontend Engineer), Task 39
 */

import { AppShell } from '../components/layout/AppShell'
import { PageLayout } from '../components/layout/PageLayout'

export function StatusPage() {
  return (
    <AppShell>
      <PageLayout title="System Status" subtitle="Real-time service health">
        <p className="text-[--color-text-secondary]">All systems operational.</p>
        <p className="text-sm text-[--color-text-muted] mt-4">
          For live status, visit the{' '}
          <a href="/status" className="text-[--color-primary] hover:underline">status dashboard</a>.
        </p>
      </PageLayout>
    </AppShell>
  )
}
