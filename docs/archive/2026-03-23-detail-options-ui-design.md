# Detail Options UI Design

**Date**: 2026-03-23
**Author**: Atlas (Tech Lead)
**Status**: Approved

## Goal

Maximize information density and user control across the SubForge UI. Show all options upfront, enrich every control with context, display comprehensive results metadata at three levels of detail, and replace disruptive connection banners with a compact header health dot popover.

## Scope

| # | Feature | Branch | Priority |
|---|---------|--------|----------|
| 1 | Two-column landing layout | `feat/editorial-redesign` | P1 |
| 2 | Rich option tooltips + badges | `feat/editorial-redesign` | P1 |
| 3 | Output format selector (SRT/VTT/JSON pills) | `feat/editorial-redesign` | P1 |
| 4 | Max line chars slider with live preview | `feat/editorial-redesign` | P2 |
| 5 | Health dot popover (replace banners) | Both branches | P1 |
| 6 | Info bar above editor | `feat/editorial-redesign` | P1 |
| 7 | Sidebar metadata panel | `feat/editorial-redesign` | P1 |
| 8 | Segment-level detail (confidence, speakers) | `feat/editorial-redesign` | P2 |

## Backend Changes Required (Minimal)

The frontend needs data the backend doesn't currently expose. These are targeted additions to existing code, not architectural changes.

### 1. Capture segment confidence (`app/services/transcription.py`)
Add `avg_logprob` (or computed 0-100 confidence) to each `seg_dict` in the transcription loop. Propagate through SSE `segment` events and `GET /subtitles/{task_id}` JSON response.

### 2. Store ffprobe metadata on task (`app/services/pipeline.py`)
After the probe step, store `task['metadata'] = probe_result` so frontend can display codec, resolution, sample rate, frame rate.

