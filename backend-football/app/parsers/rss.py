from __future__ import annotations

import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Iterable
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

from app.db.models.news_source import NewsSource
from app.parsers.base import NormalizedContentItem

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_MIN_FULL_TEXT_LENGTH = 420
_FULL_ARTICLE_ENABLED_DOMAINS = {
    "www.championat.com",
    "championat.com",
}


class RssAdapterError(ValueError):
    """Raised when RSS source configuration or feed payload is invalid."""


class RssAdapter:
    def run(self, source: NewsSource) -> list[NormalizedContentItem]:
        feed_url = self._get_feed_url(source)
        xml_payload = self._fetch(feed_url)
        root = ET.fromstring(xml_payload)

        if self._tag_name(root.tag) == "feed":
            return self._parse_atom_entries(root, feed_url, source)

        channel = root.find("./channel")
        if channel is None:
            raise RssAdapterError("RSS feed does not contain channel element.")

        return self._parse_rss_items(channel.findall("./item"), feed_url, source)

    def _get_feed_url(self, source: NewsSource) -> str:
        adapter_feed_url = source.adapter_config.get("feed_url")
        if isinstance(adapter_feed_url, str) and adapter_feed_url.strip():
            return adapter_feed_url.strip()

        if source.base_url:
            return source.base_url.strip()

        raise RssAdapterError("RSS source does not define feed_url in adapter_config.")

    def _fetch(self, feed_url: str) -> bytes:
        request = Request(
            feed_url,
            headers={
                "User-Agent": "football-tg-app/0.1 (+https://localhost)",
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
            },
        )
        with urlopen(request, timeout=20) as response:
            return response.read()

    def _fetch_article_html(self, article_url: str) -> str:
        request = Request(
            article_url,
            headers={
                "User-Agent": "football-tg-app/0.1 (+https://localhost)",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8", errors="ignore")

    def _parse_rss_items(
        self,
        items: Iterable[ET.Element],
        feed_url: str,
        source: NewsSource,
    ) -> list[NormalizedContentItem]:
        normalized_items: list[NormalizedContentItem] = []

        for item in items:
            title = self._clean_text(self._child_text(item, "title"))
            if not title:
                continue

            link = self._clean_text(self._child_text(item, "link"))
            external_id = self._clean_text(self._child_text(item, "guid")) or link
            description = (
                self._clean_html_text(self._child_text(item, "description"))
                or self._clean_html_text(self._child_text(item, "encoded"))
                or title
            )
            description = self._maybe_fetch_full_article(
                source=source,
                article_url=link,
                current_text=description,
            )
            excerpt = self._build_excerpt(description)
            author = self._clean_text(
                self._child_text(item, "author") or self._child_text(item, "creator")
            )
            published_at = self._parse_datetime(
                self._child_text(item, "pubDate")
                or self._child_text(item, "published")
                or self._child_text(item, "updated")
            )
            image_url = self._extract_media_url(item)

            normalized_items.append(
                NormalizedContentItem(
                    external_id=external_id,
                    url=link,
                    title=title,
                    raw_text=description,
                    excerpt=excerpt,
                    image_url=image_url,
                    author_name=author,
                    published_at=published_at,
                    source_payload={"feed_url": feed_url},
                )
            )

        return normalized_items

    def _parse_atom_entries(
        self,
        root: ET.Element,
        feed_url: str,
        source: NewsSource,
    ) -> list[NormalizedContentItem]:
        normalized_items: list[NormalizedContentItem] = []

        for entry in root.findall(self._ns_path(root.tag, "entry")):
            title = self._clean_text(self._child_text(entry, "title"))
            if not title:
                continue

            link = self._atom_link(entry)
            external_id = self._clean_text(self._child_text(entry, "id")) or link
            content = (
                self._clean_html_text(self._child_text(entry, "content"))
                or self._clean_html_text(self._child_text(entry, "summary"))
                or title
            )
            content = self._maybe_fetch_full_article(
                source=source,
                article_url=link,
                current_text=content,
            )
            excerpt = self._build_excerpt(content)
            author = self._atom_author(entry)
            published_at = self._parse_datetime(
                self._child_text(entry, "published")
                or self._child_text(entry, "updated")
            )

            normalized_items.append(
                NormalizedContentItem(
                    external_id=external_id,
                    url=link,
                    title=title,
                    raw_text=content,
                    excerpt=excerpt,
                    author_name=author,
                    published_at=published_at,
                    source_payload={"feed_url": feed_url},
                )
            )

        return normalized_items

    def _atom_link(self, entry: ET.Element) -> str | None:
        for child in entry:
            if self._tag_name(child.tag) != "link":
                continue
            href = child.attrib.get("href")
            rel = child.attrib.get("rel", "alternate")
            if href and rel in {"alternate", ""}:
                return href.strip()

        return None

    def _atom_author(self, entry: ET.Element) -> str | None:
        for child in entry:
            if self._tag_name(child.tag) != "author":
                continue
            for nested in child:
                if self._tag_name(nested.tag) == "name" and nested.text:
                    return self._clean_text(nested.text)

        return None

    def _extract_media_url(self, item: ET.Element) -> str | None:
        for child in item:
            if self._tag_name(child.tag) in {"content", "thumbnail"}:
                media_url = child.attrib.get("url")
                if media_url:
                    return media_url.strip()

        return None

    def _maybe_fetch_full_article(
        self,
        *,
        source: NewsSource,
        article_url: str | None,
        current_text: str,
    ) -> str:
        if not article_url:
            return current_text

        if not self._should_fetch_full_article(
            source=source,
            article_url=article_url,
            current_text=current_text,
        ):
            return current_text

        try:
            html = self._fetch_article_html(article_url)
            extracted = self._extract_article_text(article_url=article_url, html=html)
        except Exception:
            return current_text

        if not extracted or len(extracted) <= len(current_text):
            return current_text

        return extracted

    def _should_fetch_full_article(
        self,
        *,
        source: NewsSource,
        article_url: str,
        current_text: str,
    ) -> bool:
        fetch_setting = source.adapter_config.get("fetch_full_article", True)
        if isinstance(fetch_setting, bool) and not fetch_setting:
            return False

        if len(current_text.strip()) >= _MIN_FULL_TEXT_LENGTH:
            return False

        hostname = urlparse(article_url).netloc.lower()
        return hostname in _FULL_ARTICLE_ENABLED_DOMAINS

    def _extract_article_text(self, *, article_url: str, html: str) -> str | None:
        hostname = urlparse(article_url).netloc.lower()

        if hostname in {"www.championat.com", "championat.com"}:
            return self._extract_championat_article_text(html)

        return None

    def _extract_championat_article_text(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one("div.article-content")
        if container is None:
            return None

        paragraphs: list[str] = []
        for paragraph in container.select("p"):
            text = self._clean_text(paragraph.get_text(" ", strip=True))
            if not text:
                continue
            paragraphs.append(text)

        if not paragraphs:
            return None

        article_text = "\n\n".join(paragraphs).strip()
        return article_text or None

    def _parse_datetime(self, raw_value: str | None) -> datetime | None:
        cleaned = self._clean_text(raw_value)
        if not cleaned:
            return None

        try:
            parsed = parsedate_to_datetime(cleaned)
        except (TypeError, ValueError, IndexError, OverflowError):
            parsed = None

        if parsed is not None:
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)

        try:
            parsed_iso = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        except ValueError:
            return None

        if parsed_iso.tzinfo is None:
            return parsed_iso.replace(tzinfo=UTC)
        return parsed_iso.astimezone(UTC)

    def _child_text(self, element: ET.Element, name: str) -> str | None:
        for child in element:
            if self._tag_name(child.tag) == name:
                return "".join(child.itertext()) if list(child) else child.text

        return None

    def _build_excerpt(self, value: str | None) -> str | None:
        cleaned = self._clean_text(value)
        if not cleaned:
            return None

        if len(cleaned) <= 220:
            return cleaned

        return f"{cleaned[:217].rstrip()}..."

    def _clean_html_text(self, value: str | None) -> str | None:
        if value is None:
            return None

        text = unescape(value)
        text = _TAG_RE.sub(" ", text)
        text = _WHITESPACE_RE.sub(" ", text).strip()
        return text or None

    def _clean_text(self, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = _WHITESPACE_RE.sub(" ", value).strip()
        return cleaned or None

    def _tag_name(self, tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1]
        if ":" in tag:
            return tag.split(":", 1)[1]
        return tag

    def _ns_path(self, root_tag: str, name: str) -> str:
        if root_tag.startswith("{"):
            namespace = root_tag.split("}", 1)[0][1:]
            return f"{{{namespace}}}{name}"
        return name
