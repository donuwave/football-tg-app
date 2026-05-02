from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models.news_source import NewsSource
from app.db.models.enums import NewsSourceSyncStatus, NewsSourceType


class SourceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source_type: NewsSourceType
    base_url: str | None = None
    external_ref: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    adapter_config: dict[str, Any] = Field(default_factory=dict)


class SourceUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    base_url: str | None = None
    external_ref: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    adapter_config: dict[str, Any] | None = None


class SourceResponse(BaseModel):
    id: UUID
    name: str
    source_type: str
    base_url: str | None = None
    external_ref: str | None = None
    is_active: bool
    adapter_config: dict[str, Any]
    last_synced_at: datetime | None = None
    last_sync_status: str
    last_error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, source: NewsSource) -> "SourceResponse":
        return cls(
            id=source.id,
            name=source.name,
            source_type=source.source_type.value,
            base_url=source.base_url,
            external_ref=source.external_ref,
            is_active=source.is_active,
            adapter_config=source.adapter_config,
            last_synced_at=source.last_synced_at,
            last_sync_status=source.last_sync_status.value,
            last_error_message=source.last_error_message,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )


class SourceSyncResponse(BaseModel):
    source: SourceResponse
    fetched_count: int
    inserted_count: int
    updated_count: int
    skipped_count: int
    sync_status: str


class SourceListResponse(BaseModel):
    items: list[SourceResponse]
