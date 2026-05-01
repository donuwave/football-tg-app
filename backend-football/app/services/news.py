from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings
from app.core.security import TelegramValidationResult
from app.db.models.content_item import ContentItem
from app.db.models.enums import (
    ContentItemStatus,
    NewsSourceType,
    PublicationBatchStatus,
    PublicationBatchType,
    PublicationJobStatus,
    PublicationJobType,
    PublicationPlatform,
)
from app.db.models.news_source import NewsSource
from app.db.models.publication_batch import PublicationBatch
from app.db.models.publication_job import PublicationJob
from app.schemas.news import (
    NewsFeedResponse,
    NewsGenerateResponse,
    NewsItemResponse,
    NewsPublishResponse,
    NewsSourceResponse,
)
from app.services.telegram import TelegramPublishError, send_telegram_message


def list_news_feed(
    *,
    db: Session,
    source_type: NewsSourceType | None = None,
    limit: int = 100,
) -> NewsFeedResponse:
    item_query: Select[tuple[ContentItem]] = (
        select(ContentItem)
        .options(joinedload(ContentItem.source))
        .order_by(ContentItem.published_at.desc().nullslast(), ContentItem.created_at.desc())
        .limit(limit)
    )
    source_query: Select[tuple[NewsSource]] = select(NewsSource).order_by(NewsSource.name.asc())

    if source_type is not None:
        item_query = item_query.join(ContentItem.source).where(NewsSource.source_type == source_type)
        source_query = source_query.where(NewsSource.source_type == source_type)

    items = db.scalars(item_query).all()
    sources = db.scalars(source_query).all()

    return NewsFeedResponse(
        items=[NewsItemResponse.from_model(item) for item in items],
        sources=[NewsSourceResponse.from_model(source) for source in sources],
    )


def get_news_item_or_404(*, db: Session, news_id: UUID) -> ContentItem:
    item = db.scalar(
        select(ContentItem)
        .options(joinedload(ContentItem.source))
        .where(ContentItem.id == news_id)
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News item not found.",
        )

    return item


def build_generated_news_post(item: ContentItem) -> str:
    lead = item.title.strip().rstrip(".")
    summary = (item.excerpt or item.raw_text).strip()
    summary = " ".join(summary.split())
    if len(summary) > 220:
        summary = f"{summary[:217].rstrip()}..."

    source_label = (
        item.source.external_ref or item.source.name if item.source else "source"
    )
    published_hint = ""
    if item.published_at is not None:
        published_hint = item.published_at.astimezone(UTC).strftime("%d.%m %H:%M UTC")

    lines = [lead, "", summary]
    if published_hint:
        lines.extend(["", f"Источник: {source_label} • {published_hint}"])
    else:
        lines.extend(["", f"Источник: {source_label}"])

    return "\n".join(lines)


def generate_news_post(*, item: ContentItem) -> NewsGenerateResponse:
    return NewsGenerateResponse(item_id=item.id, text=build_generated_news_post(item))


def publish_news_item(
    *,
    db: Session,
    item: ContentItem,
    text: str,
    settings: Settings,
    telegram_context: TelegramValidationResult,
) -> NewsPublishResponse:
    normalized_text = text.strip()
    if not normalized_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Publication text cannot be empty.",
        )

    batch = PublicationBatch(
        batch_type=PublicationBatchType.NEWS_POST,
        status=PublicationBatchStatus.PROCESSING,
        created_by_telegram_user_id=telegram_context.user.id,
        source_item_id=item.id,
        request_payload={"text": normalized_text},
    )
    job = PublicationJob(
        platform=PublicationPlatform.TELEGRAM,
        job_type=PublicationJobType.TEXT_POST,
        status=PublicationJobStatus.PROCESSING,
        platform_payload={"channel_id": settings.telegram_channel_id},
    )
    batch.jobs.append(job)
    db.add(batch)
    db.flush()

    try:
        result = send_telegram_message(
            bot_token=settings.telegram_bot_token,
            channel_id=settings.telegram_channel_id,
            text=normalized_text,
        )
    except TelegramPublishError as exc:
        job.status = PublicationJobStatus.FAILED
        job.error_message = str(exc)
        batch.status = PublicationBatchStatus.FAILED
        batch.result_summary = {"platform": "telegram", "error": str(exc)}
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    item.status = ContentItemStatus.PUBLISHED
    job.status = PublicationJobStatus.PUBLISHED
    job.external_publication_id = str(result.message_id)
    batch.status = PublicationBatchStatus.COMPLETED
    batch.result_summary = {
        "platform": "telegram",
        "message_id": result.message_id,
        "published_at": datetime.now(tz=UTC).isoformat(),
    }
    db.commit()
    db.refresh(batch)
    db.refresh(job)

    return NewsPublishResponse(
        item_id=item.id,
        batch_id=batch.id,
        job_id=job.id,
        status=batch.status.value,
        platform=job.platform.value,
        external_publication_id=job.external_publication_id,
    )
