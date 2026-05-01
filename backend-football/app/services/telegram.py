import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class TelegramPublishError(RuntimeError):
    """Raised when Telegram Bot API rejects a publication request."""


@dataclass(frozen=True)
class TelegramSendMessageResult:
    message_id: int


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

