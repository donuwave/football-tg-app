from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_app_settings, get_db, require_allowed_telegram_user
from app.core.config import Settings
from app.core.security import TelegramValidationResult
from app.db.models.enums import NewsSourceType
from app.schemas.news import (
    NewsFeedResponse,
    NewsGenerateRequest,
    NewsGenerateResponse,
    NewsItemResponse,
    NewsPublishRequest,
    NewsPublishResponse,
    NewsTranslateResponse,
)
from app.services.news import (
    generate_news_post,
    get_news_item_or_404,
    list_news_feed,
    publish_news_item,
    translate_news_item_for_reading,
)

router = APIRouter()


@router.get("", response_model=NewsFeedResponse)
def get_news_feed(
    _: Annotated[TelegramValidationResult, Depends(require_allowed_telegram_user)],
    db: Annotated[Session, Depends(get_db)],
    source_type: Annotated[NewsSourceType | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> NewsFeedResponse:
    return list_news_feed(db=db, source_type=source_type, limit=limit)


@router.get("/{news_id}", response_model=NewsItemResponse)
def get_news_item(
    news_id: UUID,
    _: Annotated[TelegramValidationResult, Depends(require_allowed_telegram_user)],
    db: Annotated[Session, Depends(get_db)],
) -> NewsItemResponse:
    item = get_news_item_or_404(db=db, news_id=news_id)
    return NewsItemResponse.from_model(item)


@router.post("/{news_id}/generate-post", response_model=NewsGenerateResponse)
def generate_news_item_post(
    news_id: UUID,
    payload: NewsGenerateRequest,
    _: Annotated[TelegramValidationResult, Depends(require_allowed_telegram_user)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    db: Annotated[Session, Depends(get_db)],
) -> NewsGenerateResponse:
    item = get_news_item_or_404(db=db, news_id=news_id)
    return generate_news_post(
        item=item,
        instruction=payload.instruction,
        settings=settings,
    )


@router.post("/{news_id}/translate", response_model=NewsTranslateResponse)
def translate_news_item_text(
    news_id: UUID,
    _: Annotated[TelegramValidationResult, Depends(require_allowed_telegram_user)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    db: Annotated[Session, Depends(get_db)],
) -> NewsTranslateResponse:
    item = get_news_item_or_404(db=db, news_id=news_id)
    return translate_news_item_for_reading(
        item=item,
        settings=settings,
    )


@router.post("/{news_id}/publish", response_model=NewsPublishResponse)
def publish_news_item_post(
    news_id: UUID,
    payload: NewsPublishRequest,
    telegram_context: Annotated[
        TelegramValidationResult, Depends(require_allowed_telegram_user)
    ],
    settings: Annotated[Settings, Depends(get_app_settings)],
    db: Annotated[Session, Depends(get_db)],
) -> NewsPublishResponse:
    item = get_news_item_or_404(db=db, news_id=news_id)
    return publish_news_item(
        db=db,
        item=item,
        text=payload.text,
        settings=settings,
        telegram_context=telegram_context,
    )
