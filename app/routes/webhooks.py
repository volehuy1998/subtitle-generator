"""Webhook callback management for task completion notifications."""

import ipaddress
import logging
import socket
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import state

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["User"])


def _is_safe_url(url: str) -> bool:
    """Reject webhook URLs pointing to private/internal IP addresses (SSRF protection)."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname or not parsed.scheme:
            return False
        if parsed.scheme not in ("http", "https"):
            return False
        # Block localhost aliases
        if hostname in ("localhost", "[::1]"):
            return False
        # Resolve hostname and check all addresses
        try:
            addr_infos = socket.getaddrinfo(hostname, None)
        except socket.gaierror:
            return False
        for _, _, _, _, sockaddr in addr_infos:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        return True
    except Exception:
        return False


# In-memory webhook registrations: task_id -> webhook URL
_webhooks: dict[str, str] = {}


class WebhookRegister(BaseModel):
    task_id: str
    url: str  # callback URL
    secret: Optional[str] = None  # optional signing secret


@router.post("/webhooks/register")
async def register_webhook(webhook: WebhookRegister):
    """Register a webhook callback URL for task completion.

    When the task completes (done, error, or cancelled), a POST request
    will be sent to the registered URL with the task result as JSON body.
    """
    if webhook.task_id not in state.tasks:
        raise HTTPException(404, "Task not found")

    task = state.tasks[webhook.task_id]
    if task.get("status") in ("done", "error", "cancelled"):
        raise HTTPException(400, "Task already completed. Webhook not needed.")

    if not _is_safe_url(webhook.url):
        raise HTTPException(400, "Webhook URL must not point to private/internal addresses")

    _webhooks[webhook.task_id] = webhook.url
    logger.info(f"WEBHOOK Registered for [{webhook.task_id[:8]}] -> {webhook.url}")

    return {
        "message": "Webhook registered",
        "task_id": webhook.task_id,
        "url": webhook.url,
    }


@router.get("/webhooks/{task_id}")
async def get_webhook(task_id: str):
    """Check if a webhook is registered for a task."""
    if task_id not in _webhooks:
        raise HTTPException(404, "No webhook registered for this task")
    return {"task_id": task_id, "url": _webhooks[task_id]}


@router.delete("/webhooks/{task_id}")
async def delete_webhook(task_id: str):
    """Remove a registered webhook."""
    if task_id not in _webhooks:
        raise HTTPException(404, "No webhook registered for this task")
    del _webhooks[task_id]
    return {"message": "Webhook removed", "task_id": task_id}


async def fire_webhook(task_id: str, result: dict):
    """Fire webhook callback for a completed task (called from pipeline)."""
    url = _webhooks.pop(task_id, None)
    if not url:
        return

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json={
                "task_id": task_id,
                "result": result,
            })
            logger.info(f"WEBHOOK Fired for [{task_id[:8]}] -> {url} (status={response.status_code})")
    except ImportError:
        logger.warning(f"WEBHOOK httpx not installed, skipping callback for [{task_id[:8]}]")
    except Exception as e:
        logger.error(f"WEBHOOK Failed for [{task_id[:8]}] -> {url}: {e}")


def get_pending_webhooks() -> dict[str, str]:
    """Get all pending webhook registrations."""
    return dict(_webhooks)
