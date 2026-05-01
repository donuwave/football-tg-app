from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.db.models.content_item import ContentItem
    from app.db.models.news_source import NewsSource


class NewsSourceResponse(BaseModel):
    id: UUID
    name: str
    source_type: str
    external_ref: str | None = None
    is_active: bool
    last_synced_at: datetime | None = None

    @classmethod
    def from_model(cls, source: NewsSource) -> "NewsSourceResponse":
        return cls(
            id=source.id,
            name=source.name,
            source_type=source.source_type.value,
            external_ref=source.external_ref,
            is_active=source.is_active,
            last_synced_at=source.last_synced_at,
        )


class NewsItemResponse(BaseModel):
    id: UUID
    source_id: UUID
    title: str
    excerpt: str | None = None
    raw_text: str
    published_at: datetime | None = None
    status: str
    image_hint: str | None = None
    source: NewsSourceResponse

    @classmethod
    def from_model(cls, item: ContentItem) -> "NewsItemResponse":
        if item.source is None:
            raise ValueError("ContentItem.source must be loaded before serialization.")

        return cls(
            id=item.id,
            source_id=item.source_id,
            title=item.title,
            excerpt=item.excerpt,
            raw_text=item.raw_text,
            published_at=item.published_at,
            status=item.status.value,
            image_hint=(item.source_payload or {}).get("image_hint"),  # type: ignore[arg-type]
            source=NewsSourceResponse.from_model(item.source),
        )


class NewsFeedResponse(BaseModel):
    items: list[NewsItemResponse]
    sources: list[NewsSourceResponse]


class NewsGenerateResponse(BaseModel):
    item_id: UUID
    text: str


class NewsPublishRequest(BaseModel):
    text: str


class NewsPublishResponse(BaseModel):
    item_id: UUID
    batch_id: UUID
    job_id: UUID
    status: str
    platform: str
    external_publication_id: str | None = None
