from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.db.models.enums import NewsSourceSyncStatus, NewsSourceType, enum_values


class NewsSource(Base):
    __tablename__ = "news_sources"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    source_type: Mapped[NewsSourceType] = mapped_column(
        Enum(
            NewsSourceType,
            name="news_source_type",
            values_callable=enum_values,
            validate_strings=True,
        ),
        nullable=False,
    )
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    adapter_config: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_status: Mapped[NewsSourceSyncStatus] = mapped_column(
        Enum(
            NewsSourceSyncStatus,
            name="news_source_sync_status",
            values_callable=enum_values,
            validate_strings=True,
        ),
        nullable=False,
        default=NewsSourceSyncStatus.NEVER_RUN,
    )
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    content_items = relationship(
        "ContentItem",
        back_populates="source",
        cascade="all, delete-orphan",
    )
