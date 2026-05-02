from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_allowed_telegram_user
from app.core.security import TelegramValidationResult
from app.schemas.sources import (
    SourceCreateRequest,
    SourceListResponse,
    SourceResponse,
    SourceSyncResponse,
    SourceUpdateRequest,
)
from app.services.sources import create_source, get_source_or_404, list_sources, sync_source_now, update_source

router = APIRouter()


@router.get("", response_model=SourceListResponse)
def get_sources(
    _: Annotated[TelegramValidationResult, Depends(require_allowed_telegram_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SourceListResponse:
    items = list_sources(db=db)
    return SourceListResponse(items=[SourceResponse.from_model(item) for item in items])


@router.post("", response_model=SourceResponse, status_code=201)
def create_news_source(
    payload: SourceCreateRequest,
    _: Annotated[TelegramValidationResult, Depends(require_allowed_telegram_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SourceResponse:
    source = create_source(db=db, payload=payload)
    return SourceResponse.from_model(source)


@router.get("/{source_id}", response_model=SourceResponse)
def get_news_source(
    source_id: UUID,
    _: Annotated[TelegramValidationResult, Depends(require_allowed_telegram_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SourceResponse:
    source = get_source_or_404(db=db, source_id=source_id)
    return SourceResponse.from_model(source)


@router.patch("/{source_id}", response_model=SourceResponse)
def update_news_source(
    source_id: UUID,
    payload: SourceUpdateRequest,
    _: Annotated[TelegramValidationResult, Depends(require_allowed_telegram_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SourceResponse:
    source = update_source(db=db, source_id=source_id, payload=payload)
    return SourceResponse.from_model(source)


@router.post("/{source_id}/sync", response_model=SourceSyncResponse)
def sync_news_source_now(
    source_id: UUID,
    _: Annotated[TelegramValidationResult, Depends(require_allowed_telegram_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SourceSyncResponse:
    result = sync_source_now(db=db, source_id=source_id)
    return SourceSyncResponse(
        source=SourceResponse.from_model(result.source),
        fetched_count=result.fetched_count,
        inserted_count=result.inserted_count,
        updated_count=result.updated_count,
        skipped_count=result.skipped_count,
        sync_status=result.source.last_sync_status.value,
    )
