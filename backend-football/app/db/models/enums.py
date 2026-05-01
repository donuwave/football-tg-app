from enum import Enum


class NewsSourceType(str, Enum):
    RSS = "rss"
    X = "x"
    WEBSITE = "website"


class NewsSourceSyncStatus(str, Enum):
    NEVER_RUN = "never_run"
    OK = "ok"
    FAILED = "failed"


class ContentItemStatus(str, Enum):
    NEW = "new"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PublicationBatchType(str, Enum):
    NEWS_POST = "news_post"
    RUBRIC_POST = "rubric_post"


class PublicationBatchStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIALLY_FAILED = "partially_failed"
    FAILED = "failed"


class PublicationPlatform(str, Enum):
    TELEGRAM = "telegram"
    VK = "vk"
    YOUTUBE = "youtube"


class PublicationJobType(str, Enum):
    TEXT_POST = "text_post"
    VIDEO_POST = "video_post"
    MIXED_POST = "mixed_post"


class PublicationJobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"


def enum_values(enum_class: type[Enum]) -> list[str]:
    return [item.value for item in enum_class]
