"""Translation routes - list available languages and manage translation packages."""

import logging

from fastapi import APIRouter, HTTPException

from app.services.translation import (
    get_available_languages,
    is_translation_available,
    install_translation_package,
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
            f"Could not install language pair {source} -> {target}. "
            f"The pair may not be available in argos-translate.",
        )
