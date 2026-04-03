# Product Strategy

**Owner**: Atlas, Tech Lead -- Team Sentinel
**Updated**: 2026-04-03

## Vision

Make every piece of audio and video content accessible to every person on Earth, regardless of language or ability.

## Mission

Build a production-grade, self-hostable subtitle generation platform that combines state-of-the-art speech recognition with neural machine translation and professional subtitle tooling.

## Target Users

| Segment | Needs | Scale |
|---------|-------|-------|
| Content Creators | Fast turnaround, multi-language, style control | Individual, high volume |
| Journalists | Accurate transcription, speaker ID, timestamped quotes | Small teams, precision-critical |
| Educators | Lecture transcription, translation, accessibility compliance | Institutions, batch processing |
| Enterprises | API integration, audit trails, SLAs, on-premise deployment | Large orgs, compliance-heavy |
| Accessibility Advocates | WCAG compliance, accurate captions, SDH support | NGOs, government, regulated |
| Localization Studios | Batch translation, style consistency, QA workflows | Professional, high throughput |

## Priority Order

1. **Architecture and Performance** -- optimal data processing, minimal user wait time
2. **Security** -- production-grade input validation and error handling
3. **Features** -- user-facing functionality and UX improvements

## Competitive Positioning

| Dimension | SubForge | Cloud APIs (Google, AWS) | SaaS (Otter, Descript) |
|-----------|----------|--------------------------|------------------------|
| Self-hostable | Yes | No | No |
| Offline capable | Yes (all models local) | No | No |
| Data privacy | Full control | Third-party processing | Third-party storage |
| Languages | 99 transcription + Argos translation | Varies | Limited |
| Cost model | One-time infra cost | Per-minute billing | Monthly subscription |
| Customization | Full source access | API only | None |

## Key Differentiators

- **Self-hosted and offline**: no data leaves your infrastructure
- **Full pipeline in one tool**: transcribe, translate, diarize, embed, and download
- **Real-time feedback**: SSE/WebSocket progress with per-stage timing
- **Professional subtitle tooling**: style presets, soft/hard embed, format flexibility
- **Production-ready**: PostgreSQL persistence, rate limiting, audit logging, health monitoring

## Feature Tiers

### Tier 1 -- Core (zero tolerance for bugs)
File upload, transcription (5 models), SRT/VTT/JSON download, real-time progress, error handling

### Tier 2 -- Essential (high value)
Translation (Whisper + Argos), soft/hard embed, model selection, auto-embed, task control

### Tier 3 -- Professional (differentiation)
Speaker diarization, style presets, analytics dashboard, status page, audit logging

## Scale Targets

| Dimension | Current | Target |
|-----------|---------|--------|
| Languages | 99 transcription | + 50 translation pairs via Argos |
| Deployment | Single server | Multi-region (US, EU, AP) |
| Compliance | Basic | GDPR, CCPA, Section 508 |

## Success Metrics

| Metric | Target |
|--------|--------|
| Transcription accuracy | Within 5% WER of OpenAI Whisper baseline |
| Upload-to-subtitle time | Under 2x audio duration (large model, CPU) |
| System uptime | 99.9% |
| Test coverage | 80%+ (currently 3,667 tests) |
| Zero-downtime deploys | All production updates via rolling deploy |
