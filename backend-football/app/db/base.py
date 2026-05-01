from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.db.models.content_item import ContentItem  # noqa: E402,F401
from app.db.models.news_source import NewsSource  # noqa: E402,F401
from app.db.models.publication_batch import PublicationBatch  # noqa: E402,F401
from app.db.models.publication_job import PublicationJob  # noqa: E402,F401
