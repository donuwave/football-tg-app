from datetime import datetime

from pydantic import BaseModel

from app.core.security import TelegramValidationResult


class TelegramVerifyRequest(BaseModel):
    initData: str


class TelegramUserResponse(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool | None = None


class TelegramAuthResponse(BaseModel):
    success: bool
    allowed: bool
    telegram_user_id: int
    auth_date: datetime
    query_id: str | None = None
    user: TelegramUserResponse

    @classmethod
    def from_validation_result(
        cls,
        result: TelegramValidationResult,
        allowed: bool,
    ) -> "TelegramAuthResponse":
        return cls(
            success=True,
            allowed=allowed,
            telegram_user_id=result.user.id,
            auth_date=result.auth_date,
            query_id=result.query_id,
            user=TelegramUserResponse(
                id=result.user.id,
                first_name=result.user.first_name,
                last_name=result.user.last_name,
                username=result.user.username,
                language_code=result.user.language_code,
                is_premium=result.user.is_premium,
            ),
        )
