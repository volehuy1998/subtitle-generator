# Phase Lumen — SubForge Quality & Design Overhaul

> **Codename:** Lumen (Latin: "light") · **Status:** Planning · **Owner:** Atlas (Tech Lead)
> **Development subdomain:** `lumen.openlabs.club`
> **Production target:** `openlabs.club` (promoted when investor approves)
> **Scale:** Hundreds of sprints · Dozens of continuous working hours

---

## Vision

Transform SubForge from a functional tool into a **professional-grade product** that stands alongside enterprise software from Microsoft, Google, and Anthropic — zero bugs, instant responsiveness, and a UI that communicates trust and quality.

## Three Pillars

```
┌─────────────────────────────────────────────────────────────┐
│                     PHASE LUMEN                              │
├───────────────────┬───────────────────┬─────────────────────┤
│    STABILITY      │   PERFORMANCE     │      DESIGN         │
│  Zero bugs        │  Zero wait        │  Professional UI    │
│  Rich testing     │  Instant feedback │  Enterprise quality │
│  Edge case proof  │  Smart preloading │  Light & bright     │
└───────────────────┴───────────────────┴─────────────────────┘
```

---

## Pillar 1: Stability — Zero Bugs

### 1.1 Advanced Test Suite

**Goal:** Every feature tested with real-world data that breaks things.

#### Test Data Categories

| Category | Examples | What It Tests |
|----------|---------|---------------|
| **Multilingual** | Chinese, Arabic, Hindi, Japanese, mixed-language audio | Language detection, Unicode handling, RTL text |
| **Accents & Dialects** | British, Australian, Indian English, Southern US, Scottish | Transcription accuracy under accent variation |
| **Background Noise** | Music, crowd noise, traffic, echo, wind | VAD filter effectiveness, hallucination prevention |
| **Edge Cases** | 0.5s audio, 4-hour lecture, silence-only, corrupt files | Boundary conditions, timeout handling, error recovery |
| **File Formats** | MP3 VBR, FLAC, OGG, WebM, MKV with multiple tracks | Format support, ffmpeg extraction, codec handling |
| **Large Files** | 500MB, 1GB, 2GB (limit) | Upload handling, memory pressure, progress accuracy |
| **Concurrent** | 3 simultaneous uploads, rapid cancel/restart | Race conditions, semaphore correctness, state consistency |
| **Network** | Slow upload, connection drop mid-upload, SSE reconnect | Resilience, session recovery, graceful degradation |

#### Test Infrastructure

```
tests/
├── test_lumen/
│   ├── fixtures/                    # Real audio samples (gitignored, downloaded in CI)
│   │   ├── multilingual/            # 10+ languages
│   │   ├── accents/                 # 8+ English accents
│   │   ├── noisy/                   # Background noise variants
│   │   ├── edge_cases/              # Boundary conditions
│   │   └── large_files/             # 100MB+ test files
│   ├── test_transcription_accuracy.py    # WER measurement against known transcripts
│   ├── test_language_detection.py        # Auto-detect accuracy across 20+ languages
│   ├── test_format_output.py             # SRT/VTT/JSON correctness per specification
│   ├── test_upload_resilience.py         # Network failure, corrupt files, size limits
│   ├── test_concurrent_pipeline.py       # Race conditions, state consistency
│   ├── test_embedding_integrity.py       # Soft mux + hard burn output verification
│   ├── test_translation_quality.py       # Argos translation output validation
│   └── test_sse_liveness.py              # SSE heartbeat, reconnection, event ordering
```

#### Quality Metrics

| Metric | Target | Current | How Measured |
|--------|--------|---------|-------------|
| Test count | 2000+ | 1328 | `pytest --co -q` |
| Code coverage | >85% | Unknown | `pytest --cov` |
| WER (Word Error Rate) on English | <5% (base model) | Not measured | Standard WER calculation |
| E2E test pass rate | 100% | Not running regularly | Playwright CI |
| Regression rate | 0 | 0 | CI on every PR |