### 3. Add `language_probability` and `speakers` to done event
The `done` SSE event payload should include `language_probability` (float 0-1 from faster-whisper's `TranscriptionInfo`) and `speakers` (int, already in task dict).

### 4. Persist speaker labels in JSON output
Speaker labels exist during transcription but are lost when segments are re-parsed from SRT. Store in JSON format output and load from there in the editor.

## Not in Scope

- No new API endpoints
- No pipeline architecture changes
- No changes to Settings page or static pages

---

## Feature 1: Two-Column Landing Layout

Replace the current stacked layout (upload zone + collapsed "Advanced options") with a side-by-side two-column layout.

**Desktop (>768px):**
- Left column (60%): Upload drop zone — centered, generous padding
- Right column (40%): Options panel — all controls visible, no collapsible

**Mobile (<768px):**
- Stacks vertically: upload zone on top, options below

**Below both columns:** Recent Projects grid (unchanged).

```
┌──────────────────────┬──────────────────────┐
│                      │  Model      [Large ▾]│
│   Drop your file     │  Language   [auto   ]│
│   here               │  Format    (SRT)(VTT)│
│   or click to browse │  Max chars  [===42==]│
│                      │  ☐ Diarization       │
│   MP4, MKV, MOV...   │  ☐ Word timestamps   │
│   Up to 2GB          │  ☐ Translate         │
│                      │  Prompt  [________]  │
├──────────────────────┴──────────────────────┤
│              Recent Projects                 │
└──────────────────────────────────────────────┘
```

## Feature 2: Rich Option Tooltips + Badges

Every control in the options panel gets:

1. **Label** (bold, `--color-text`)
2. **Description** (muted, below label, `--color-text-muted`)
3. **ℹ️ icon** that shows a tooltip on hover with recommendation and impact

### Model Select

Each option in the dropdown shows:
- Model name + parameter count
- Speed indicator (bar or text like "~10x realtime")
- Accuracy indicator (WER percentage)
- Badge: "⚡ Fastest" (Tiny), "⚖️ Balanced" (Small), "🎯 Best" (Large)

Tooltip: "Controls transcription quality vs speed. Large (1.5GB) gives best results but is ~2x slower than Small."

### Language Input

- Autocomplete dropdown with common languages + flag emoji
- Tooltip: "Specifying the language improves accuracy by ~15% vs auto-detection. Use ISO 639-1 codes (en, fr, de, ja, zh)."

### Output Format (NEW)

- Radio pill group: `SRT` | `VTT` | `JSON`
- Each pill has a tooltip:
  - SRT: "Universal subtitle format. Compatible with all video players."
  - VTT: "Web-native format with styling support. Best for HTML5 video."
  - JSON: "Structured data with timestamps, confidence scores, and word-level detail."

### Max Line Characters (NEW on landing)

- Slider (20-80), default 42
- Live preview below: renders a sample subtitle line at the current character count
- Tooltip: "Controls line wrapping. 42 is standard for broadcast. Shorter = more lines, easier to read on small screens."

### Speaker Diarization

- Switch toggle
- Description: "Identify and label different speakers"
- Tooltip: "Uses pyannote to detect speaker changes. Adds ~30% processing time. Best for interviews, meetings, podcasts."

### Word-Level Timestamps

- Switch toggle
- Description: "Generate timestamps for each word"
- Tooltip: "Enables per-word timing for karaoke-style display and precise editing. Minimal performance impact."

### Translate to English

- Switch toggle
- Description: "Whisper built-in translation (any → English)"
- Tooltip: "Higher quality than post-transcription translation. Only supports target=English. For other languages, use the Translate panel after transcription."

### Initial Prompt

- Textarea (3 rows, 500 char limit)
- Description: "Context hints to improve accuracy"
- Tooltip: "Give Whisper domain context: technical terms, speaker names, expected content. Example: 'Medical conference about cardiology. Speakers: Dr. Smith, Dr. Lee.'"

## Feature 3: Health Dot Popover (Both Branches)

Remove `ConnectionBanner` from page content. Remove `HealthPanel` drawer. Replace with a **popover card** anchored to the existing health dot in the header.

### Dot States

| State | Color | Animation | Tooltip (hover) |
|-------|-------|-----------|-----------------|
| Healthy + SSE connected | Green | Solid | "All systems healthy" |
| SSE reconnecting | Amber | Pulse | "Reconnecting in {n}s..." |
| Model loading | Blue | Pulse | "Loading: {model} ({percent}%)" |
| System critical | Red | Pulse | "System critical: {reason}" |
| Disconnected | Grey | None | "Disconnected" |

### Click Popover

Clicking the dot opens a small card (280px wide) with:

```
┌─────────────────────────┐
│ System Health        🟢 │
│ Status: Healthy         │
│ Uptime: 2h 15m          │
│ SSE: Connected          │
│                         │
│ CPU  [████░░░░░] 38%    │
│ RAM  [██████░░░] 62%    │
│ Disk [████████░] 82%    │
│                         │
│ Active tasks: 0 / 3     │
│ Models: large (loaded)  │
│                         │
│ Last check: 2s ago      │
│         [Reconnect]     │
└─────────────────────────┘
```

- Auto-dismisses when clicking outside
- Updates in real-time via existing health SSE stream
- "Reconnect" button only visible when disconnected

### Implementation on Both Branches

The HealthDotPopover component is self-contained:
- `frontend/src/components/system/HealthDotPopover.tsx`
- Imports: `useUIStore` (health state), `useHealthStream` (SSE data)
- No dependencies on branch-specific components

Create once on `feat/editorial-redesign`, cherry-pick to `prod-editorial-nav`. Both branches already have `HealthIndicator.tsx` in the Header — replace it with `HealthDotPopover`.

## Feature 4: Info Bar (Above Editor)

After transcription completes, a compact horizontal bar appears above the subtitle editor showing key stats at a glance.

```
┌──────────────────────────────────────────────────────────────┐
│ 🎯 Large · 🌐 English (98%) · ⏱ 2m 34s · 📝 147 segments · 1,842 words │
└──────────────────────────────────────────────────────────────┘
```

- Fixed above the editor (scrolls with page, not sticky)
- Uses semantic color for confidence: green (>90%), amber (70-90%), red (<70%)
- Each stat is a pill/badge for visual separation
- Responsive: wraps to two lines on mobile

Data source: `task.model`, `task.language`, `task.audio_duration`, `task.segments.length`, word count computed client-side, `task.step_timings` for processing time.

## Feature 5: Sidebar Metadata Panel

A persistent right sidebar panel visible in the editor page, showing grouped metadata.

### Layout

```
┌──────────────────────────────┬─────────────────────┐
│                              │ 📋 File Info        │
│   Subtitle Editor            │ interview.mp4       │
│   (segments list)            │ Duration: 15:42     │
│                              │ Size: 84.2 MB       │
│                              │ Codec: AAC 44.1kHz  │
│                              │ Resolution: 1920×1080│
│                              │                     │
│                              │ ⚙️ Processing       │
│                              │ Model: large        │
│                              │ Device: CPU         │
│                              │ Total: 2m 34s       │
│                              │  · Probe    0.2s    │
│                              │  · Extract  1.8s    │
│                              │  · Load     12.4s   │
│                              │  · Transcribe 2m18s │
│                              │  · Format   0.3s    │
│                              │                     │
│                              │ 📊 Results          │
│                              │ Language: en (98%)  │
│                              │ Segments: 147       │
│                              │ Words: 1,842        │
│                              │ Speakers: 2         │
│                              │ Avg confidence: 94% │
│                              │                     │
│                              │ 📥 Export           │
│                              │ [SRT] [VTT] [JSON]  │
│                              │ [Embed subtitles]   │
└──────────────────────────────┴─────────────────────┘
```

### Sections

**File Info**: filename, duration, file size, codec, sample rate. For video: resolution, video codec, frame rate. Data from `task.metadata` (ffprobe output).

**Processing**: Model used, device (CPU/GPU), total processing time, per-step timing breakdown from `task.step_timings`. Visual: each step has a mini bar showing proportion of total time.

**Results**: Detected language + confidence, segment count, total word count, speaker count (if diarized), average confidence score with color indicator.

**Export**: Download buttons for each format (SRT, VTT, JSON). Embed subtitles button (opens embed panel).

### Responsive

- Desktop (>1024px): sidebar always visible, ~280px wide
- Tablet (768-1024px): sidebar collapses to an icon strip, click to expand as overlay
- Mobile (<768px): sidebar becomes a bottom sheet, swipe up to see

## Feature 6: Segment-Level Detail

Each subtitle segment row in the editor shows additional metadata inline.

### Segment Row Layout

```
┌──┬────────────────┬────────────────────────────┬──────┐
│1 │ 00:01:24,500   │ Hello, welcome to the show │  96% │
│  │ → 00:01:27,800 │                            │ 🔊S1 │
└──┴────────────────┴────────────────────────────┴──────┘
```

- **Index** (#): segment number
- **Timestamps**: start → end, editable
- **Text**: subtitle content, editable
- **Confidence**: percentage, color-coded (green >90%, amber 70-90%, red <70%)
- **Speaker**: label (S1, S2, etc.) if diarization was enabled, with speaker color coding

### Low-Confidence Highlighting

- Segments with confidence <70% get an amber left border
- Segments with confidence <50% get a red left border
- A "Jump to next low-confidence" button in the info bar for quick review

### Word-Level Detail (if word timestamps enabled)

Hovering over a word in the segment text shows a micro-tooltip: "0:01:25.120 → 0:01:25.450 (conf: 92%)"

**Performance note**: Word-level tooltips use event delegation on the segment container, not individual listeners per word. Only visible segments (virtualized list) have active handlers.

### Responsive (Mobile)

On mobile (<768px), confidence and speaker columns collapse into the segment text area:
- Confidence shown as a small colored dot before the text
- Speaker label shown as a prefix: "[S1] Hello, welcome..."

---

## Data Flow Clarifications

### Output Format Selector

The format selector (SRT/VTT/JSON pills) controls the **preferred download format** stored in `preferencesStore.preferredFormat`. The backend always generates all 3 formats regardless. The selector determines which format is pre-selected in download buttons and the Export section.

### Max Line Characters Slider

The slider value is sent as the `max_line_chars` query parameter on the upload request (the backend already accepts this parameter). Value is also persisted in `preferencesStore.maxLineChars` as the default for future uploads.

---

## Data Dependencies

| UI Element | Data Source | Available now? | Backend change needed? |
|------------|------------|----------------|----------------------|
| Model used | `task['model']` | Yes | No |
| Language | `task['language']` | Yes | No |
| Language confidence | `TranscriptionInfo.language_probability` | No | Yes — add to done event |
| Audio duration | `task['audio_duration']` | Yes | No |
| Step timings | `task['step_timings']` | Yes | No |
| Segment confidence | `segment.avg_logprob` | No | Yes — capture in transcription loop |
| Speaker labels | `segment.speaker` | Partial (SSE only) | Yes — persist in JSON output |
| File metadata (codec, resolution) | ffprobe result | No | Yes — store as `task['metadata']` |
| Word timestamps | `segment.words[]` | Yes (if enabled) | No |
| Processing device | `task['device']` | Yes | No |
| Speaker count | `task['speakers']` | Server-side only | Yes — add to done event |

---

## Store Schema Changes

### taskStore.ts additions

```typescript
// Add to TaskState:
metadata?: {
  codec?: string
  sampleRate?: number
  resolution?: string
  videoCodec?: string
  frameRate?: number
}
languageProbability?: number
speakers?: number

// Add to Segment type:
confidence?: number  // 0-100, computed from avg_logprob
speaker?: string     // "S1", "S2", etc.
```

### preferencesStore.ts (already has these)

- `preferredFormat`: 'srt' | 'vtt' | 'json' — used by FormatSelector
- `maxLineChars`: number — used by LineCharsSlider

---

## Loading / Empty / Error States

### Info Bar
- **During transcription**: Shows a skeleton bar with pulsing placeholders
- **On error**: Not shown (editor shows error state instead)
- **Session restore**: Shows available data, "—" for missing fields

### Sidebar Metadata Panel
- **During transcription**: Sections appear progressively as steps complete (File Info after probe, Processing updates in real-time, Results after done)
- **On error**: Processing section shows last completed step + "Failed at: {step}" in red
- **No data**: "Upload a file to see details"

### Health Dot Popover
- **Never connected**: Grey dot, popover shows "Connecting..." with spinner
- **Data loading**: Usage bars show skeleton shimmer until first SSE event arrives
- **SSE error**: Amber dot, popover shows last known data + "Last updated: {time}" + Reconnect button

### Segment-Level Detail
- **No confidence data**: Column hidden entirely (graceful degradation)
- **No speaker data**: Speaker column hidden
- **Both hidden**: Segment row looks identical to current design (no regression)

---

## Components to Create

| Component | File | Purpose |
|-----------|------|---------|
| `OptionsPanel` | `components/landing/OptionsPanel.tsx` | Right column with all controls |
| `ModelSelect` | `components/landing/ModelSelect.tsx` | Model dropdown with badges |
| `LanguageInput` | `components/landing/LanguageInput.tsx` | Autocomplete with flags |
| `FormatSelector` | `components/landing/FormatSelector.tsx` | SRT/VTT/JSON radio pills |
| `LineCharsSlider` | `components/landing/LineCharsSlider.tsx` | Slider with live preview |
| `InfoTooltip` | `components/ui/InfoTooltip.tsx` | Reusable ℹ️ tooltip |
| `HealthDotPopover` | `components/system/HealthDotPopover.tsx` | Header health dot + click popover |
| `InfoBar` | `components/editor/InfoBar.tsx` | Stats strip above editor |
| `MetadataSidebar` | `components/editor/MetadataSidebar.tsx` | Right sidebar with grouped metadata |
| `ConfidenceBadge` | `components/editor/ConfidenceBadge.tsx` | Color-coded confidence percentage |
| `SpeakerLabel` | `components/editor/SpeakerLabel.tsx` | Color-coded speaker tag |
