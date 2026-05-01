from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_app_settings, require_allowed_telegram_user
from app.core.config import Settings
from app.core.security import (
    TelegramForbiddenUserError,
    TelegramInitDataValidationError,
    TelegramValidationResult,
    validate_telegram_init_data,
)
from app.schemas.auth import TelegramAuthResponse, TelegramVerifyRequest

router = APIRouter()


@router.post("/verify", response_model=TelegramAuthResponse)
def verify_telegram_auth(
    payload: TelegramVerifyRequest,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> TelegramAuthResponse:
    try:
        result = validate_telegram_init_data(
            init_data=payload.initData,
            bot_token=settings.telegram_bot_token,
            max_age_seconds=settings.telegram_init_data_ttl_seconds,
        )
    except TelegramInitDataValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    if result.user.id != settings.telegram_allowed_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(TelegramForbiddenUserError(result.user.id)),
        )

    return TelegramAuthResponse.from_validation_result(result=result, allowed=True)


@router.get("/me", response_model=TelegramAuthResponse)
def get_current_telegram_user(
    telegram_context: Annotated[
        TelegramValidationResult, Depends(require_allowed_telegram_user)
    ],
) -> TelegramAuthResponse:
    return TelegramAuthResponse.from_validation_result(
        result=telegram_context,
        allowed=True,
    )
