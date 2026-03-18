/**
 * AboutPage — Information about SubForge.
 *
 * — Pixel (Sr. Frontend Engineer), Task 39
 */

import { AppShell } from '../components/layout/AppShell'
import { PageLayout } from '../components/layout/PageLayout'

export function AboutPage() {
  return (
    <AppShell>
      <PageLayout title="About SubForge" subtitle="AI-powered subtitle generation">
        <div className="space-y-4 text-[--color-text-secondary]">
          <p>SubForge uses faster-whisper (CTranslate2) to transcribe audio and video into accurate subtitles.</p>
          <p>Upload any media file and get SRT, VTT, or JSON subtitles in seconds.</p>
          <p>Features: speaker diarization, translation, subtitle embedding, and more.</p>
        </div>
      </PageLayout>
    </AppShell>
  )
}
