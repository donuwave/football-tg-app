from __future__ import annotations

from dataclasses import dataclass

from deep_translator import GoogleTranslator

from app.core.config import Settings
from app.db.models.content_item import ContentItem

MAX_TRANSLATION_CHUNK_SIZE = 4200


class TranslationError(RuntimeError):
    """Raised when the configured translation provider cannot return a translation."""


@dataclass(frozen=True, slots=True)
class TranslationResult:
    text: str
    mode: str


def translate_news_item(
    *,
    item: ContentItem,
    settings: Settings,
) -> TranslationResult:
    source_text = _build_news_translation_payload(item)
    return translate_text_to_russian(text=source_text, settings=settings)


def translate_text_to_russian(
    *,
    text: str,
    settings: Settings,
) -> TranslationResult:
    normalized_text = " ".join(text.split()) if "\n" not in text else text.strip()
    if not normalized_text:
        return TranslationResult(text="", mode="empty")

    mode = settings.translation_service_mode.strip().lower()
    if mode in {"", "none", "disabled"}:
        return TranslationResult(text=normalized_text, mode="original")

    if mode != "google":
        raise TranslationError(f"Unsupported translation mode: {mode}")

    try:
        translated = _translate_with_google(
            text=normalized_text,
            target_language=settings.translation_target_language,
        )
    except Exception as exc:  # pragma: no cover - network/provider failures
        raise TranslationError(f"Translation failed: {exc}") from exc

    return TranslationResult(text=translated.strip(), mode="google")


def _translate_with_google(*, text: str, target_language: str) -> str:
    translator = GoogleTranslator(source="auto", target=target_language)
    chunks = _split_text(text=text, limit=MAX_TRANSLATION_CHUNK_SIZE)
    translated_chunks = [translator.translate(chunk) for chunk in chunks if chunk.strip()]
    return "\n\n".join(chunk.strip() for chunk in translated_chunks if chunk and chunk.strip())


def _build_news_translation_payload(item: ContentItem) -> str:
    blocks: list[str] = []

    if item.title.strip():
        blocks.append(item.title.strip())

    if item.excerpt and item.excerpt.strip() and item.excerpt.strip() != item.title.strip():
        blocks.append(item.excerpt.strip())

    raw_text = item.raw_text.strip()
    if raw_text and raw_text not in blocks:
        blocks.append(raw_text)

    return "\n\n".join(blocks).strip()


def _split_text(*, text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_length = 0

    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if len(paragraph) > limit:
            if current:
                chunks.append("\n\n".join(current).strip())
                current = []
                current_length = 0

            chunks.extend(_split_long_paragraph(paragraph=paragraph, limit=limit))
            continue

        projected_length = current_length + len(paragraph) + (2 if current else 0)
        if projected_length > limit and current:
            chunks.append("\n\n".join(current).strip())
            current = [paragraph]
            current_length = len(paragraph)
            continue

        current.append(paragraph)
        current_length = projected_length

    if current:
        chunks.append("\n\n".join(current).strip())

    return chunks


def _split_long_paragraph(*, paragraph: str, limit: int) -> list[str]:
    words = paragraph.split()
    chunks: list[str] = []
    current_words: list[str] = []
    current_length = 0

    for word in words:
        projected_length = current_length + len(word) + (1 if current_words else 0)
        if projected_length > limit and current_words:
            chunks.append(" ".join(current_words))
            current_words = [word]
            current_length = len(word)
            continue

        current_words.append(word)
        current_length = projected_length

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks
