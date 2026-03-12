"""SQLAlchemy ORM models."""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class TaskRecord(Base):
    """Persistent task record — replaces task_history.json and in-memory tasks dict."""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)  # UUID
    status = Column(String(20), nullable=False, default="queued",
                    index=True)
    filename = Column(String(512), nullable=False)
    language_requested = Column(String(10), nullable=True)
    language = Column(String(10), nullable=True)  # detected
    model_size = Column(String(20), nullable=True)
    device = Column(String(10), nullable=True)  # cpu / cuda
    percent = Column(Float, default=0.0)
    message = Column(Text, nullable=True)

    # File metadata
    file_size = Column(Integer, nullable=True)
    file_size_fmt = Column(String(20), nullable=True)
    audio_size_fmt = Column(String(20), nullable=True)
    duration = Column(Float, nullable=True)

    # Processing results
    segments = Column(Text, nullable=True)  # JSON-encoded list
    word_timestamps = Column(Integer, default=0)  # boolean as int
    diarize = Column(Integer, default=0)  # boolean as int
    speakers = Column(Integer, nullable=True)

    # Session link
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=True,
                        index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc),
                        nullable=False)

    # Relationships
    session = relationship("SessionRecord", back_populates="tasks")

    __table_args__ = (
        Index("ix_tasks_session_status", "session_id", "status"),
        Index("ix_tasks_created_at", "created_at"),
    )

    def to_dict(self) -> dict:
        """Convert to dict matching the legacy state.tasks format."""
        import json
        d = {
            "status": self.status,
            "percent": self.percent or 0.0,
            "message": self.message or "",
            "filename": self.filename,
            "language_requested": self.language_requested,
            "language": self.language,
            "model_size": self.model_size,
            "device": self.device,
            "file_size": self.file_size,
            "file_size_fmt": self.file_size_fmt,
            "audio_size_fmt": self.audio_size_fmt,
            "duration": self.duration,
            "word_timestamps": bool(self.word_timestamps),
            "diarize": bool(self.diarize),
            "speakers": self.speakers,
            "session_id": self.session_id,
        }
        if self.segments:
            try:
                d["segments"] = json.loads(self.segments)
            except (json.JSONDecodeError, TypeError):
                d["segments"] = []
        else:
            d["segments"] = []
        return d

    @classmethod
    def from_dict(cls, task_id: str, data: dict) -> "TaskRecord":
        """Create a TaskRecord from a legacy state dict."""
        import json
        segments = data.get("segments")
        if isinstance(segments, (list, dict)):
            segments = json.dumps(segments, default=str)
        # Duration may be a formatted string like "2m 16s" — convert to float seconds
        raw_dur = data.get("duration")
        if isinstance(raw_dur, str):
            try:
                raw_dur = float(raw_dur)
            except ValueError:
                raw_dur = None  # can't store formatted strings in Float column

        return cls(
            id=task_id,
            status=data.get("status", "queued"),
            filename=data.get("filename", ""),
            language_requested=data.get("language_requested"),
            language=data.get("language"),
            model_size=data.get("model_size"),
            device=data.get("device"),
            percent=data.get("percent", 0.0),
            message=data.get("message"),
            file_size=data.get("file_size"),
            file_size_fmt=data.get("file_size_fmt"),
            audio_size_fmt=data.get("audio_size_fmt"),
            duration=raw_dur,
            segments=segments,
            word_timestamps=int(data.get("word_timestamps", False)),
            diarize=int(data.get("diarize", False)),
            speakers=data.get("speakers"),
            session_id=data.get("session_id"),
        )


class SessionRecord(Base):
    """Client session tracking — replaces cookie-only sessions."""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)  # UUID from cookie
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        nullable=False)
    last_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                       nullable=False)
    ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(512), nullable=True)

    # Relationships
    tasks = relationship("TaskRecord", back_populates="session")

    __table_args__ = (
        Index("ix_sessions_last_seen", "last_seen"),
    )


