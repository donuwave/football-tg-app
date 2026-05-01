from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.db.models.enums import ContentItemStatus, enum_values


class ContentItem(Base):
    __tablename__ = "content_items"
    __table_args__ = (
        Index("ix_content_items_status", "status"),
        Index("ix_content_items_source_published_at", "source_id", "published_at"),
        Index(
            "uq_content_items_source_external_id",
            "source_id",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
            sqlite_where=text("external_id IS NOT NULL"),
        ),
        Index(
            "uq_content_items_source_url_when_no_external_id",
            "source_id",
            "url",
            unique=True,
            postgresql_where=text("external_id IS NULL AND url IS NOT NULL"),
            sqlite_where=text("external_id IS NULL AND url IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("news_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ContentItemStatus] = mapped_column(
        Enum(
            ContentItemStatus,
            name="content_item_status",
            values_callable=enum_values,
            validate_strings=True,
        ),
        nullable=False,
        default=ContentItemStatus.NEW,
    )
    source_payload: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    source = relationship("NewsSource", back_populates="content_items")
    publication_batches = relationship("PublicationBatch", back_populates="source_item")
