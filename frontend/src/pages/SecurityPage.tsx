/**
 * SecurityPage — Security information for SubForge.
 *
 * — Pixel (Sr. Frontend Engineer), Task 39
 */

import { AppShell } from '../components/layout/AppShell'
import { PageLayout } from '../components/layout/PageLayout'

export function SecurityPage() {
  return (
    <AppShell>
      <PageLayout title="Security" subtitle="How we protect your data">
        <div className="space-y-4 text-[--color-text-secondary]">
          <p>Uploaded files are processed in memory and deleted after {'{'} FILE_RETENTION_HOURS {'}'} hours.</p>
          <p>All connections use HTTPS with HSTS in production.</p>
          <p>To report a vulnerability, please see our{' '}
            <a href="/SECURITY.md" className="text-[--color-primary] hover:underline">security policy</a>.
          </p>
        </div>
      </PageLayout>
    </AppShell>
  )
}
