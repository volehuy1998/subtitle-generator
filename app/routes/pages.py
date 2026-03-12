"""Page routes — serves React SPA build when available, Jinja2 templates as fallback."""

import os
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from app.config import TEMPLATE_DIR

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# React build directory (built by `npm run build` inside frontend/)
_REACT_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"
_REACT_INDEX = _REACT_DIST / "index.html"
_USE_REACT = _REACT_INDEX.exists() and os.environ.get("FRONTEND", "react") == "react"


def _react_index() -> FileResponse:
    return FileResponse(
        str(_REACT_INDEX),
        media_type="text/html",
        headers={"Cache-Control": "no-store"},
    )


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


@router.get("/security", response_class=HTMLResponse)
async def security_page(request: Request):
    from app.routes.security import load_security_assertions
    assertions_data = load_security_assertions()
    return templates.TemplateResponse("security.html", {
        "request": request,
        "active_page": "security",
        "assertions": assertions_data,
    })


@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "active_page": "about"})


@router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request, "active_page": "contact"})


@router.get("/manifest.json")
async def manifest():
    f = _REACT_DIST / "manifest.json"
    if f.exists():
        return FileResponse(str(f), media_type="application/manifest+json")
    return FileResponse(str(Path(__file__).parent.parent.parent / "frontend" / "public" / "manifest.json"), media_type="application/manifest+json")


@router.get("/logo.svg")
async def logo_svg():
    f = _REACT_DIST / "logo.svg"
    if f.exists():
        return FileResponse(str(f), media_type="image/svg+xml")
    return FileResponse(str(Path(__file__).parent.parent.parent / "frontend" / "public" / "logo.svg"), media_type="image/svg+xml")


@router.get("/favicon.svg")
async def favicon_svg():
    f = _REACT_DIST / "favicon.svg"
    if f.exists():
        return FileResponse(str(f), media_type="image/svg+xml")
    return FileResponse(str(Path(__file__).parent.parent.parent / "frontend" / "public" / "favicon.svg"), media_type="image/svg+xml")
