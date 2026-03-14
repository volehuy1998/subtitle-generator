"""Pydantic response models for all public API routes.

These are the single source of truth for the OpenAPI schema.
FastAPI serialises every decorated route through its model, so any
field mismatch between implementation and schema surfaces at runtime
rather than silently at the frontend.

To regenerate the frontend TypeScript types after changing a model:

    cd frontend && npm run gen:types
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


# ── Upload ────────────────────────────────────────────────────────────────────


class UploadResponse(BaseModel):
    task_id: str
    model_size: str
    language: str
    word_timestamps: bool
    diarize: bool


# ── Task progress (polling fallback) ─────────────────────────────────────────

TaskStatusLiteral = Literal[
    "queued",
    "uploading",
    "probing",
    "extracting",
    "loading_model",
    "transcribing",
    "formatting",
    "writing",
    "done",
    "error",
    "cancelled",
    "paused",
    "combining",
]


class StepTimings(BaseModel):
    """Wall-clock seconds for each pipeline stage."""

    model_config = ConfigDict(extra="allow")
    upload: Optional[float] = None
    extract: Optional[float] = None
    transcribe: Optional[float] = None
    finalize: Optional[float] = None


class TaskProgressResponse(BaseModel):
    """Returned by GET /progress/{task_id}."""

    model_config = ConfigDict(extra="allow")
    task_id: Optional[str] = None
    status: str
    percent: float
    message: str
    filename: Optional[str] = None
    file_size: Optional[int] = None
    audio_duration: Optional[float] = None
    model: Optional[str] = None
    language: Optional[str] = None
    device: Optional[str] = None
    segments: Optional[int] = None
    total_time_sec: Optional[float] = None
    step_timings: Optional[StepTimings] = None
    is_video: Optional[bool] = None
    error: Optional[str] = None
    current_step: Optional[int] = None
    download_url: Optional[str] = None
    embed_download_url: Optional[str] = None


# ── Health ────────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Returned by GET /health — liveness only."""

    status: Literal["healthy"]
    uptime_sec: float


class AlertItem(BaseModel):
    alert: str
    severity: str
    message: str


class SystemStatusResponse(BaseModel):
    """Returned by GET /api/status — full health aggregate for the UI."""

    status: Literal["healthy", "warning", "critical"]
    uptime_sec: float
    active_tasks: int
    max_tasks: int
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_free_gb: Optional[float] = None
    disk_percent: Optional[float] = None
    disk_ok: bool
    db_ok: bool
    db_latency_ms: Optional[float] = None
    ffmpeg_ok: bool
    gpu_available: bool
    gpu_name: Optional[str] = None
    gpu_vram_total: Optional[float] = None
    gpu_vram_used: Optional[float] = None
    gpu_vram_free: Optional[float] = None
    shutting_down: bool
    system_critical: bool
    system_critical_reasons: list[str]
    alerts: list[AlertItem]
    alert_count: int
    model_preload: Optional[dict] = None


# ── System info ───────────────────────────────────────────────────────────────


class DiarizationInfo(BaseModel):
    available: bool


class SystemInfoResponse(BaseModel):
    """Returned by GET /system-info."""

    model_config = ConfigDict(extra="allow")
    cuda_available: bool
    gpu_name: Optional[str] = None
    gpu_vram: Optional[float] = None
    gpu_vram_free: Optional[float] = None
    model_recommendations: dict[str, Literal["ok", "tight", "too_large"]]
    auto_model: str
    diarization: Optional[DiarizationInfo] = None


class LanguagesResponse(BaseModel):
    """Returned by GET /languages."""

    languages: dict[str, str]


# ── Tasks list ────────────────────────────────────────────────────────────────


class TaskListItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    task_id: str
    status: str
    filename: Optional[str] = None
    percent: float
    position: Optional[int] = None
    created_at: Optional[str] = None


class TasksResponse(BaseModel):
    tasks: list[TaskListItem]
