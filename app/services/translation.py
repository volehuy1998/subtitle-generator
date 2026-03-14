"""Subtitle translation service.

Two translation modes:
1. Whisper translate: Uses faster-whisper's built-in task="translate" to translate
   any language to English during transcription (no extra dependency).
2. Argos Translate: Offline neural machine translation for any-to-any language pairs.
   Models are downloaded on demand (~100-200MB per pair) and cached for reuse.
"""

import logging

import app.state as state
from app.config import TRANSLATION_BATCH_SIZE
from app.logging_setup import log_task_event

logger = logging.getLogger("subtitle-generator")

# Argos-translate language codes that differ from Whisper/ISO 639-1
_ARGOS_LANG_MAP = {
    "zh": "zh",
    "he": "he",
    "jw": "jv",  # Javanese
}


def _to_argos_code(lang: str) -> str:
    """Map Whisper/ISO language code to argos-translate code."""
    return _ARGOS_LANG_MAP.get(lang, lang)


def get_whisper_translate_options() -> dict:
    """Get faster-whisper options for translate mode (any language -> English)."""
    return {"task": "translate"}


def install_translation_package(source_lang: str, target_lang: str) -> bool:
    """Download and install an argos-translate language package on demand.

    Returns True if the package was installed or already exists.
    """
    try:
        import argostranslate.package as argos_package

        src = _to_argos_code(source_lang)
        tgt = _to_argos_code(target_lang)

        # Check if already installed
        installed = argos_package.get_installed_packages()
        for pkg in installed:
            if pkg.from_code == src and pkg.to_code == tgt:
                return True

        # Update package index and download
        argos_package.update_package_index()
        available = argos_package.get_available_packages()
        matching = [p for p in available if p.from_code == src and p.to_code == tgt]
        if not matching:
            logger.warning(f"TRANSLATE No argos package found for {src} -> {tgt}")
            return False

        pkg = matching[0]
        download_path = pkg.download()
        argos_package.install_from_path(download_path)
        logger.info(f"TRANSLATE Installed argos package: {src} -> {tgt}")
        return True
    except Exception as e:
        logger.error(f"TRANSLATE Failed to install package {source_lang} -> {target_lang}: {e}")
        return False


def get_translation_model(source_lang: str, target_lang: str):
    """Get a cached argos-translate model, loading on first use.

    Uses double-checked locking pattern matching model_manager.py.
    Returns the argos translation object, or None if unavailable.
    """
    src = _to_argos_code(source_lang)
    tgt = _to_argos_code(target_lang)
    key = (src, tgt)

    if key in state.translation_models:
        return state.translation_models[key]

    with state.translation_model_lock:
        if key in state.translation_models:
            return state.translation_models[key]

        # Ensure package is installed
        if not install_translation_package(source_lang, target_lang):
            return None

        try:
            import argostranslate.translate as argos_translate

            installed_languages = argos_translate.get_installed_languages()
            src_lang_obj = None
            tgt_lang_obj = None
            for lang in installed_languages:
                if lang.code == src:
                    src_lang_obj = lang
                if lang.code == tgt:
                    tgt_lang_obj = lang

            if src_lang_obj is None or tgt_lang_obj is None:
                logger.error(f"TRANSLATE Language objects not found for {src} -> {tgt}")
                return None

            translation = src_lang_obj.get_translation(tgt_lang_obj)
            if translation is None:
                logger.error(f"TRANSLATE No translation path for {src} -> {tgt}")
                return None

            state.translation_models[key] = translation
            logger.info(f"TRANSLATE Loaded model: {src} -> {tgt}")
            return translation
        except Exception as e:
            logger.error(f"TRANSLATE Failed to load model {src} -> {tgt}: {e}")
            return None


