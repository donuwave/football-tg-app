from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.content_item import ContentItem
from app.db.models.enums import ContentItemStatus, NewsSourceSyncStatus
from app.db.models.news_source import NewsSource
from app.parsers.base import NormalizedContentItem
from app.parsers.registry import UnsupportedSourceTypeError, get_adapter


class SourceSyncFailedError(RuntimeError):
    """Raised when a source cannot be synced due to parser/fetch failure."""


@dataclass(frozen=True, slots=True)
class SourceSyncResult:
    source: NewsSource
    fetched_count: int
    inserted_count: int
    updated_count: int
    skipped_count: int


def sync_news_source(*, db: Session, source: NewsSource) -> SourceSyncResult:
    adapter = get_adapter(source.source_type)
    sync_started_at = datetime.now(tz=UTC)
    settings = get_settings()

    try:
        normalized_items = adapter.run(source)
    except UnsupportedSourceTypeError:
        source.last_synced_at = sync_started_at
        source.last_sync_status = NewsSourceSyncStatus.FAILED
        source.last_error_message = f"Source type '{source.source_type.value}' is not supported yet."
        db.commit()
        raise
    except Exception as exc:
        source.last_synced_at = sync_started_at
        source.last_sync_status = NewsSourceSyncStatus.FAILED
        source.last_error_message = str(exc)
        db.commit()
        raise SourceSyncFailedError(str(exc)) from exc

    recent_items, aged_out_count = _filter_recent_items(
        items=normalized_items,
        synced_at=sync_started_at,
        max_age_hours=settings.parser_max_item_age_hours,
    )

    inserted_count = 0
    updated_count = 0
    skipped_count = aged_out_count
    seen_keys: set[tuple[str, str]] = set()

    for normalized_item in recent_items:
        canonical_item = _canonicalize_item(normalized_item)
        dedupe_key = _build_dedupe_key(canonical_item)
        if dedupe_key is None:
            skipped_count += 1
            continue

        if dedupe_key in seen_keys:
            skipped_count += 1
            continue
        seen_keys.add(dedupe_key)

        existing_item = _find_existing_item(db=db, source=source, item=canonical_item)
        if existing_item is None:
            db.add(_build_content_item(source=source, item=canonical_item))
            inserted_count += 1
            continue

        has_changes = _apply_content_item_updates(existing_item, canonical_item)
        if has_changes:
            updated_count += 1
        else:
            skipped_count += 1

    source.last_synced_at = sync_started_at
    source.last_sync_status = NewsSourceSyncStatus.OK
    source.last_error_message = None

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        source.last_synced_at = sync_started_at
        source.last_sync_status = NewsSourceSyncStatus.FAILED
        source.last_error_message = f"Integrity error during sync: {exc.orig}"
        db.commit()
        raise SourceSyncFailedError("Integrity error during source sync.") from exc

    db.refresh(source)

    return SourceSyncResult(
        source=source,
        fetched_count=len(recent_items),
        inserted_count=inserted_count,
        updated_count=updated_count,
        skipped_count=skipped_count,
    )


def get_source_or_404(*, db: Session, source_id: UUID) -> NewsSource:
    source = db.get(NewsSource, source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found.",
        )

    return source


def _filter_recent_items(
    *,
    items: list[NormalizedContentItem],
    synced_at: datetime,
    max_age_hours: int,
) -> tuple[list[NormalizedContentItem], int]:
    if max_age_hours <= 0:
        return items, 0

    cutoff = synced_at - timedelta(hours=max_age_hours)
    recent_items: list[NormalizedContentItem] = []
    skipped_count = 0

    for item in items:
        published_at = _normalize_datetime(item.published_at)
        if published_at is None or published_at < cutoff:
            skipped_count += 1
            continue

        if published_at is not item.published_at:
            item = NormalizedContentItem(
                external_id=item.external_id,
                url=item.url,
                title=item.title,
                raw_text=item.raw_text,
                excerpt=item.excerpt,
                image_url=item.image_url,
                author_name=item.author_name,
                published_at=published_at,
                source_payload=item.source_payload,
            )

        recent_items.append(item)

    return recent_items, skipped_count


def _build_dedupe_key(item: NormalizedContentItem) -> tuple[str, str] | None:
    if item.external_id:
        return ("external_id", item.external_id)
    if item.url:
        return ("url", item.url)
    return None


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _canonicalize_item(item: NormalizedContentItem) -> NormalizedContentItem:
    source_payload = dict(item.source_payload)
    external_id = item.external_id
    if external_id and len(external_id) > 255:
        source_payload.setdefault("external_id_raw", external_id)
        external_id = f"sha256:{hashlib.sha256(external_id.encode('utf-8')).hexdigest()}"

    author_name = item.author_name
    if author_name and len(author_name) > 255:
        source_payload.setdefault("author_name_raw", author_name)
        author_name = author_name[:255]

    return NormalizedContentItem(
        external_id=external_id,
        url=item.url,
        title=item.title,
        raw_text=item.raw_text,
        excerpt=item.excerpt,
        image_url=item.image_url,
        author_name=author_name,
        published_at=item.published_at,
        source_payload=source_payload,
    )


def _find_existing_item(
    *,
    db: Session,
    source: NewsSource,
    item: NormalizedContentItem,
) -> ContentItem | None:
    if item.external_id:
        existing_by_external_id = db.scalar(
            select(ContentItem).where(
                ContentItem.source_id == source.id,
                ContentItem.external_id == item.external_id,
            )
        )
        if existing_by_external_id is not None:
            return existing_by_external_id

    if item.url:
        return db.scalar(
            select(ContentItem).where(
                ContentItem.source_id == source.id,
                ContentItem.url == item.url,
            )
        )

    return None


def _build_content_item(
    *,
    source: NewsSource,
    item: NormalizedContentItem,
) -> ContentItem:
    return ContentItem(
        source_id=source.id,
        external_id=item.external_id,
        url=item.url,
        title=item.title,
        raw_text=item.raw_text,
        excerpt=item.excerpt,
        image_url=item.image_url,
        author_name=item.author_name,
        published_at=item.published_at,
        status=ContentItemStatus.NEW,
        source_payload=item.source_payload,
    )


def _apply_content_item_updates(
    existing_item: ContentItem,
    updated_item: NormalizedContentItem,
) -> bool:
    has_changes = False
    field_mapping = {
        "external_id": updated_item.external_id,
        "url": updated_item.url,
        "title": updated_item.title,
        "raw_text": updated_item.raw_text,
        "excerpt": updated_item.excerpt,
        "image_url": updated_item.image_url,
        "author_name": updated_item.author_name,
        "published_at": updated_item.published_at,
        "source_payload": updated_item.source_payload,
    }

    for field_name, field_value in field_mapping.items():
        if getattr(existing_item, field_name) != field_value:
            setattr(existing_item, field_name, field_value)
            has_changes = True

    return has_changes
