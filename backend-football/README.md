# backend-football

Основной backend приложения.

## Ответственность
- `FastAPI` API под `/api/v1`
- валидация Telegram Mini App `initData`
- registry источников новостей
- scheduler парсинга раз в 2 часа
- AI stub orchestration
- multi-platform публикация:
  - Telegram
  - VK
  - YouTube

## Планируемые очереди
- `parser`
- `ai`
- `publisher`

## Основные домены
- `news_sources`
- `content_items`
- `publication_batches`
- `publication_jobs`
