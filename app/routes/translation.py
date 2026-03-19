"""Translation routes - list available languages and manage translation packages."""

import logging
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException

from app import config
from app.services.translation import (
    get_available_languages,
    install_translation_package,
    is_translation_available,
)

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Translation"])


@router.get("/translation/languages")
async def list_translation_languages():
    """List available translation language pairs.

    Returns installed pairs and downloadable pairs.
    English target is always available via Whisper's built-in translation.
    """
    pairs = get_available_languages()
    return {"pairs": pairs, "count": len(pairs)}


@router.get("/translation/status/{target}")
async def translation_status(target: str):
    """Check if translation to a specific target language is available."""
    result = is_translation_available(target)
    return result


@router.post("/translation/install")
async def install_language(source: str = "en", target: str = ""):
    """Download and install a translation language pair on demand.

    This pre-downloads the argos-translate model so that future translations
    are instant instead of waiting for the download during processing.
    """
    if not target:
        raise HTTPException(400, "Target language code is required")
    if target == "en":
        return {"message": "English target uses Whisper (no download needed)", "installed": True}

    success = install_translation_package(source, target)
    if success:
        return {"message": f"Language pair {source} -> {target} installed", "installed": True}
    else:
        raise HTTPException(
            404,
            f"Could not install language pair {source} -> {target}. The pair may not be available in argos-translate.",
        )


@router.post("/translate/{task_id}")
async def translate_task(task_id: str, target_language: str = Form("en")):
    """Translate existing subtitles for a task to a target language.

    Uses Argos Translate for any-to-any translation.
    For English targets, Whisper translate during re-transcription is recommended.
    """
    # — Forge (Sr. Backend Engineer)
    from app import state
    from app.services.sse import create_event_queue, emit_event
    from app.services.translation import translate_segments
    from app.utils.srt import parse_srt, segments_to_srt

    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")

    task = state.tasks[task_id]
    if task.get("status") != "done":
        raise HTTPException(400, "Transcription not complete")

    srt_path = Path(config.OUTPUT_DIR) / f"{task_id}.srt"
    if not srt_path.exists():
        raise HTTPException(404, "Subtitle file not found")

    source_lang = task.get("language", "en")
    if source_lang == target_language:
        raise HTTPException(400, f"Source and target language are the same: {target_language}")

    # Create event queue for SSE
    create_event_queue(task_id)

    def do_translate():
        try:
            emit_event(task_id, "translate_progress", {"message": "Translating...", "percent": 0})

            srt_content = srt_path.read_text(encoding="utf-8")
            segments = parse_srt(srt_content)

            translated = translate_segments(segments, source_lang, target_language, task_id)
            translated_srt = segments_to_srt(translated, include_speakers=False)

            # Save translated subtitles
            translated_path = Path(config.OUTPUT_DIR) / f"{task_id}_translated_{target_language}.srt"
            translated_path.write_text(translated_srt, encoding="utf-8")

            # Update task with translated segments
            task["translated_to"] = target_language
            task["translated_segments"] = len(translated)

            emit_event(
                task_id,
                "translate_done",
                {
                    "message": f"Translation to {target_language} complete",
                    "target_language": target_language,
                    "segments": len(translated),
                },
            )
        except Exception as e:
            logger.error("TRANSLATE [%s] Failed: %s", task_id[:8], e)
            emit_event(task_id, "translate_error", {"message": f"Translation failed: {e!s}"})

    import asyncio

    asyncio.create_task(asyncio.to_thread(do_translate))

    return {"message": f"Translation to {target_language} started", "task_id": task_id}
