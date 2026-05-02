from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings
from app.db.models.content_item import ContentItem


class AIRewriteError(RuntimeError):
    """Raised when the configured AI provider cannot return a rewritten post."""


@dataclass(frozen=True, slots=True)
class AIRewriteResult:
    text: str
    mode: str


def rewrite_news_post(
    *,
    item: ContentItem,
    instruction: str | None,
    settings: Settings,
) -> AIRewriteResult:
    normalized_instruction = _normalize_instruction(instruction)
    mode = settings.ai_service_mode.strip().lower()

    if mode == "ollama":
        text = _rewrite_with_ollama(
            item=item,
            instruction=normalized_instruction,
            settings=settings,
        )
        return AIRewriteResult(text=text, mode="ollama")

    return AIRewriteResult(
        text=_build_stub_post(item=item, instruction=normalized_instruction),
        mode="stub",
    )


def _rewrite_with_ollama(
    *,
    item: ContentItem,
    instruction: str | None,
    settings: Settings,
) -> str:
    base_url = settings.ai_ollama_base_url.rstrip("/")
    if base_url.endswith("/api"):
        endpoint = f"{base_url}/generate"
    else:
        endpoint = f"{base_url}/api/generate"

    payload = {
        "model": settings.ai_ollama_model,
        "prompt": _build_user_prompt(item=item, instruction=instruction),
        "system": settings.ai_system_prompt,
        "stream": False,
    }
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.ai_request_timeout_seconds) as response:
            raw_payload = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise AIRewriteError(
            f"Ollama HTTP error {exc.code}: {detail or exc.reason}"
        ) from exc
    except URLError as exc:
        raise AIRewriteError(
            f"Ollama is unreachable at {endpoint}: {exc.reason}"
        ) from exc

    try:
        parsed_payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise AIRewriteError("Ollama returned invalid JSON payload.") from exc

    response_text = str(parsed_payload.get("response") or "").strip()
    if not response_text:
        raise AIRewriteError("Ollama returned an empty response.")

    return response_text


def _build_user_prompt(*, item: ContentItem, instruction: str | None) -> str:
    source_name = item.source.name if item.source else "unknown"
    source_ref = item.source.external_ref if item.source else None
    published_at = (
        item.published_at.astimezone(UTC).strftime("%d.%m.%Y %H:%M UTC")
        if item.published_at is not None
        else "unknown"
    )
    instruction_block = instruction or (
        "Сделай короткий пост для Telegram-канала: 2-4 абзаца, без эмодзи, "
        "с сильным первым предложением и аккуратным завершением."
    )

    parts = [
        f"Задание редактора:\n{instruction_block}",
        "Факты по новости:",
        f"Заголовок: {item.title}",
        f"Источник: {source_name}",
        f"Референс источника: {source_ref or 'n/a'}",
        f"Время публикации источника: {published_at}",
        f"URL: {item.url or 'n/a'}",
        f"Краткое описание: {item.excerpt or 'n/a'}",
        "Полный текст:",
        item.raw_text,
        "",
        "Верни только готовый текст поста для Telegram без пояснений.",
    ]
    return "\n".join(parts).strip()


def _build_stub_post(*, item: ContentItem, instruction: str | None) -> str:
    lead = item.title.strip().rstrip(".")
    summary = (item.excerpt or item.raw_text).strip()
    summary = " ".join(summary.split())
    if len(summary) > 320:
        summary = f"{summary[:317].rstrip()}..."

    source_label = item.source.external_ref or item.source.name if item.source else "source"
    published_hint = ""
    if item.published_at is not None:
        published_hint = item.published_at.astimezone(UTC).strftime("%d.%m %H:%M UTC")

    lines = [lead, "", summary]

    if instruction:
        lines.extend(["", f"Редакторская задача: {instruction}"])

    footer = f"Источник: {source_label}"
    if published_hint:
        footer = f"{footer} • {published_hint}"
    lines.extend(["", footer])

    return "\n".join(lines).strip()


def _normalize_instruction(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = " ".join(value.split())
    return normalized or None
