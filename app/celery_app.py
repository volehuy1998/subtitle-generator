"""Celery application for distributed task processing.

Usage:
    celery -A app.celery_app worker --concurrency=1 --loglevel=info

Concurrency=1 because faster-whisper is not multi-worker safe within a process.
"""

from celery import Celery

from app.config import CELERY_BROKER_URL

celery = Celery(
    "subtitle_generator",
    broker=CELERY_BROKER_URL or "redis://localhost:6379/0",
    include=["app.tasks"],
)

celery.conf.update(
    result_backend=CELERY_BROKER_URL or "redis://localhost:6379/0",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Don't prefetch — each task is long-running
    result_expires=86400,  # Results expire after 24h
)
