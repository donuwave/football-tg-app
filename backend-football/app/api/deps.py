from typing import Annotated, Generator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import (
    TelegramForbiddenUserError,
    TelegramInitDataValidationError,
    TelegramValidationResult,
    validate_telegram_init_data,
)
from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_app_settings() -> Settings:
    return get_settings()


def get_telegram_context(
    settings: Annotated[Settings, Depends(get_app_settings)],
    init_data: Annotated[str | None, Header(alias="X-Telegram-Init-Data")] = None,
) -> TelegramValidationResult:
    if not init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Telegram-Init-Data header.",
        )

    try:
        return validate_telegram_init_data(
            init_data=init_data,
            bot_token=settings.telegram_bot_token,
            max_age_seconds=settings.telegram_init_data_ttl_seconds,
        )
    except TelegramInitDataValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


def require_allowed_telegram_user(
    settings: Annotated[Settings, Depends(get_app_settings)],
    telegram_context: Annotated[TelegramValidationResult, Depends(get_telegram_context)],
) -> TelegramValidationResult:
    if telegram_context.user.id != settings.telegram_allowed_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(TelegramForbiddenUserError(telegram_context.user.id)),
        )

    return telegram_context
