import json
from dataclasses import dataclass
from functools import lru_cache
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.core.config import Settings

MAX_TELEGRAM_TEXT_LENGTH = 4096


class TelegramPublishError(RuntimeError):
    """Raised when Telegram Bot API rejects a publication request."""


@dataclass(frozen=True)
class TelegramSendMessageResult:
    message_id: int


def append_channel_link(*, text: str, settings: Settings) -> str:
    normalized_text = text.strip()
    if not normalized_text:
        return normalized_text

    channel_url = _resolve_channel_url(settings=settings)
    if not channel_url or channel_url in normalized_text:
        return normalized_text

    footer = f"Подписаться: {channel_url}"
    message = f"{normalized_text}\n\n{footer}"
    if len(message) <= MAX_TELEGRAM_TEXT_LENGTH:
        return message

    available_length = MAX_TELEGRAM_TEXT_LENGTH - len(footer) - 2
    if available_length <= 1:
        return footer[:MAX_TELEGRAM_TEXT_LENGTH]

    truncated_body = normalized_text[: available_length - 1].rstrip()
    return f"{truncated_body}…\n\n{footer}"


def send_telegram_message(
    *,
    bot_token: str,
    channel_id: str,
    text: str,
) -> TelegramSendMessageResult:
    request = Request(
        url=f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=json.dumps(
            {
                "chat_id": channel_id,
                "text": text,
                "disable_web_page_preview": True,
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise TelegramPublishError(
            f"Telegram API HTTP error {exc.code}: {detail or exc.reason}"
        ) from exc
    except URLError as exc:
        raise TelegramPublishError(f"Telegram API is unreachable: {exc.reason}") from exc

    if not payload.get("ok"):
        raise TelegramPublishError(
            f"Telegram API rejected the message: {payload.get('description', 'unknown error')}"
        )

    result = payload.get("result") or {}
    message_id = result.get("message_id")
    if not isinstance(message_id, int):
        raise TelegramPublishError("Telegram API response does not include message_id.")

    return TelegramSendMessageResult(message_id=message_id)


def _resolve_channel_url(*, settings: Settings) -> str | None:
    if settings.telegram_channel_url:
        return settings.telegram_channel_url.strip() or None

    channel_id = settings.telegram_channel_id.strip()
    if channel_id.startswith("@") and len(channel_id) > 1:
        return f"https://t.me/{channel_id[1:]}"

    return _resolve_channel_url_via_bot_api(
        bot_token=settings.telegram_bot_token,
        channel_id=channel_id,
    )


@lru_cache(maxsize=16)
def _resolve_channel_url_via_bot_api(*, bot_token: str, channel_id: str) -> str | None:
    request = Request(
        url=(
            f"https://api.telegram.org/bot{bot_token}/getChat"
            f"?chat_id={quote(channel_id, safe='@-')}"
        ),
        method="GET",
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError):
        return None

    if not payload.get("ok"):
        return None

    result = payload.get("result") or {}
    username = str(result.get("username") or "").strip()
    if username:
        return f"https://t.me/{username}"

    invite_link = str(result.get("invite_link") or "").strip()
    if invite_link:
        return invite_link

    return None
