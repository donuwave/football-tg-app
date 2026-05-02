from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.db.models.news_source import NewsSource


@dataclass(frozen=True, slots=True)
class NormalizedContentItem:
    title: str
    raw_text: str
    external_id: str | None = None
    url: str | None = None
    excerpt: str | None = None
    image_url: str | None = None
    author_name: str | None = None
    published_at: datetime | None = None
    source_payload: dict[str, object] = field(default_factory=dict)


class SourceAdapter(Protocol):
    def run(self, source: NewsSource) -> list[NormalizedContentItem]:
        ...
