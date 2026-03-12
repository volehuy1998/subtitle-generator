"""System info route."""

from fastapi import APIRouter

from app.config import SUPPORTED_LANGUAGES
from app.services.gpu import get_system_info
from app.services.diarization import is_diarization_available
from app.schemas import SystemInfoResponse, LanguagesResponse

router = APIRouter(tags=["System"])


@router.get("/system-info", response_model=SystemInfoResponse)
async def system_info():
    info = get_system_info()
    info["diarization"] = is_diarization_available()
    return info


@router.get("/languages", response_model=LanguagesResponse)
async def languages():
    return {"languages": SUPPORTED_LANGUAGES}