def translate_segments(segments: list, source_lang: str, target_lang: str, task_id: str = "") -> list:
    """Translate subtitle segments to target language.

    - Any language -> English: handled at transcription time via Whisper (caller should
      use translate_to_english=True instead of calling this).
    - Same language: returns segments unchanged.
    - Other targets: uses argos-translate for offline neural machine translation.

    Returns translated segments with original text preserved in 'original_text' field.
    """
    if source_lang == target_lang:
        return segments

    if target_lang == "en" and source_lang != "en":
        # This should be handled at transcription time with task="translate"
        logger.info(f"TRANSLATE [{task_id[:8]}] Whisper translate mode (-> English)")
        return segments

    # Use argos-translate for non-English targets
    model = get_translation_model(source_lang, target_lang)
    if model is None:
        logger.warning(
            f"TRANSLATE [{task_id[:8]}] No model available for {source_lang} -> {target_lang}. "
            f"Returning original segments."
        )
        log_task_event(task_id, "translate_unsupported", source=source_lang, target=target_lang)
        result = []
        for seg in segments:
            translated = dict(seg)
            translated["original_text"] = seg["text"]
            result.append(translated)
        return result

    # Translate segments with progress reporting
    from app.services.sse import emit_event

    total = len(segments)
    result = []
    log_task_event(task_id, "translate_start", source=source_lang, target=target_lang, segments=total)
    logger.info(f"TRANSLATE [{task_id[:8]}] Translating {total} segments: {source_lang} -> {target_lang}")

    for i, seg in enumerate(segments):
        translated = dict(seg)
        translated["original_text"] = seg["text"]

        try:
            translated["text"] = model.translate(seg["text"])
        except Exception as e:
            logger.error(f"TRANSLATE [{task_id[:8]}] Segment {i} failed: {e}")
            # Keep original text on failure

        result.append(translated)

        # Emit progress at batch intervals
        if task_id and (i + 1) % TRANSLATION_BATCH_SIZE == 0 or i == total - 1:
            pct = int((i + 1) / total * 100)
            emit_event(
                task_id,
                "translate_progress",
                {
                    "percent": pct,
                    "translated": i + 1,
                    "total": total,
                    "message": f"Translating: {i + 1}/{total} segments",
                },
            )

    logger.info(f"TRANSLATE [{task_id[:8]}] Completed {total} segments: {source_lang} -> {target_lang}")
    log_task_event(task_id, "translate_done", source=source_lang, target=target_lang, segments=total)
    return result


def is_translation_available(target_lang: str) -> dict:
    """Check if translation to target language is available."""
    if target_lang == "en":
        return {
            "available": True,
            "method": "whisper_translate",
            "note": "Built-in Whisper translation (any language -> English)",
        }

    try:
        import argostranslate.package as argos_package

        tgt = _to_argos_code(target_lang)

        # Check installed packages
        installed = argos_package.get_installed_packages()
        for pkg in installed:
            if pkg.to_code == tgt:
                return {
                    "available": True,
                    "method": "argos_translate",
                    "note": f"Argos Translate ({pkg.from_name} -> {pkg.to_name}, installed)",
                    "installed": True,
                }

        # Check available packages
        try:
            argos_package.update_package_index()
            available = argos_package.get_available_packages()
            matching = [p for p in available if p.to_code == tgt]
            if matching:
                return {
                    "available": True,
                    "method": "argos_translate",
                    "note": f"Argos Translate (downloadable, ~{len(matching)} pair(s))",
                    "installed": False,
                }
        except Exception:
            pass

        return {
            "available": False,
            "method": None,
            "note": f"Translation to '{target_lang}' not available via argos-translate",
        }
    except ImportError:
        return {
            "available": False,
            "method": None,
            "note": "argos-translate not installed",
        }


def get_available_languages() -> list[dict]:
    """List available translation target languages with install status.

    Returns a list of dicts with source/target language info and install status.
    """
    try:
        import argostranslate.package as argos_package

        # Get installed packages
        installed = argos_package.get_installed_packages()
        installed_pairs = {(p.from_code, p.to_code) for p in installed}

        result = []

        # Add installed pairs
        for pkg in installed:
            result.append(
                {
                    "source": pkg.from_code,
                    "source_name": pkg.from_name,
                    "target": pkg.to_code,
                    "target_name": pkg.to_name,
                    "installed": True,
                }
            )

        # Add downloadable pairs
        try:
            argos_package.update_package_index()
            available = argos_package.get_available_packages()
            for pkg in available:
                if (pkg.from_code, pkg.to_code) not in installed_pairs:
                    result.append(
                        {
                            "source": pkg.from_code,
                            "source_name": pkg.from_name,
                            "target": pkg.to_code,
                            "target_name": pkg.to_name,
                            "installed": False,
                        }
                    )
        except Exception as e:
            logger.warning(f"TRANSLATE Could not fetch available packages: {e}")

        # Always include English as a target (via Whisper)
        has_english = any(p["target"] == "en" for p in result)
        if not has_english:
            result.insert(
                0,
                {
                    "source": "auto",
                    "source_name": "Any language",
                    "target": "en",
                    "target_name": "English",
                    "installed": True,
                    "method": "whisper_translate",
                },
            )

        return result
    except ImportError:
        # argos-translate not installed, only Whisper translate available
        return [
            {
                "source": "auto",
                "source_name": "Any language",
                "target": "en",
                "target_name": "English",
                "installed": True,
                "method": "whisper_translate",
            }
        ]
