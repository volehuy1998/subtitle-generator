"""Aggregated router combining all route modules."""

from fastapi import APIRouter

from app.routes.admin_logs import router as admin_logs_router
from app.routes.analytics import router as analytics_router
from app.routes.analytics_page import router as analytics_page_router
from app.routes.auth import router as auth_router
from app.routes.combine import router as combine_router
from app.routes.control import router as control_router
from app.routes.dashboard import router as dashboard_router
from app.routes.download import router as download_router
from app.routes.embed import router as embed_router
from app.routes.events import router as events_router
from app.routes.export import router as export_router
from app.routes.feedback import router as feedback_router
from app.routes.health import router as health_router
from app.routes.logs import router as logs_router
from app.routes.metrics import router as metrics_router
from app.routes.monitoring import router as monitoring_router
from app.routes.pages import router as pages_router
from app.routes.query import router as query_router
from app.routes.security import router as security_router
from app.routes.status_page import router as status_page_router
from app.routes.subtitles import router as subtitles_router
from app.routes.system import router as system_router
from app.routes.tasks import router as tasks_router
from app.routes.tracking import router as tracking_router
from app.routes.translation import router as translation_router
from app.routes.upload import router as upload_router
from app.routes.preferences import router as preferences_router
from app.routes.webhooks import router as webhooks_router
from app.routes.ws import router as ws_router

router = APIRouter()
router.include_router(pages_router)
router.include_router(system_router)
router.include_router(upload_router)
router.include_router(events_router)
router.include_router(control_router)
router.include_router(download_router)
router.include_router(logs_router)
router.include_router(tasks_router)
router.include_router(subtitles_router)
router.include_router(health_router)
router.include_router(embed_router)
router.include_router(metrics_router)
router.include_router(ws_router)
router.include_router(dashboard_router)
router.include_router(feedback_router)
router.include_router(analytics_router)
router.include_router(analytics_page_router)
router.include_router(webhooks_router)
router.include_router(export_router)
router.include_router(security_router)
router.include_router(tracking_router)
router.include_router(admin_logs_router)
router.include_router(auth_router)
router.include_router(query_router)
router.include_router(monitoring_router)
router.include_router(combine_router)
router.include_router(status_page_router)
router.include_router(translation_router)
router.include_router(preferences_router)