### 1.2 Error Handling Hardening

| Scenario | Current Behavior | Lumen Target |
|----------|-----------------|--------------|
| Upload corrupt file | ffmpeg error with 500-char banner | Human-readable error: "This file appears to be damaged" |
| Model download fails | Task stuck in "loading" | Retry 3x, then: "Model unavailable, try a smaller model" |
| Disk full during transcription | Unhandled exception | Graceful: "Storage full — please free space or reduce file size" |
| SSE connection drops | UI shows stale progress | Auto-reconnect with state recovery |
| 0 segments transcribed | 404 on download | Empty SRT with header comment: "No speech detected" |
| Concurrent model switch | Potential deadlock | Queue-based model loading with timeout |

### 1.3 Input Validation

- File magic bytes verification (not just extension)
- Audio stream detection (reject video-only without audio)
- Duration estimation before extraction (reject >4hr files early)
- Character encoding validation on subtitle output

---

## Pillar 2: Performance — Zero Wait

### 2.1 Model Loading Strategy

**Current:** First request = 60-120s cold start. Users stare at "Loading model..."

**Lumen:**

```
Server Start
    │
    ├──► Preload default model (base) in background
    │    Server accepts connections immediately
    │
    ├──► UI shows model readiness:
    │    ● Tiny    [Ready]     75MB
    │    ● Base    [Loading…]  140MB
    │    ● Small   [Not loaded] 460MB
    │    ● Medium  [Not loaded] 1.5GB
    │    ● Large   [Not loaded] 3GB
    │
    ├──► User selects model → if not loaded:
    │    "This model needs ~30s to load. Start now?"
    │    [Load & Transcribe] [Use Ready Model Instead]
    │
    └──► Smart preloading during idle:
         After 5 min idle, preload next most-used model
```

### 2.2 Pipeline Optimization

| Stage | Current | Lumen Target | How |
|-------|---------|-------------|-----|
| Probe | 0.1-0.5s | <0.1s | Cache ffprobe results |
| Extract | 5-30s | 2-10s | Stream extraction, skip if WAV input |
| Model load | 1-5s (cached) | <0.5s (pre-warmed) | Keep model in GPU/CPU memory |
| Transcribe | Variable | 10-30% faster | Beam size auto-tuning, VAD optimization |
| Write output | 0.1-1s | <0.1s | Async file writes |

### 2.3 User-Perceived Performance

Even when actual processing takes time, the UI should never feel frozen:

| Technique | Implementation |
|-----------|---------------|
| **Instant acknowledgment** | Upload accepted → show file info + model card immediately |
| **Progressive results** | Show segments as they arrive (already implemented via SSE) |
| **Heartbeat pulse** | Animated indicator on active step — proves system is alive |
| **Time-since-update** | "Last update: 2s ago" — resets on every SSE event |
| **Stale warning** | After 30s no update: "This is taking longer than expected…" |
| **Segment counter** | "Processing segment 14 of ~29" with live updates |
| **ETA countdown** | "~12 seconds remaining" based on TranscriptionProfiler |
| **Cancel anytime** | Cancel button always visible and responsive |

---

## Pillar 3: Design — Professional UI

### 3.1 Design Philosophy

**Principle:** If a Fortune 500 company wouldn't ship this UI, neither do we.

**Reference companies (study before every design decision):**

| Company | What to Learn | URL |
|---------|--------------|-----|
| Microsoft 365 | Clean layout, subtle shadows, blue accents on white | office.com |
| Google Workspace | Material Design 3, surface colors, rounded shapes | workspace.google.com |
| Anthropic Claude | Warm whites, generous spacing, orange accents | claude.ai |
| Vercel | Developer-focused clean design, dark/light toggle | vercel.com |
| Linear | Task management UX, keyboard shortcuts, speed | linear.app |
| Notion | Content-focused, minimal chrome, clear hierarchy | notion.so |

### 3.2 Color System

