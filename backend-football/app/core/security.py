import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import parse_qsl


class TelegramInitDataValidationError(ValueError):
    """Raised when initData does not match Telegram's integrity rules."""


class TelegramForbiddenUserError(ValueError):
    def __init__(self, user_id: int):
        super().__init__(f"Telegram user {user_id} is not allowed.")


@dataclass(frozen=True)
class TelegramUser:
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool | None = None


@dataclass(frozen=True)
class TelegramValidationResult:
    auth_date: datetime
    data_check_string: str
    query_id: str | None
    raw_init_data: str
    user: TelegramUser


def _build_secret_key(bot_token: str) -> bytes:
    return hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()


def _build_data_check_string(parsed_items: dict[str, str]) -> str:
    return "\n".join(
        f"{key}={value}" for key, value in sorted(parsed_items.items(), key=lambda item: item[0])
    )


def _parse_user(raw_user: str | None) -> TelegramUser:
    if not raw_user:
        raise TelegramInitDataValidationError("Telegram initData does not include user.")

    try:
        user_payload = json.loads(raw_user)
    except json.JSONDecodeError as exc:
        raise TelegramInitDataValidationError("Telegram user payload is invalid JSON.") from exc

    try:
        return TelegramUser(
            id=int(user_payload["id"]),
            first_name=user_payload.get("first_name"),
            last_name=user_payload.get("last_name"),
            username=user_payload.get("username"),
            language_code=user_payload.get("language_code"),
            is_premium=user_payload.get("is_premium"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise TelegramInitDataValidationError("Telegram user payload is incomplete.") from exc


def validate_telegram_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int,
) -> TelegramValidationResult:
    if not init_data:
        raise TelegramInitDataValidationError("initData is empty.")

    if not bot_token or bot_token == "your_bot_token":
        raise TelegramInitDataValidationError("Telegram bot token is not configured.")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
    received_hash = pairs.pop("hash", None)

    if not received_hash:
        raise TelegramInitDataValidationError("Telegram initData hash is missing.")

    data_check_string = _build_data_check_string(pairs)
    calculated_hash = hmac.new(
        key=_build_secret_key(bot_token),
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise TelegramInitDataValidationError("Telegram initData hash mismatch.")

    auth_date_raw = pairs.get("auth_date")
    if not auth_date_raw:
        raise TelegramInitDataValidationError("Telegram initData auth_date is missing.")

    try:
        auth_date = datetime.fromtimestamp(int(auth_date_raw), tz=UTC)
    except (TypeError, ValueError, OSError) as exc:
        raise TelegramInitDataValidationError("Telegram initData auth_date is invalid.") from exc

    now = datetime.now(tz=UTC)
    age_seconds = (now - auth_date).total_seconds()
    if age_seconds < 0:
        raise TelegramInitDataValidationError("Telegram initData auth_date is in the future.")
    if age_seconds > max_age_seconds:
        raise TelegramInitDataValidationError("Telegram initData is too old.")

    return TelegramValidationResult(
        auth_date=auth_date,
        data_check_string=data_check_string,
        query_id=pairs.get("query_id"),
        raw_init_data=init_data,
        user=_parse_user(pairs.get("user")),
    )
