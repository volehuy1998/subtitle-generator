# Changelog

## v1.0.0 (2026-03-11)

### Core Features
- AI-powered subtitle generation using faster-whisper (CTranslate2 engine)
- Support for 99 languages with auto-detection
- Output formats: SRT, VTT, JSON (with word-level data)
- GPU acceleration (CUDA) with automatic model selection based on VRAM
- CPU fallback with hardware-aware optimization (OMP threads, model selection)

### Transcription
- 5 Whisper models: tiny, base, small, medium, large
- Word-level timestamps for karaoke-style subtitles
- Speaker diarization via pyannote.audio (optional, graceful degradation)
- Custom vocabulary via initial_prompt for domain-specific terms
- Translation mode: any language to English via Whisper translate
- VAD filtering (Silero) for silence skipping

### Subtitle Processing
- Smart line-breaking: sentence/clause/word boundary splits
- Characters per second (CPS) validation (Netflix/YouTube standards)
- Subtitle embedding: soft mux (MKV/MP4) and hard burn with ASS styling
- 6 style presets: default, youtube_white, youtube_yellow, cinema, large_bold, top_position
- In-browser subtitle editor with save/regenerate

### User Interface
- Single-page web application with dark theme
- Drag-and-drop file upload with batch processing
- Real-time progress via SSE and WebSocket
- Video preview with subtitle track overlay
- Task queue visualization
- Built-in monitoring dashboard (/dashboard)

### Architecture
- System capability detection at startup (CPU, GPU, RAM, disk, OS)
- Hardware-aware auto-tuning (threads, concurrency, model selection)
- Structured JSON logging (app.jsonl) for ELK/Grafana/Loki integration
- Request ID tracing across middleware, logs, and response headers
- Global exception handler preventing service crashes
- Background file cleanup (configurable 24h retention)
- Task persistence across restarts

### Production
- Dockerfile (CPU) + Dockerfile.gpu (NVIDIA CUDA) with non-root user
- docker-compose.yml with CPU/GPU profiles
- GitHub Actions CI/CD: lint, test, build, health check
- API key authentication (X-API-Key header, optional)
- Prometheus /metrics endpoint (zero-dependency)
- Health (/health) and readiness (/ready) probes
- Graceful shutdown with in-flight task draining
- Session management via cookies with task ownership
- Rate limiting via slowapi

### Security
- File extension allowlist + magic byte verification
- Filename sanitization (path separators, null bytes, special chars)
- File size limits (1KB - 2GB)
- Audio duration limit (4 hours max)
- ffmpeg protocol whitelist + execution timeout
- Security headers (CSP, X-Frame-Options, X-Content-Type-Options)
- Path traversal prevention on downloads

### Quality
- 307+ automated tests across 10 test modules
- 0 regressions across 7 sprint cycles
- Cross-platform support (Linux, Windows, macOS, Docker)
