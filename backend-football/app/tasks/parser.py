from uuid import UUID

from sqlalchemy import select

from app.db.models.news_source import NewsSource
from app.db.session import SessionLocal
from app.services.parser import SourceSyncFailedError, get_source_or_404, sync_news_source
from app.tasks.celery_app import celery_app


@celery_app.task(name="parser.sync_source", queue="parser")
def sync_source(source_id: str) -> dict[str, str]:
    with SessionLocal() as db:
        source = get_source_or_404(db=db, source_id=UUID(source_id))
        try:
            result = sync_news_source(db=db, source=source)
        except SourceSyncFailedError:
            return {
                "status": "failed",
                "source_id": source_id,
            }

    return {
        "status": result.source.last_sync_status.value,
        "source_id": source_id,
    }


@celery_app.task(name="parser.enqueue_active_sources", queue="parser")
def enqueue_active_sources() -> dict[str, int]:
    with SessionLocal() as db:
        source_ids = db.scalars(
            select(NewsSource.id)
            .where(NewsSource.is_active.is_(True))
            .order_by(NewsSource.created_at.asc())
        ).all()

    for source_id in source_ids:
        sync_source.delay(str(source_id))

    return {
        "queued_sources": len(source_ids),
    }
