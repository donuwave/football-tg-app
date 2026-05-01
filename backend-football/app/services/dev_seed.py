from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.content_item import ContentItem
from app.db.models.enums import ContentItemStatus, NewsSourceSyncStatus, NewsSourceType
from app.db.models.news_source import NewsSource


def seed_dev_news_feed(session: Session) -> None:
    existing_item = session.scalar(select(ContentItem.id).limit(1))
    if existing_item is not None:
        return

    now = datetime.now(tz=UTC)

    sources = [
        NewsSource(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            name="BBC Sport RSS",
            source_type=NewsSourceType.RSS,
            external_ref="bbc-football",
            base_url="https://www.bbc.com/sport/football",
            is_active=True,
            adapter_config={"feed_url": "https://feeds.bbci.co.uk/sport/football/rss.xml"},
            last_synced_at=now - timedelta(minutes=7),
            last_sync_status=NewsSourceSyncStatus.OK,
        ),
        NewsSource(
            id=UUID("22222222-2222-2222-2222-222222222222"),
            name="Sky Sports RSS",
            source_type=NewsSourceType.RSS,
            external_ref="sky-football",
            base_url="https://www.skysports.com/football",
            is_active=True,
            adapter_config={"feed_url": "https://www.skysports.com/rss/12040"},
            last_synced_at=now - timedelta(minutes=10),
            last_sync_status=NewsSourceSyncStatus.OK,
        ),
        NewsSource(
            id=UUID("33333333-3333-3333-3333-333333333333"),
            name="Fabrizio Romano",
            source_type=NewsSourceType.X,
            external_ref="@FabrizioRomano",
            base_url="https://x.com/FabrizioRomano",
            is_active=True,
            adapter_config={"account_handle": "FabrizioRomano"},
            last_synced_at=now - timedelta(minutes=24),
            last_sync_status=NewsSourceSyncStatus.OK,
        ),
        NewsSource(
            id=UUID("44444444-4444-4444-4444-444444444444"),
            name="The Athletic",
            source_type=NewsSourceType.WEBSITE,
            external_ref="transfer-desk",
            base_url="https://www.nytimes.com/athletic",
            is_active=True,
            adapter_config={"section": "transfer-desk"},
            last_synced_at=now - timedelta(minutes=38),
            last_sync_status=NewsSourceSyncStatus.OK,
        ),
    ]

    items = [
        ContentItem(
            id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"),
            source_id=sources[2].id,
            external_id="x-fabrizio-001",
            url="https://x.com/FabrizioRomano/status/1",
            title="Романо: клубы АПЛ ускорили переговоры по молодому вингеру",
            excerpt="Сразу два клуба вышли в финальную фазу переговоров и хотят закрыть трансфер до открытия окна.",
            raw_text="По данным источника, два клуба из верхней части таблицы АПЛ ускорили переговоры по молодому вингеру. Стороны обсуждают структуру платежей, бонусы и процент от будущей продажи. Игрок уже дал понять, что готов к переходу, если клубы договорятся до старта предсезонки.",
            published_at=now - timedelta(minutes=18),
            status=ContentItemStatus.NEW,
            source_payload={"image_hint": "transfer-window"},
        ),
        ContentItem(
            id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2"),
            source_id=sources[0].id,
            external_id="rss-bbc-001",
            url="https://www.bbc.com/sport/football/example-1",
            title="Тренер подтвердил, что лидер полузащиты пропустит следующий тур",
            excerpt="Игрок получил мышечное повреждение и вернётся только после дополнительного обследования.",
            raw_text="Главный тренер команды подтвердил, что лидер полузащиты пропустит следующий тур из-за мышечного повреждения. Клуб не хочет форсировать восстановление и ждёт результаты дополнительного обследования. Сроки возвращения станут известны в ближайшие дни.",
            published_at=now - timedelta(hours=1, minutes=5),
            status=ContentItemStatus.NEW,
            source_payload={"image_hint": "injury-update"},
        ),
        ContentItem(
            id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"),
            source_id=sources[1].id,
            external_id="rss-sky-001",
            url="https://www.skysports.com/football/example-1",
            title="Клуб Серии А начал поиск замены основному форварду",
            excerpt="Руководство уже общается с агентами трёх кандидатов и хочет ускорить работу по летнему рынку.",
            raw_text="После вероятного ухода основного форварда клуб Серии А начал поиск замены. В шорт-листе три кандидата из чемпионатов Италии, Франции и Нидерландов. Спортивный директор хочет ускорить переговоры до начала международных турниров.",
            published_at=now - timedelta(hours=1, minutes=39),
            status=ContentItemStatus.NEW,
            source_payload={"image_hint": "serie-a"},
        ),
        ContentItem(
            id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa4"),
            source_id=sources[3].id,
            external_id="site-athletic-001",
            url="https://www.nytimes.com/athletic/example-1",
            title="Новый спортивный директор пересматривает список летних целей",
            excerpt="После смены руководства клуб обновляет профиль трансферных целей и сокращает число дорогих опций.",
            raw_text="Новый спортивный директор пересматривает стратегию летнего окна и сокращает пул дорогих опций. Приоритет смещается в сторону игроков до 24 лет с высокой перепродажной стоимостью. Несколько переговоров поставлены на паузу до повторной оценки.",
            published_at=now - timedelta(hours=2, minutes=42),
            status=ContentItemStatus.NEW,
            source_payload={"image_hint": "sporting-director"},
        ),
    ]

    session.add_all([*sources, *items])
    session.commit()

