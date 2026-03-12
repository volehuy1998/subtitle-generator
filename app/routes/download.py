"""Download route for subtitle files (SRT and VTT).

Supports local filesystem and S3 storage backends.
"""

import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app import state
from app.config import OUTPUT_DIR, STORAGE_BACKEND
from app.logging_setup import log_task_event

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Download"])


def _get_task_data(task_id: str) -> dict | None:
    """Get task data from local state or backend."""
    if task_id in state.tasks:
        return state.tasks[task_id]
    from app.config import REDIS_URL
    if REDIS_URL:
        try:
            from app.services.task_backend import get_task_backend
            return get_task_backend().get(task_id)
        except Exception:
            pass
    return None


@router.get("/download/{task_id}")
async def download(task_id: str, format: Literal["srt", "vtt", "json"] = Query("srt")):
    task_data = _get_task_data(task_id)
    if task_data is None:
        raise HTTPException(404, "Task not found")
    if task_data.get("status") != "done":
        raise HTTPException(400, "Subtitles not ready yet")

    filename = f"{task_id}.{format}"
    original_name = Path(task_data["filename"]).stem + f".{format}"
    media_types = {"srt": "text/plain", "vtt": "text/vtt", "json": "application/json"}
    media_type = media_types.get(format, "text/plain")

    if STORAGE_BACKEND == "s3":
        # Try S3 pre-signed URL first
        from app.services.storage import get_storage
        storage = get_storage()
        # Ensure file is available locally (download from S3 if needed)
        local_path = storage.get_output_path(filename)
        if local_path is None:
            raise HTTPException(404, f"{format.upper()} file not found")
        sub_path = local_path
    else:
        sub_path = OUTPUT_DIR / filename
        if not sub_path.exists():
            raise HTTPException(404, f"{format.upper()} file not found")

    # Security: verify path is within OUTPUT_DIR
    resolved = sub_path.resolve()
    if not str(resolved).startswith(str(OUTPUT_DIR.resolve())):
        raise HTTPException(403, "Access denied")

    logger.info(f"DOWNLOAD [{task_id[:8]}] Serving {original_name}")
    log_task_event(task_id, "downloaded", filename=original_name, format=format)
    return FileResponse(
        sub_path, filename=original_name, media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{original_name}"'},
    )
