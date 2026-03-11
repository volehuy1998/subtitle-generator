"""Subtitle translation service.

Two translation modes:
1. Whisper translate: Uses faster-whisper's built-in task="translate" to translate
   any language to English during transcription (no extra dependency).
2. External translation: Placeholder for future integration with translation APIs
   (Google Translate, DeepL, etc.) for translating to any target language.
"""

import logging

from app.logging_setup import log_task_event

logger = logging.getLogger("subtitle-generator")


def get_whisper_translate_options() -> dict:
    """Get faster-whisper options for translate mode (any language -> English)."""
    return {"task": "translate"}


def translate_segments(segments: list, source_lang: str, target_lang: str,
                       task_id: str = "") -> list:
    """Translate subtitle segments to target language.

    Currently supports:
    - Any language -> English via Whisper (handled at transcription time)
    - Placeholder for external API translation

    Returns translated segments with original text preserved.
    """
    if target_lang == "en" and source_lang != "en":
        # This should be handled at transcription time with task="translate"
        logger.info(f"TRANSLATE [{task_id[:8]}] Whisper translate mode (-> English)")
        return segments

    if source_lang == target_lang:
        return segments

    # For non-English targets, we need an external translation API
    # This is a placeholder that preserves original segments
    logger.warning(
        f"TRANSLATE [{task_id[:8]}] Translation to '{target_lang}' requires external API. "
        f"Currently only Whisper translate (-> English) is supported natively."
    )
    log_task_event(task_id, "translate_unsupported",
                   source=source_lang, target=target_lang)

    # Return segments with a note
    result = []
    for seg in segments:
        translated = dict(seg)
        translated["original_text"] = seg["text"]
        # Keep original text when no translator available
        result.append(translated)

    return result


def is_translation_available(target_lang: str) -> dict:
    """Check if translation to target language is available."""
    if target_lang == "en":
        return {
            "available": True,
            "method": "whisper_translate",
            "note": "Built-in Whisper translation (any language -> English)",
        }
    return {
        "available": False,
        "method": None,
        "note": f"Translation to '{target_lang}' requires external API (not yet configured)",
    }
