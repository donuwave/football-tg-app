"""Initial schema for sources, content items and publication jobs."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260501_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    news_source_type = sa.Enum("rss", "x", "website", name="news_source_type")
    news_source_sync_status = sa.Enum(
        "never_run",
        "ok",
        "failed",
        name="news_source_sync_status",
    )
    content_item_status = sa.Enum(
        "new",
        "published",
        "archived",
        name="content_item_status",
    )
    publication_batch_type = sa.Enum(
        "news_post",
        "rubric_post",
        name="publication_batch_type",
    )
    publication_batch_status = sa.Enum(
        "queued",
        "processing",
        "completed",
        "partially_failed",
        "failed",
        name="publication_batch_status",
    )
    publication_platform = sa.Enum(
        "telegram",
        "vk",
        "youtube",
        name="publication_platform",
    )
    publication_job_type = sa.Enum(
        "text_post",
        "video_post",
        "mixed_post",
        name="publication_job_type",
    )
    publication_job_status = sa.Enum(
        "queued",
        "processing",
        "published",
        "failed",
        name="publication_job_status",
    )

    op.create_table(
        "news_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", news_source_type, nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("external_ref", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("adapter_config", sa.JSON(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", news_source_sync_status, nullable=False),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "content_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("author_name", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", content_item_status, nullable=False),
        sa.Column("source_payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["source_id"], ["news_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_content_items_status",
        "content_items",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_content_items_source_published_at",
        "content_items",
        ["source_id", "published_at"],
        unique=False,
    )
    op.create_index(
        "uq_content_items_source_external_id",
        "content_items",
        ["source_id", "external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
        sqlite_where=sa.text("external_id IS NOT NULL"),
    )
    op.create_index(
        "uq_content_items_source_url_when_no_external_id",
        "content_items",
        ["source_id", "url"],
        unique=True,
        postgresql_where=sa.text("external_id IS NULL AND url IS NOT NULL"),
        sqlite_where=sa.text("external_id IS NULL AND url IS NOT NULL"),
    )

    op.create_table(
        "publication_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("batch_type", publication_batch_type, nullable=False),
        sa.Column("status", publication_batch_status, nullable=False),
        sa.Column("created_by_telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("source_item_id", sa.Uuid(), nullable=True),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("result_summary", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["source_item_id"],
            ["content_items.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_publication_batches_status",
        "publication_batches",
        ["status"],
        unique=False,
    )

    op.create_table(
        "publication_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("platform", publication_platform, nullable=False),
        sa.Column("job_type", publication_job_type, nullable=False),
        sa.Column("status", publication_job_status, nullable=False),
        sa.Column("platform_payload", sa.JSON(), nullable=False),
        sa.Column("external_publication_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["publication_batches.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_publication_jobs_status",
        "publication_jobs",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_publication_jobs_platform",
        "publication_jobs",
        ["platform"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_publication_jobs_platform", table_name="publication_jobs")
    op.drop_index("ix_publication_jobs_status", table_name="publication_jobs")
    op.drop_table("publication_jobs")

    op.drop_index("ix_publication_batches_status", table_name="publication_batches")
    op.drop_table("publication_batches")

    op.drop_index(
        "uq_content_items_source_url_when_no_external_id",
        table_name="content_items",
    )
    op.drop_index("uq_content_items_source_external_id", table_name="content_items")
    op.drop_index("ix_content_items_source_published_at", table_name="content_items")
    op.drop_index("ix_content_items_status", table_name="content_items")
    op.drop_table("content_items")

    op.drop_table("news_sources")

    bind = op.get_bind()
    sa.Enum(name="publication_job_status").drop(bind, checkfirst=True)
    sa.Enum(name="publication_job_type").drop(bind, checkfirst=True)
    sa.Enum(name="publication_platform").drop(bind, checkfirst=True)
    sa.Enum(name="publication_batch_status").drop(bind, checkfirst=True)
    sa.Enum(name="publication_batch_type").drop(bind, checkfirst=True)
    sa.Enum(name="content_item_status").drop(bind, checkfirst=True)
    sa.Enum(name="news_source_sync_status").drop(bind, checkfirst=True)
    sa.Enum(name="news_source_type").drop(bind, checkfirst=True)
