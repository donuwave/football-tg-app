from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.enums import NewsSourceType
from app.db.models.news_source import NewsSource
from app.parsers.registry import UnsupportedSourceTypeError
from app.schemas.sources import SourceCreateRequest, SourceUpdateRequest
from app.services.parser import SourceSyncFailedError, SourceSyncResult, get_source_or_404, sync_news_source


def list_sources(*, db: Session) -> list[NewsSource]:
    return db.scalars(select(NewsSource).order_by(NewsSource.created_at.desc())).all()


def create_source(*, db: Session, payload: SourceCreateRequest) -> NewsSource:
    _validate_source_payload(
        source_type=payload.source_type,
        base_url=payload.base_url,
        adapter_config=payload.adapter_config,
    )

    source = NewsSource(
        name=payload.name.strip(),
        source_type=payload.source_type,
        base_url=_normalize_optional_string(payload.base_url),
        external_ref=_normalize_optional_string(payload.external_ref),
        is_active=payload.is_active,
        adapter_config=payload.adapter_config,
    )
    db.add(source)
    _commit_or_conflict(db)
    db.refresh(source)
    return source


def update_source(
    *,
    db: Session,
    source_id: UUID,
    payload: SourceUpdateRequest,
) -> NewsSource:
    source = get_source_or_404(db=db, source_id=source_id)
    provided_fields = payload.model_fields_set

    if "name" in provided_fields and payload.name is not None:
        source.name = payload.name.strip()
    if "base_url" in provided_fields:
        source.base_url = _normalize_optional_string(payload.base_url)
    if "external_ref" in provided_fields:
        source.external_ref = _normalize_optional_string(payload.external_ref)
    if "is_active" in provided_fields:
        source.is_active = payload.is_active
    if "adapter_config" in provided_fields and payload.adapter_config is not None:
        source.adapter_config = payload.adapter_config

    _validate_source_payload(
        source_type=source.source_type,
        base_url=source.base_url,
        adapter_config=source.adapter_config,
    )
    _commit_or_conflict(db)
    db.refresh(source)
    return source


def sync_source_now(*, db: Session, source_id: UUID) -> SourceSyncResult:
    source = get_source_or_404(db=db, source_id=source_id)

    try:
        return sync_news_source(db=db, source=source)
    except UnsupportedSourceTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except SourceSyncFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


def _validate_source_payload(
    *,
    source_type: NewsSourceType,
    base_url: str | None,
    adapter_config: dict[str, Any],
) -> None:
    if source_type is not NewsSourceType.RSS:
        return

    feed_url = adapter_config.get("feed_url")
    if isinstance(feed_url, str) and feed_url.strip():
        return

    if base_url and base_url.strip():
        return

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="RSS source requires adapter_config.feed_url or base_url.",
    )


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Source with the same unique fields already exists.",
        ) from exc