```
Background:     #FFFFFF (primary), #F8FAFC (surface), #F1F5F9 (subtle)
Text:           #0F172A (primary), #475569 (secondary), #94A3B8 (muted)
Brand:          #6366F1 (indigo — primary action), #8B5CF6 (purple — accent)
Success:        #10B981 (emerald)
Warning:        #F59E0B (amber)
Error:          #EF4444 (red)
Border:         #E2E8F0 (subtle), #CBD5E1 (emphasis)
```

### 3.3 Typography

```
Font:           Inter (Google Fonts) — clean, professional, excellent readability
Headings:       600 weight, #0F172A
Body:           400 weight, #475569
Mono (code):    JetBrains Mono — for timestamps, segment text
Size scale:     12px / 14px / 16px (base) / 18px / 20px / 24px / 32px
Line height:    1.5 (body), 1.3 (headings)
```

### 3.4 Component Design

#### Header
```
┌─────────────────────────────────────────────────────────┐
│  🔷 SubForge          App  Status  About    ● Healthy  │
└─────────────────────────────────────────────────────────┘
- White background, subtle bottom border
- Logo + wordmark left, navigation center, health indicator right
- Active page underlined in brand color
- No GPU badge (distracting, non-essential)
```

#### Transcription Form
```
┌─────────────────────────────────────────────────────────┐
│  ┌─ Transcribe ─┐  ┌─ Embed ─┐                        │
│  │              │  │         │                         │
│  └──────────────┘  └─────────┘                        │
│                                                        │
│  Model     ○ Tiny  ○ Base  ● Small  ○ Medium  ○ Large │
│            Ready    Ready   Ready    Loading   —       │
│                                                        │
│  Language  [ Auto-detect          ▼ ]                  │
│  Format    [ SRT ▼ ]   Translate [ No ▼ ]             │
│                                                        │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐ │
│  │          Drop files here or browse                │ │
│  │       MP4, MKV, AVI, MP3, WAV · Max 2GB          │ │
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘ │
│                                                        │
│  ┌─ Confirmation ──────────────────────────────────┐  │
│  │  Ready to transcribe "video.mp4" (59.5 MB)     │  │
│  │  Model: Small (460MB) · Format: SRT · Lang: Auto│  │
│  │                                                  │  │
│  │  [ Cancel ]              [ Start Transcription ] │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

#### Progress View
```
┌─────────────────────────────────────────────────────────┐
│  videoplayback.mp4                           59.5 MB   │
│                                                        │
│  ① Upload ──── ② Extract ──── ③ Transcribe ──── ✓ Done│
│    0.1s          0.2s          ● 3.8s / ~12s           │
│                                                        │
│  ████████████████████░░░░░░░░░  67%  ~4s remaining    │
│                                         ● Live (2s ago)│
│                                                        │
│  SEGMENTS (14 of ~29)                                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 1:40.1 → 1:44.4  Monday, Tuesday, Wednesday... │   │
│  │ 1:44.4 → 1:48.4  Now if you want to learn...   │   │
│  │ 1:48.4 → 1:50.4  without having to have that...│   │
│  └─────────────────────────────────────────────────┘   │
│                                                        │
│  [ Cancel Transcription ]                              │
└────────────────────────────────────────────────────────┘
```

### 3.5 User Confirmation Rule

**Every action that starts a process requires explicit user confirmation:**

| Action | Confirmation UI |
|--------|----------------|
| Start transcription | Summary card: file, model, format, language → [Start] |
| Embed subtitles | Preview styling → "Embed into video?" → [Embed & Download] |
| Cancel running task | "Cancel transcription of video.mp4?" → [Keep Going] [Cancel] |
| Delete task | "Remove this task and its files?" → [Keep] [Delete] |
| Switch model mid-queue | "Switching model will restart. Continue?" → [Keep Current] [Switch] |

### 3.6 Liveness Indicators

Every active process shows proof of life:

```
● Live (2s ago)         — Green dot + time since last SSE event
◐ Processing...         — Animated spinner on active step
⚠ Slow (45s ago)       — Yellow warning after 30s no update
✕ Connection lost      — Red, with auto-reconnect countdown
```

---

## Sprint Structure

### Sprint Numbering

Phase Lumen sprints are numbered `L1`, `L2`, `L3`, etc. (separate from the existing S1-S30 numbering).

### Sprint Categories

| Category | Sprint Range | Focus |
|----------|-------------|-------|
| **Foundation** | L1-L10 | Test infrastructure, CI improvements, fixture pipeline |
| **Performance** | L11-L20 | Model preloading, pipeline optimization, caching |
| **Design System** | L21-L40 | Color system, typography, component library, layouts |
| **Feature Polish** | L41-L60 | Confirmation dialogs, liveness indicators, error messages |
| **Integration** | L61-L80 | End-to-end testing, cross-browser, responsive |
| **Hardening** | L81-L100 | Load testing, stress testing, edge cases, security review |
| **Final Polish** | L100+ | Pixel-perfect refinement, animation, microinteractions |

### Each Sprint Delivers

1. Specific functionality on `lumen.openlabs.club`
2. Tests proving it works
3. PR with engineer reviews
4. Investor can preview at any time

### Quality Gate (Before Promotion to Production)

| Check | Requirement |
|-------|-------------|
| All tests pass | 2000+ tests, 0 failures |
| E2E Playwright pass | Full user journey tested |
| Performance baseline | Model load <5s (cached), transcription within 2x real-time |
| Cross-browser | Chrome, Firefox, Safari, Edge |
| Mobile responsive | 375px, 768px, 1024px, 1440px |
| Accessibility | WCAG 2.1 AA |
| Security headers | All present and correct |
| Investor approval | Explicit sign-off on lumen.openlabs.club |

---

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend framework | React 19 + TypeScript | Already in place, mature ecosystem |
| Styling | Tailwind CSS v4 | Utility-first, fast iteration, design system tokens |
| State management | Zustand | Already in place, simple, performant |
| Testing (backend) | pytest + real audio fixtures | Comprehensive, existing infrastructure |
| Testing (frontend) | Vitest + Playwright | Fast unit tests + real browser E2E |
| Testing (visual) | Playwright screenshot comparison | Catch visual regressions |
| Design reference | `feature-dev` plugin | Guided feature development with design focus |
| Build | Vite 6 | Already in place, fast HMR |

---

## File Structure (New)

```
docs/
└── lumen/
    ├── PHASE_LUMEN.md          # This document
    ├── DESIGN_SYSTEM.md        # Color, typography, spacing tokens
    ├── COMPONENT_LIBRARY.md    # Component specs and usage
    └── SPRINT_LOG.md           # Sprint-by-sprint progress log

