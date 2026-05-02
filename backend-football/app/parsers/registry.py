from app.db.models.enums import NewsSourceType
from app.parsers.base import SourceAdapter
from app.parsers.rss import RssAdapter


class UnsupportedSourceTypeError(ValueError):
    def __init__(self, source_type: NewsSourceType):
        super().__init__(f"Source type '{source_type.value}' is not supported yet.")


_RSS_ADAPTER = RssAdapter()


def get_adapter(source_type: NewsSourceType) -> SourceAdapter:
    if source_type is NewsSourceType.RSS:
        return _RSS_ADAPTER

    raise UnsupportedSourceTypeError(source_type)
