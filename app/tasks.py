"""Celery task definitions for distributed transcription processing."""

import logging

from app.celery_app import celery

logger = logging.getLogger("subtitle-generator")


@celery.task(name="transcribe", bind=True, max_retries=0)
def transcribe_task(
    self,
    task_id: str,
    video_filename: str,
    model_size: str,
    device: str,
    language: str = "auto",
    word_timestamps: bool = False,
    initial_prompt: str = "",
    diarize: bool = False,
    num_speakers: int | None = None,
    max_line_chars: int = 42,
    translate_to_english: bool = False,
    auto_embed: str = "",
    translate_to: str = "",
):
    """Run the transcription pipeline on a Celery worker.

    This is the distributed equivalent of the asyncio.to_thread(process_video, ...)
    call in the standalone upload route.
    """
    from app.config import STORAGE_BACKEND, UPLOAD_DIR
    from app.services.pipeline import process_video

    # If using S3, download file to local storage first
    if STORAGE_BACKEND == "s3":
        from app.services.storage import get_storage

        storage = get_storage()
        local_path = storage.get_upload_path(video_filename)
        if local_path is None:
            logger.error(f"CELERY [{task_id[:8]}] Upload file not found in S3: {video_filename}")
            return {"status": "error", "message": "Upload file not found"}
        video_path = local_path
    else:
        video_path = UPLOAD_DIR / video_filename

    # Initialize task state in Redis
    from app.config import REDIS_URL

    if REDIS_URL:
        from app.services.task_backend_redis import RedisTaskBackend

        backend = RedisTaskBackend()
        task_data = backend.get(task_id)
        if task_data:
            from app import state

            state.tasks[task_id] = task_data

    logger.info(f"CELERY [{task_id[:8]}] Starting transcription: {video_filename}")

    process_video(
        task_id,
        video_path,
        model_size,
        device,
        language,
        word_timestamps=word_timestamps,
        initial_prompt=initial_prompt,
        diarize=diarize,
        num_speakers=num_speakers,
        max_line_chars=max_line_chars,
        translate_to_english=translate_to_english,
        auto_embed=auto_embed,
        translate_to=translate_to,
    )

    # If using S3, upload output files
    if STORAGE_BACKEND == "s3":
        from app.config import OUTPUT_DIR
        from app.services.storage import get_storage

        storage = get_storage()
        for ext in ("srt", "vtt", "json"):
            output_file = OUTPUT_DIR / f"{task_id}.{ext}"
            if output_file.exists():
                storage.save_output_from_path(output_file.name, output_file)
                logger.info(f"CELERY [{task_id[:8]}] Uploaded {ext} to S3")

    return {"status": "done", "task_id": task_id}
