"""System info route."""

from fastapi import APIRouter, Request

from app.config import SUPPORTED_LANGUAGES
from app.schemas import LanguagesResponse, SystemInfoResponse
from app.services.diarization import is_diarization_available
from app.services.gpu import get_system_info
from app.services.response_cache import ttl_cache

router = APIRouter(tags=["System"])


@router.get("/system-info", response_model=SystemInfoResponse)
@ttl_cache(seconds=30)
async def system_info(request: Request):
    from app import state

    info = get_system_info()
    info["diarization"] = is_diarization_available()
    # Include model preload status so the UI can show which models are ready
    info["model_preload"] = state.model_preload
    return info


@router.get("/languages", response_model=LanguagesResponse)
@ttl_cache(seconds=3600)
async def languages(request: Request):
    return {"languages": SUPPORTED_LANGUAGES}
