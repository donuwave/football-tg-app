# Football TG Publishing Tool (MVP)

Инструмент для одного владельца футбольного Telegram-канала с Telegram Mini App интерфейсом.

## Что входит в MVP
### 1. Новости
- Автосбор новостей по расписанию раз в 2 часа.
- Единая новостная лента в Mini App.
- AI-шаблон для быстрого превращения новости в текст поста.
- Публикация выбранной новости в Telegram-канал.

### 2. Рубрика
- Отдельная форма ручной публикации.
- 4 поля:
  - видео для Telegram,
  - текст поста для Telegram,
  - short-видео для VK и YouTube,
  - описание для VK и YouTube.
- Одна кнопка `Опубликовать`, которая запускает публикацию сразу в Telegram, VK и YouTube.

## Архитектурные решения
- Один владелец (`TELEGRAM_ALLOWED_USER_ID`).
- Один Telegram-канал (`TELEGRAM_CHANNEL_ID`).
- Валидация Telegram Mini App `initData` по официальной схеме Telegram.
- Источники разных типов (`rss`, `x`, `website`, ...) описываются как отдельные записи в БД.
- Один adapter обслуживает много источников одного типа.
- Кросс-источниковой дедупликации в MVP нет.
- Идемпотентность сохраняется внутри одного источника.
- Видео не хранится как долговременный медиакаталог: используется временная рабочая директория для upload/processing/publish pipeline.

## Текущий статус репозитория
Репозиторий уже перешёл из стадии согласования в стадию рабочей реализации. Базовый runnable-контур собран локально.

### Уже реализовано
- `app-football/`:
  - Telegram Mini App shell на `React + Vite`,
  - Telegram WebApp auth flow,
  - главный экран,
  - экран `Новости`,
  - owner UI для RSS-источников,
  - поле задания для AI rewrite в карточке новости.
- `backend-football/`:
  - `FastAPI` backend с `/api/v1`,
  - PostgreSQL + Redis в `docker compose`,
  - официальная валидация Telegram `initData`,
  - ограничение доступа по одному `TELEGRAM_ALLOWED_USER_ID`,
  - `GET /api/v1/health`,
  - `GET /api/v1/news`,
  - `GET /api/v1/news/{id}`,
  - `POST /api/v1/news/{id}/generate-post`,
  - `POST /api/v1/news/{id}/publish`,
  - `GET /api/v1/sources`,
  - `POST /api/v1/sources`,
  - `PATCH /api/v1/sources/{id}`,
  - `POST /api/v1/sources/{id}/sync`,
  - RSS adapter,
  - Celery Beat scheduler раз в 2 часа,
  - AI rewrite service:
    - `stub` по умолчанию,
    - `ollama` как локальный runtime режим.

### Важное текущее ограничение
- Автосид тестовых новостей убран.
- Лента пустая, пока ты не добавишь реальные RSS-источники через UI или API.
- Реальную публикацию новости в твой Telegram-канал я намеренно не дёргал автоматически.
- `Рубрика` ещё не подключена к backend.

## Что осталось до MVP
1. Довести до боевого состояния news publish flow:
   - smoke test реальной публикации в Telegram,
   - обработка retry / platform errors.
2. Если нужен не `stub`, а реальная локальная генерация:
   - поднять `Ollama`,
   - переключить `AI_SERVICE_MODE=ollama`,
   - подобрать модель и системный prompt.
3. Реализовать retention / cleanup:
   - удаление старых `content_items`,
   - cleanup временных файлов.
4. Реализовать backend для `Рубрики`:
   - multipart upload,
   - временное хранение файлов,
   - pipeline публикации в Telegram, VK и YouTube.
5. Подключить экран `Рубрика` к реальному backend.
6. Добавить batch status endpoint для multi-platform публикаций.
7. Завершить локальный-to-prod деплой-контур backend с публичным HTTPS URL.

## Структура
- `app-football/` — frontend Telegram Mini App
- `backend-football/` — backend API, scheduler, workers
- `ai-service/` — локальная модель и инструкция по запуску
- `docs/` — спецификация, этапы реализации и деплой

## Документация
- [PROJECT_SPEC](./docs/PROJECT_SPEC.md) — продуктовая и техническая спецификация MVP
- [IMPLEMENTATION_PLAN](./docs/IMPLEMENTATION_PLAN.md) — этапы реализации
- [DEPLOYMENT](./docs/DEPLOYMENT.md) — целевая схема деплоя после появления кода