tests/
└── test_lumen/
    ├── fixtures/               # Real audio test data (gitignored)
    ├── conftest.py             # Lumen-specific test setup
    └── test_*.py               # Feature-specific tests
```

---

## Development Workflow

```
main branch (production — openlabs.club)
    │
    └──► feat/lumen-L1-test-infrastructure
         feat/lumen-L2-model-preloading
         feat/lumen-L3-color-system
         ...
         │
         └──► Merge to main → auto-deploys to lumen.openlabs.club
              (Docker newui profile or dedicated Lumen profile)
              │
              └──► Investor reviews on lumen.openlabs.club
                   │
                   └──► Approved → promote to openlabs.club production
```

---

## Success Criteria

Phase Lumen is complete when:

1. **Zero known bugs** — every reported issue resolved
2. **2000+ tests passing** — including real-world audio fixtures
3. **Model loads in <5s** — preloaded, with readiness indicators
4. **UI matches enterprise standards** — brighter, cleaner than current
5. **Every action requires confirmation** — no surprise processes
6. **Every process shows liveness** — users always know the system is working
7. **Investor approves** — explicit sign-off after reviewing `lumen.openlabs.club`
8. **Cross-browser and mobile tested** — Chrome, Firefox, Safari, Edge + responsive

---

*Phase Lumen: Where clarity meets quality.*
