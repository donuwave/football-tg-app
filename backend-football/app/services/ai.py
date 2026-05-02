from __future__ import annotations

import json
import re
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
        text = _sanitize_generated_post(text)
        if _needs_stronger_news_hook(text=text, item=item):
            text = _sanitize_generated_post(
                _rewrite_with_stronger_news_hook(
                    draft=text,
                    item=item,
                    instruction=normalized_instruction,
                    settings=settings,
                )
            )
        text = _enhance_generic_fact(text=text, item=item)
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
        "Сделай короткий пост для Telegram-канала: без эмодзи, с главным крючком новости. "
        "Если достаточно одного факта, пиши очень коротко; если нужен контекст или цитата, "
        "можно 2-4 предложения без воды."
    )
    notable_quote = _extract_notable_quote(item.raw_text)

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
        "Если в материале есть сильная короткая цитата игрока или тренера, можно встроить её во второе предложение.",
        f"Потенциальная цитата: {notable_quote or 'n/a'}",
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


def _rewrite_with_stronger_news_hook(
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
            "Предыдущий вариант оказался слишком общим и пустым. "
            "Не используй формулы вроде 'поделился впечатлениями', 'высказался', "
            "'прокомментировал', если они не раскрывают саму новость. "
            "Вытащи главный крючок: бывший клуб, рекорд, конфликт, решение, травма, "
            "трансфер, признание, жёсткая цитата или необычный поворот. "
            "Верни короткий текст по сути. Если нужен контекст или цитата, "
            "допустимо 2-4 предложения."
        ),
        "prompt": "\n".join(
            [
                f"Задание редактора: {instruction or 'Сделай короткий факт для Telegram.'}",
                f"Заголовок новости: {item.title}",
                f"Краткое описание: {item.excerpt or 'n/a'}",
                "Полный текст новости:",
                item.raw_text[:4000],
                "",
                "Слабый вариант, который нельзя повторять:",
                draft,
                "",
                "Сделай сильнее и конкретнее. Плохо: 'поделился впечатлениями от гола'.",
                "Хорошо: вынести главный инфоповод и почему он интересен.",
                "Пример хорошей логики: не 'игрок поделился впечатлениями', а 'игрок забил бывшему клубу и признал, что эмоции были особенными'.",
                "Запрещённые слова без конкретики: 'поделился впечатлениями', 'высказался о', 'прокомментировал', 'рассказал о'.",
                "Верни только финальный русский текст.",
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
            "Если в тексте есть содержательная цитата игрока или тренера, можно добавить её целиком, при необходимости отдельным абзацем.",
            "Не стремись любой ценой уложить всё в одно или два предложения, если из-за этого теряется смысл.",
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


def _needs_stronger_news_hook(*, text: str, item: ContentItem) -> bool:
    normalized = text.lower()
    title = (item.title or "").lower()
    excerpt = (item.excerpt or "").lower()
    source_text = " ".join(part for part in [title, excerpt] if part).strip()

    forbidden_phrases = (
        "поделился впечатлениями",
        "высказался о",
        "прокомментировал",
        "рассказал о",
        "оценил",
    )
    if any(phrase in normalized for phrase in forbidden_phrases):
        return True

    generic_patterns = (
        "поделил",
        "высказал",
        "прокомментир",
        "рассказал",
        "оценил",
        "заявил",
    )
    if not any(pattern in normalized for pattern in generic_patterns):
        return False

    hook_markers = (
        "бывш",
        "ранее выступ",
        "1000",
        "рекорд",
        "гол",
        "бывшего клуба",
        "цска",
        "зенит",
        "трансфер",
        "травм",
        "скандал",
        "конфликт",
    )

    source_has_hook = any(marker in source_text for marker in hook_markers)
    output_has_hook = any(marker in normalized for marker in hook_markers)

    return source_has_hook and not output_has_hook


def _enhance_generic_fact(*, text: str, item: ContentItem) -> str:
    normalized = text.lower()
    if not any(
        phrase in normalized
        for phrase in (
            "поделился впечатлениями",
            "поделился эмоциями",
            "высказался о",
            "прокомментировал",
        )
    ):
        return text

    former_club_fact = _build_former_club_fact(item=item)
    if former_club_fact:
        return former_club_fact

    return text


def _build_former_club_fact(*, item: ContentItem) -> str | None:
    source_text = " ".join(part for part in [item.title, item.excerpt, item.raw_text] if part).strip()
    lowered = source_text.lower()
    if not any(marker in lowered for marker in ("выступал ранее", "бывшей моей команды", "бывшего клуба")):
        return None

    first_sentence = item.raw_text.split(".", 1)[0].strip()
    actor_match = re.search(
        r"^(.+?)\s+(?:поделился|высказался|прокомментировал|рассказал|оценил|заявил)\b",
        first_sentence,
        flags=re.IGNORECASE,
    )
    actor = actor_match.group(1).strip() if actor_match else None
    if not actor:
        return None

    former_club = None
    for pattern in (
        r"(?:в ворота|против)\s+([А-ЯA-ZЁ0-9][А-ЯA-ZЁ0-9\s«»\"-]{1,40})(?:,|\s+где|\s+\(|\s+за)",
        r"бывшей моей команды\s*[—-]?\s*([А-ЯA-ZЁ0-9][А-ЯA-ZЁ0-9\s«»\"-]{1,40})",
    ):
        match = re.search(pattern, source_text, flags=re.IGNORECASE)
        if match:
            former_club = match.group(1).strip(" ,.-")
            break

    if not former_club:
        return None

    quote = _extract_notable_quote(item.raw_text)
    if quote:
        return (
            f"{actor} забил {former_club}, за который раньше выступал, "
            "и признал особенные эмоции после этого гола."
            f"\n\n«{quote}»"
        )

    return (
        f"{actor} забил {former_club}, за который раньше выступал, "
        "и признал, что гол бывшей команде дался ему с особенными эмоциями."
    )


def _extract_notable_quote(text: str) -> str | None:
    if not text.strip():
        return None

    candidates: list[str] = []

    for match in re.finditer(r"—\s.*?\?\s*—\s*(.+?)(?=\n\s*\n—\s|\Z)", text, flags=re.S):
        candidate = _sanitize_quote_candidate(match.group(1), preserve_full_answer=True)
        if candidate:
            candidates.append(candidate)

    normalized = " ".join(text.split())
    for pattern in (r"«([^»]{20,520})»", r'"([^"]{20,520})"'):
        for match in re.finditer(pattern, normalized):
            candidate = _sanitize_quote_candidate(match.group(1))
            if candidate:
                candidates.append(candidate)

    if not candidates:
        return None

    scored_candidates = sorted(
        ((_score_quote_candidate(candidate), candidate) for candidate in candidates),
        key=lambda item: item[0],
        reverse=True,
    )
    best_score, best_candidate = scored_candidates[0]
    if best_score <= 0:
        return None

    return best_candidate


def _sanitize_quote_candidate(value: str, *, preserve_full_answer: bool = False) -> str | None:
    candidate = " ".join(value.split()).strip(" -—\"«»")
    if not candidate:
        return None

    candidate = re.sub(
        r"\s*[—-]\s*(?:приводит|привёл|цитирует|цитирует слова|сказал|сообщил|заявил)\b.*$",
        "",
        candidate,
        flags=re.IGNORECASE,
    ).strip(" -—\"«»")

    if not preserve_full_answer and len(candidate) > 180:
        sentences = re.split(r"(?<=[.!?])\s+", candidate)
        trimmed_sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
        if trimmed_sentences:
            candidate = max(trimmed_sentences, key=_score_quote_candidate)

    candidate = candidate.strip(" -—\"«»")
    if not candidate or len(candidate) < 18:
        return None

    return candidate.rstrip(".!?")


def _score_quote_candidate(value: str) -> int:
    lowered = value.lower()
    score = 0

    if 24 <= len(value) <= 260:
        score += 3
    elif len(value) <= 420:
        score += 1
    else:
        score -= 2

    if any(token in lowered for token in ("я ", "мне ", "мой ", "мы ", "нас ")):
        score += 2

    if any(
        token in lowered
        for token in (
            "эмоц",
            "главное",
            "выиграл",
            "бывш",
            "честно",
            "наконец",
            "гол",
            "команд",
            "цска",
        )
    ):
        score += 3

    if "?" in value:
        score -= 3

    if any(token in lowered for token in ("вопрос", "спросил", "матч с ахматом")):
        score -= 2

    return score
