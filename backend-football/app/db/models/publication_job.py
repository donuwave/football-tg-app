from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.db.models.enums import PublicationJobStatus, PublicationJobType, PublicationPlatform


class PublicationJob(Base):
    __tablename__ = "publication_jobs"
    __table_args__ = (
        Index("ix_publication_jobs_status", "status"),
        Index("ix_publication_jobs_platform", "platform"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    batch_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("publication_batches.id", ondelete="CASCADE"),
        nullable=False,
    )
    platform: Mapped[PublicationPlatform] = mapped_column(
        Enum(PublicationPlatform, name="publication_platform"),
        nullable=False,
    )
    job_type: Mapped[PublicationJobType] = mapped_column(
        Enum(PublicationJobType, name="publication_job_type"),
        nullable=False,
    )
    status: Mapped[PublicationJobStatus] = mapped_column(
        Enum(PublicationJobStatus, name="publication_job_status"),
        nullable=False,
        default=PublicationJobStatus.QUEUED,
    )
    platform_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    external_publication_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    batch = relationship("PublicationBatch", back_populates="jobs")
