"""Download route for subtitle files (SRT and VTT)."""

import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app import state
from app.config import OUTPUT_DIR
from app.logging_setup import log_task_event

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Download"])


@router.get("/download/{task_id}")
async def download(task_id: str, format: Literal["srt", "vtt", "json"] = Query("srt")):
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")
    if state.tasks[task_id]["status"] != "done":
        raise HTTPException(400, "Subtitles not ready yet")

    sub_path = OUTPUT_DIR / f"{task_id}.{format}"
    if not sub_path.exists():
        raise HTTPException(404, f"{format.upper()} file not found")

    # Security: verify path is within OUTPUT_DIR
    resolved = sub_path.resolve()
    if not str(resolved).startswith(str(OUTPUT_DIR.resolve())):
        raise HTTPException(403, "Access denied")

    original_name = Path(state.tasks[task_id]["filename"]).stem + f".{format}"
    media_types = {"srt": "text/plain", "vtt": "text/vtt", "json": "application/json"}
    media_type = media_types.get(format, "text/plain")
    logger.info(f"DOWNLOAD [{task_id[:8]}] Serving {original_name}")
    log_task_event(task_id, "downloaded", filename=original_name, format=format)
    return FileResponse(
        sub_path, filename=original_name, media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{original_name}"'},
    )
