# SubForge — Long-Term Development Plan

> **Owner:** Atlas (Tech Lead) · **Last updated:** 2026-03-16 · **Status:** Active

This document captures the investor's long-term vision and engineering priorities for SubForge. All items here are approved directions — implementation begins when the investor gives the green light.

---

## Priority 1: UX Principles (Investor Directives)

### 1.1 User Confirmation Before Any Process

**Requirement:** Always ask for user confirmation before starting any process (upload, transcription, embedding, deletion, etc.). No action should start automatically without explicit user consent.

**Why:** Prevents accidental operations, gives users control over resource-intensive tasks, and builds trust.

**Implementation approach:**
- Add confirmation modal/dialog before upload starts transcription
- Add confirmation before embed/download operations that modify files
- Add confirmation before cancel/delete operations
- Keep the confirmation lightweight — one click, not a multi-step wizard

### 1.2 Brighter, Professional UI Design

**Requirement:** The interface should be brighter and lighter. Almost no large corporations use dark website colors — Microsoft, Red Hat, Cisco, Juniper, Claude, Google, Facebook all use light themes.

**Why:** Professional appearance, accessibility (light backgrounds are easier to read for most users), corporate credibility.

**Implementation approach:**
- Use the `feature-dev` plugin for guided feature development
- Reference: Microsoft Fluent, Google Material Design 3, Anthropic Claude UI
- Light background (#FFFFFF or #F8F9FA), subtle gray accents, colored CTAs
- High contrast text (dark on light), clean typography
- Remove dark theme elements from current React SPA
- Keep the current Jinja template's light design philosophy as inspiration (it already follows this pattern)

**Note:** The current Jinja templates (`templates/index.html`) already have a brighter, lighter design compared to the React SPA's Enterprise Slate dark theme. The React SPA needs to be updated to match this direction.

### 1.3 Process Liveness Indicator

**Requirement:** Users need to know if a process/stage is actively running or if it's frozen/stuck.

**Why:** Without liveness feedback, users can't distinguish between "working slowly" and "broken." They may refresh the page or re-upload, creating duplicate tasks.

**Implementation approach:**
- **Heartbeat indicator:** Animated pulse/spinner on the active step that shows the backend is still processing
- **Time-since-last-update:** Show "Last update: 3s ago" that ticks up. If it exceeds a threshold (e.g., 30s), show "This is taking longer than expected..."
- **Per-stage ETA:** Already partially implemented via `TranscriptionProfiler`. Surface the ETA in the UI with a live countdown.
- **Segment counter:** During transcription, show "Processing segment 14 of ~29" with real-time updates
- **Backend heartbeat:** SSE events every 3-5 seconds during processing (even if no new segment is ready) to confirm the connection is alive

---

## Priority 2: Transcription & Model Loading Optimization

### 2.1 Current Performance Baseline

| Step | First Run | Cached | Bottleneck? |
|------|-----------|--------|-------------|
| Model download + load | 60-120s | 1-5s | **MAJOR** |
| Audio extraction (ffmpeg) | 5-30s | N/A | Medium |
| Transcription | Variable (0.3x-5x real-time) | N/A | Core work |
| Probe | <0.5s | N/A | No |

### 2.2 Model Loading Improvements

**Problem:** First request on any model size = 60-120s wait. Users see "Loading model..." for 2 minutes.

**Approach A — Smart Preloading (Recommended):**
- Preload the most commonly used model at startup (`PRELOAD_MODEL=base`)
- Background-load additional models during idle time
- Show model readiness status in UI (green = ready, yellow = loading, gray = not loaded)
- Allow users to see which models are loaded before choosing

**Approach B — Progressive Loading:**
- Start transcription with `tiny` model immediately (always preloaded, 0.5GB)
- While user reviews `tiny` results, background-load the selected model
- Re-transcribe with the better model when ready
- User gets fast initial results + high-quality final results

**Approach C — Model Pool Management:**
- LRU eviction when memory pressure detected
- Auto-unload models unused for >30 minutes
- VRAM-aware model selection (don't load `large` if only 4GB VRAM free)
- Dashboard showing loaded models and memory usage

### 2.3 Transcription Speed Improvements

| Optimization | Impact | Effort | Risk |
|-------------|--------|--------|------|
| Beam size auto-tuning based on audio quality | 10-30% faster | Medium | Low |
| Batch processing for multiple files | 2-3x throughput | High | Medium |
| VAD filter tuning (currently always-on 500ms) | 5-10% faster | Low | Low |
| Compute type auto-selection based on VRAM | Better GPU utilization | Medium | Low |
| Streaming transcription (process while extracting) | Reduced latency | High | Medium |

### 2.4 Architecture Improvements

- **Model warmup on health check:** Load default model when first health check arrives
- **VRAM monitoring:** Real-time GPU memory tracking, auto-downgrade compute type if tight
- **Request coalescing:** Queue multiple uploads for same model, process sequentially to avoid model switching
- **Distributed workers:** Celery workers with dedicated model assignments (worker-1 = large, worker-2 = base+small)

---

## Priority 3: Open Engineering Backlog

From DVS deployment verification and ongoing development:

| # | Item | Priority | Status |
|---|------|----------|--------|
| 1 | API key hash migration (SHA-256 → HMAC-SHA256) | P1 | Blocker for prod API auth |
| 2 | Service runs as root on bare-metal | P1 | Security hardening |
| 3 | `process_video()` refactoring (514 lines → step functions) | P2 | Technical debt |
| 4 | Video preservation for post-transcription embed | P2 | Feature gap in Jinja UI |
| 5 | Download returns 404 for 0-segment transcriptions | P2 | UX issue |
| 6 | Distributed deployment (5-server plan) | P2 | Not started |
| 7 | SLOs definition | P3 | Operational maturity |
| 8 | mypy/pyright in CI | P3 | Type safety |
| 9 | Pin TruffleHog action SHA | P3 | Supply chain security |

---

## Implementation Sequence

When the investor is ready to proceed:

1. **Phase 1 — UX Foundation** (1.1 + 1.2 + 1.3)
   - User confirmation dialogs
   - Bright/light UI redesign (feature-dev plugin)
   - Process liveness indicators
   - Tool: `feature-dev` plugin for guided implementation

2. **Phase 2 — Performance** (2.2 + 2.3)
   - Smart model preloading
   - Transcription speed optimizations
   - Model pool management

3. **Phase 3 — Infrastructure** (2.4 + backlog)
   - Distributed workers
   - API key migration
   - Security hardening

---

## Design References

| Company | UI Style | Key Elements |
|---------|----------|-------------|
| Microsoft (Fluent) | Light, clean, rounded corners | White backgrounds, blue accents, subtle shadows |
| Google (Material 3) | Light, colorful, dynamic | Surface colors, tonal palettes, rounded shapes |
| Claude (Anthropic) | Light, warm, minimal | Cream/white backgrounds, orange accents, generous spacing |
| Red Hat | Light, professional | White backgrounds, red CTAs, clean typography |

These should guide the UI redesign in Phase 1.