class AnalyticsEvent(Base):
    """Individual analytics events (replaces SQLite analytics_events)."""
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    event_type = Column(String(50), nullable=False)
    data = Column(Text, nullable=True)  # JSON

    __table_args__ = (
        Index("ix_analytics_events_type", "event_type"),
        Index("ix_analytics_events_ts", "timestamp"),
    )


class AnalyticsDaily(Base):
    """Daily aggregated analytics (replaces SQLite analytics_daily)."""
    __tablename__ = "analytics_daily"

    date = Column(String(10), primary_key=True)  # YYYY-MM-DD
    uploads = Column(Integer, default=0)
    completed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    cancelled = Column(Integer, default=0)
    total_processing_sec = Column(Float, default=0.0)
    avg_file_size = Column(Integer, default=0)
    data = Column(Text, default="{}")  # JSON for distributions


class AnalyticsTimeseries(Base):
    """Minute-resolution time-series (replaces in-memory ring buffer)."""
    __tablename__ = "analytics_timeseries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, unique=True)
    uploads = Column(Integer, default=0)
    completed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    cancelled = Column(Integer, default=0)
    total_processing_sec = Column(Float, default=0.0)
    task_count = Column(Integer, default=0)

    __table_args__ = (
        Index("ix_analytics_ts_timestamp", "timestamp"),
    )


class AuditLog(Base):
    """Security audit log (replaces audit.jsonl)."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    event_type = Column(String(50), nullable=False)
    ip = Column(String(45), nullable=True)
    path = Column(String(512), nullable=True)
    details = Column(Text, nullable=True)  # JSON

    __table_args__ = (
        Index("ix_audit_log_event", "event_type"),
        Index("ix_audit_log_ts", "timestamp"),
    )


class Feedback(Base):
    """User feedback (replaces feedback.jsonl)."""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_feedback_task", "task_id"),
        Index("ix_feedback_created", "created_at"),
    )


class UserRecord(Base):
    """User accounts for authentication and authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # admin, user
    is_active = Column(Integer, default=1)  # boolean as int
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    api_keys = relationship("ApiKeyRecord", back_populates="owner")

    __table_args__ = (
        Index("ix_users_username", "username"),
    )


class ApiKeyRecord(Base):
    """Persistent API keys with ownership and expiration."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_hash = Column(String(64), unique=True, nullable=False)  # SHA-256
    label = Column(String(100), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Integer, default=1)  # boolean as int

    # Relationships
    owner = relationship("UserRecord", back_populates="api_keys")

    __table_args__ = (
        Index("ix_api_keys_hash", "key_hash"),
        Index("ix_api_keys_owner", "owner_id"),
    )


class UIEvent(Base):
    """Frontend user interaction events for UX tracking."""
    __tablename__ = "ui_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    session_id = Column(String(36), nullable=True)
    event_type = Column(String(50), nullable=False)  # click, view, error, flow
    target = Column(String(100), nullable=True)       # button id, panel name, feature
    task_id = Column(String(36), nullable=True)
    extra = Column(Text, nullable=True)                # JSON extra data

    __table_args__ = (
        Index("ix_ui_events_session", "session_id"),
        Index("ix_ui_events_type", "event_type"),
        Index("ix_ui_events_ts", "timestamp"),
        Index("ix_ui_events_target", "target"),
    )


class BruteForceEvent(Base):
    """Persistent brute force event tracking."""
    __tablename__ = "brute_force_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(String(45), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    path = Column(String(512), nullable=True)
    blocked_until = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_brute_force_ip", "ip"),
        Index("ix_brute_force_ts", "timestamp"),
    )


class IpListEntry(Base):
    """IP allowlist/blocklist entries."""
    __tablename__ = "ip_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(String(45), nullable=False)
    list_type = Column(String(10), nullable=False)  # allow, block
    reason = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_ip_lists_ip", "ip"),
        Index("ix_ip_lists_type", "list_type"),
    )
