from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "football_tg_backend",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.parser",
        "app.tasks.ai",
        "app.tasks.publisher",
    ],
)

celery_app.conf.update(
    timezone="UTC",
    task_default_queue="default",
    task_track_started=True,
    worker_send_task_events=True,
)

# Import placeholder task modules so workers always register queue-specific tasks.
from app.tasks import ai, parser, publisher  # noqa: E402,F401
