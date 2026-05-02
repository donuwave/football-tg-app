from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings
from app.db.models.content_item import ContentItem
from app.services.translation import TranslationError, translate_news_item


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
        if not _looks_like_russian(text):
            text = _force_russian_rewrite(
                draft=text,
                item=item,
                instruction=normalized_instruction,
                settings=settings,
            )
        return AIRewriteResult(text=_sanitize_generated_post(text), mode="ollama")

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
        "prompt": _build_user_prompt(item=item, instruction=instruction, settings=settings),
        "system": _build_system_prompt(settings=settings),
        "stream": False,
        "keep_alive": settings.ai_ollama_keep_alive,
        "options": {
            "temperature": settings.ai_ollama_temperature,
            "top_p": settings.ai_ollama_top_p,
        },
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


def _build_user_prompt(
    *,
    item: ContentItem,
    instruction: str | None,
    settings: Settings,
) -> str:
    source_name = item.source.name if item.source else "unknown"
    source_ref = item.source.external_ref if item.source else None
    published_at = (
        item.published_at.astimezone(UTC).strftime("%d.%m.%Y %H:%M UTC")
        if item.published_at is not None
        else "unknown"
    )
    instruction_block = instruction or (
        "Сделай очень короткий факт для Telegram-канала: 1-2 предложения, "
        "без эмодзи, только главный факт и без лишнего контекста."
    )

    material_text = item.raw_text
    translation_mode = "original"
    source_text = " ".join([item.title or "", item.excerpt or "", item.raw_text]).strip()
    if source_text and not _looks_like_russian(source_text):
        try:
            translation = translate_news_item(item=item, settings=settings)
        except TranslationError:
            translation = None
        if translation is not None and translation.text.strip():
            material_text = translation.text
            translation_mode = translation.mode

    parts = [
        f"Задание редактора:\n{instruction_block}",
        "Факты по новости:",
        f"Заголовок: {item.title}",
        f"Источник: {source_name}",
        f"Референс источника: {source_ref or 'n/a'}",
        f"Время публикации источника: {published_at}",
        f"URL: {item.url or 'n/a'}",
        f"Краткое описание: {item.excerpt or 'n/a'}",
        "Язык ответа: только русский.",
        "Не используй форму призыва к действию вроде 'Смотрите', 'Читайте', 'Слушайте'.",
        "Если исходный заголовок построен как Watch/Read/Listen, перепиши его как нейтральный факт.",
        f"Режим подложки текста: {translation_mode}",
        "Текст материала для работы:",
        material_text,
        "",
        "Верни только готовый короткий факт для Telegram без пояснений.",
    ]
    return "\n".join(parts).strip()


def _force_russian_rewrite(
    *,
    draft: str,
    item: ContentItem,
    instruction: str | None,
    settings: Settings,
) -> str:
    base_url = settings.ai_ollama_base_url.rstrip("/")
    endpoint = f"{base_url}/generate" if base_url.endswith("/api") else f"{base_url}/api/generate"
    payload = {
        "model": settings.ai_ollama_model,
        "system": (
            f"{_build_system_prompt(settings=settings)} "
            "Ниже дан черновик поста не на русском языке или со смешанным языком. "
            "Полностью перепиши и переведи его на русский язык. "
            "Не используй служебные подписи вроде 'Заголовок новости', "
            "'Черновик для исправления', 'Источник новости'. "
            "Верни только русский текст без пояснений."
        ),
        "prompt": "\n".join(
            [
                f"Задание редактора: {instruction or 'Сделай короткий факт для Telegram.'}",
                f"Заголовок новости: {item.title}",
                "Черновик для исправления:",
                draft,
                "",
                "Верни только русский текст поста.",
            ]
        ),
        "stream": False,
        "keep_alive": settings.ai_ollama_keep_alive,
        "options": {
            "temperature": settings.ai_ollama_temperature,
            "top_p": settings.ai_ollama_top_p,
        },
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


def _build_stub_post(*, item: ContentItem, instruction: str | None) -> str:
    lead = item.title.strip().rstrip(".")
    summary_limit = _stub_summary_limit(instruction)
    summary = _normalize_text(item.excerpt or item.raw_text)
    if len(summary) > summary_limit:
        summary = f"{summary[:summary_limit - 3].rstrip()}..."

    if summary and summary.lower().startswith(lead.lower()):
        return summary

    if summary and not summary.endswith((".", "!", "?")):
        summary = f"{summary}."

    if summary:
        return f"{lead}. {summary}".strip()

    return lead


def _normalize_instruction(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = " ".join(value.split())
    return normalized or None


def _build_system_prompt(*, settings: Settings) -> str:
    return " ".join(
        [
            settings.ai_system_prompt.strip(),
            "Формулируй текст как нейтральный редакторский факт, а не как призыв к просмотру или действию.",
            "Не копируй англоязычный заголовок дословно, если он выглядит как Watch, Read, Listen или Highlights.",
            "Если новость про подборку, обзор или хайлайты, прямо скажи это как факт: например 'BBC Sport выпустил обзор...' .",
        ]
    ).strip()


def _normalize_text(value: str | None) -> str:
    return " ".join((value or "").split()).strip()


def _stub_summary_limit(instruction: str | None) -> int:
    if not instruction:
        return 180

    lowered = instruction.lower()
    if "очень корот" in lowered or "ультракорот" in lowered:
        return 110
    if "коротк" in lowered or "кратк" in lowered:
        return 160
    return 220


def _looks_like_russian(text: str) -> bool:
    if not text:
        return False

    cyrillic_count = sum(1 for char in text if "а" <= char.lower() <= "я" or char.lower() == "ё")
    latin_count = sum(1 for char in text if "a" <= char.lower() <= "z")

    if cyrillic_count == 0:
        return False

    return cyrillic_count >= latin_count


def _sanitize_generated_post(text: str) -> str:
    lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n")]
    cleaned_lines: list[str] = []

    for line in lines:
        if not line:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue

        normalized = line
        for prefix in (
            "Заголовок новости:",
            "Заголовок:",
            "Title:",
            "Черновик для исправления:",
            "Источник новости:",
        ):
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
                break

        if normalized:
            cleaned_lines.append(normalized)

    while cleaned_lines and cleaned_lines[-1] == "":
        cleaned_lines.pop()

    return "\n".join(cleaned_lines).strip()
