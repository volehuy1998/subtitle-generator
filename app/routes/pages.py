"""Page routes — serves React SPA build when available, Jinja2 templates as fallback."""

import os
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.config import TEMPLATE_DIR

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# React build directory (built by `npm run build` inside frontend/)
_REACT_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"
_REACT_INDEX = _REACT_DIST / "index.html"
_USE_REACT = _REACT_INDEX.exists() and os.environ.get("FRONTEND", "react") == "react"


def _react_index() -> FileResponse:
    return FileResponse(str(_REACT_INDEX), media_type="text/html")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if _USE_REACT:
        return _react_index()
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/status", response_class=HTMLResponse)
async def status_page_html(request: Request):
    if _USE_REACT:
        return _react_index()
    return templates.TemplateResponse("status.html", {"request": request})
