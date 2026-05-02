from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.config import get_settings
from app.db.models.content_item import ContentItem
from app.db.session import SessionLocal
from app.services.ai import AIRewriteError, rewrite_news_post
from app.tasks.celery_app import celery_app


@celery_app.task(name="ai.generate_news_post", queue="ai")
def generate_news_post(
    content_item_id: str,
    instruction: str | None = None,
) -> dict[str, str]:
    settings = get_settings()

    with SessionLocal() as db:
        item = db.scalar(
            select(ContentItem)
            .options(joinedload(ContentItem.source))
            .where(ContentItem.id == UUID(content_item_id))
        )

        if item is None:
            return {
                "status": "not_found",
                "content_item_id": content_item_id,
            }

        try:
            result = rewrite_news_post(
                item=item,
                instruction=instruction,
                settings=settings,
            )
        except AIRewriteError as exc:
            return {
                "status": "failed",
                "content_item_id": content_item_id,
                "error": str(exc),
            }

    return {
        "status": "completed",
        "content_item_id": content_item_id,
        "mode": result.mode,
        "text": result.text,
    }
