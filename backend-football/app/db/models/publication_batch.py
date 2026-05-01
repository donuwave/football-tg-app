from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.db.models.enums import PublicationBatchStatus, PublicationBatchType, enum_values


class PublicationBatch(Base):
    __tablename__ = "publication_batches"
    __table_args__ = (
        Index("ix_publication_batches_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    batch_type: Mapped[PublicationBatchType] = mapped_column(
        Enum(
            PublicationBatchType,
            name="publication_batch_type",
            values_callable=enum_values,
            validate_strings=True,
        ),
        nullable=False,
    )
    status: Mapped[PublicationBatchStatus] = mapped_column(
        Enum(
            PublicationBatchStatus,
            name="publication_batch_status",
            values_callable=enum_values,
            validate_strings=True,
        ),
        nullable=False,
        default=PublicationBatchStatus.QUEUED,
    )
    created_by_telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_item_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("content_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    request_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    result_summary: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
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

    source_item = relationship("ContentItem", back_populates="publication_batches")
    jobs = relationship(
        "PublicationJob",
        back_populates="batch",
        cascade="all, delete-orphan",
    )
