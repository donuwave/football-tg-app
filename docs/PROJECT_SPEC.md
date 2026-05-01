# PROJECT SPEC: Football TG Publishing Tool (MVP)

## 1. Цель продукта
Сделать систему для одного владельца футбольного Telegram-канала, где он:
1. Автоматически получает ленту новостей из большого числа источников.
2. Быстро превращает выбранную новость в Telegram-пост через AI-шаблон.
3. Публикует новость в Telegram прямо из Telegram Mini App.
4. Создаёт отдельную `Рубрику` с медиа и текстами для Telegram, VK и YouTube.

## 2. Границы MVP
### Входит в MVP
- Сбор новостей минимум из 1 RSS-источника с архитектурой под много источников и много типов.
- Автопарсинг источников каждые 2 часа.
- Единый формат нормализованной новости для всех adapters.
- Идемпотентность внутри одного источника:
  - primary: `(source_id, external_id)`
  - fallback: `(source_id, url)`
- Telegram Mini App с 4 основными состояниями:
  - `Home`
  - `NewsList`
  - `NewsDetails / Compose`
  - `RubricComposer`
- AI stub для шаблонной генерации текста по новости.
- Публикация новости в Telegram.
- `Рубрика` с 4 пользовательскими полями:
  - видео для Telegram,
  - текст для Telegram,
  - short-видео для VK и YouTube,
  - описание для VK и YouTube.
- Одна команда публикации, которая запускает отправку rubric-контента в:
  - Telegram,
  - VK,
  - YouTube.
- Валидация Telegram `initData` по официальной схеме Telegram Web Apps.
- Ограничение доступа по одному `allowed_user_id`.

### Не входит в MVP (но учитывается архитектурно)
- Многопользовательский доступ.
- Несколько Telegram-каналов с UI-настройкой.
- Кросс-источниковая дедупликация похожих новостей.
- Публичная история публикаций как отдельный экран Mini App.
- Продвинутый AI-пайплайн с фактчекингом, памятью и retrieval.
- TikTok и другие дополнительные video platforms.

## 3. Технический стек
- Frontend: Telegram Mini App (`React + Vite`).
- Backend API: `FastAPI`.
- DB: `PostgreSQL`.
- Queue: `Redis + Celery`.
- Scheduler: Celery Beat или эквивалент внутри backend-контекста.
- Workers:
  - `parser worker`
  - `ai worker`
  - `publisher worker`
- Video processing:
  - `FFmpeg` для валидации, обрезки и подготовки short-видео.
- Storage:
  - временная локальная рабочая директория для upload/process/publish,
  - без долговременного media catalog в MVP.

## 4. Архитектура (логическая)
1. **Source Registry**
   - Каждый источник хранится как отдельная запись в БД.
   - Источник описывает:
     - тип (`rss`, `x`, `website`, ...),
     - параметры подключения,
     - активность,
     - статус последнего запуска.
   - Один adapter обслуживает много источников своего типа.
2. **Parser Layer**
   - Adapter не является отдельным микросервисом.
   - Adapter живёт внутри backend-контекста и исполняется parser worker-ом.
   - Scheduler раз в 2 часа создаёт parser-задачи по всем активным источникам.
3. **Ingestion Layer**
   - Нормализация данных в единый `ContentItemDTO`.
   - Сохранение новостей в одну ленту `content_items`.
   - Кросс-источниковая дедупликация не выполняется.
4. **News Publishing Layer**
   - Backend отдаёт список новостей в Mini App.
   - По клику на новость AI worker генерирует шаблон поста.
   - Пользователь правит текст на клиенте и публикует его в Telegram.
   - Отдельная сущность draft-а в БД не создаётся.
5. **Rubric Publishing Layer**
   - Пользователь загружает 2 видео и вводит 2 текстовых поля.
   - Backend формирует publication batch.
   - Publisher worker создаёт platform jobs для Telegram, VK и YouTube.
6. **Temporary Media Layer**
   - Видео хранятся только во временной рабочей директории.
   - После публикации или ошибки временные файлы могут быть очищены cleanup-задачей.

## 4.1 Доменные зоны в продукте
В MVP продукт состоит из двух пользовательских зон:
1. **Новости**
   - лента новостей,
   - генерация текста поста,
   - публикация новости в Telegram.
2. **Рубрика**
   - ручная форма для публикации контента сразу в несколько платформ,
   - один short-видео файл для VK и YouTube,
   - единая кнопка `Опубликовать`.

## 5. Основные сценарии
### Сценарий A: Новость -> AI text -> Telegram publish
1. Scheduler раз в 2 часа запускает parser jobs по активным источникам.
2. Adapter получает данные источника и возвращает нормализованный список.
3. Backend сохраняет новые записи в `content_items` без кросс-источниковой дедупликации.
4. Пользователь открывает Mini App и видит общую новостную ленту.
5. Пользователь открывает новость и нажимает `Сгенерировать текст`.
6. Создаётся `ai_generation_job` и уходит в очередь `ai`.
7. AI worker возвращает шаблонный Telegram-текст на русском.
8. Пользователь редактирует текст на фронтенде.
9. Пользователь нажимает `Опубликовать`.
10. Создаётся publication batch с одной job на платформу `telegram`.
11. Publisher worker публикует пост и сохраняет статус.

### Сценарий B: Рубрика -> Telegram + VK + YouTube publish
1. Пользователь открывает экран `Рубрика`.
2. Загружает:
   - видео для Telegram,
   - short-видео для VK и YouTube.
3. Заполняет:
   - текст для Telegram,
   - описание для VK и YouTube.
4. Backend валидирует:
   - MIME/type,
   - extension,
   - max size,
   - video duration/codec при необходимости.
5. Backend сохраняет файлы во временную рабочую директорию.
6. Создаётся publication batch типа `rubric_post`.
7. Publisher worker создаёт 3 platform jobs:
   - `telegram`,
   - `vk`,
   - `youtube`.
8. Telegram получает Telegram-видео и Telegram-текст.
9. VK и YouTube получают один и тот же short-видео файл и общее описание.
10. Клиент получает итоговый статус `completed / partially_failed / failed`.

## 6. Модель данных (черновой контракт)
### `news_sources`
- `id` (uuid)
- `name` (string, unique)
- `source_type` (enum: rss, x, website, ...)
- `base_url` (string, nullable)
- `external_ref` (string, nullable) — например username, feed url или идентификатор канала
- `is_active` (bool)
- `adapter_config` (jsonb)
- `last_synced_at` (timestamp, nullable)
- `last_sync_status` (enum: never_run, ok, failed)
- `last_error_message` (text, nullable)
- `created_at`, `updated_at`

### `content_items`
- `id` (uuid)
- `source_id` (fk -> news_sources)
- `external_id` (string, nullable)
- `url` (text, nullable)
- `title` (text)
- `raw_text` (text)
- `excerpt` (text, nullable)
- `image_url` (text, nullable)
- `author_name` (string, nullable)
- `published_at` (timestamp, nullable)
- `status` (enum: new, published, archived)
- `source_payload` (jsonb, nullable)
- `created_at`, `updated_at`

Правила уникальности:
- уникальность внутри источника по `(source_id, external_id)`, если `external_id` присутствует;
- fallback-уникальность по `(source_id, url)`, если `external_id` отсутствует.

Retention policy (MVP):
- Новости не хранятся бесконечно.
- Записи в `content_items` автоматически удаляются через 7 дней после `created_at`.
- Очистка выполняется периодической задачей.

### `publication_batches`
- `id` (uuid)
- `batch_type` (enum: news_post, rubric_post)
- `status` (enum: queued, processing, completed, partially_failed, failed)
- `created_by_telegram_user_id` (bigint)
- `source_item_id` (fk -> content_items, nullable)
- `request_payload` (jsonb)
- `result_summary` (jsonb, nullable)
- `created_at`, `updated_at`

### `publication_jobs`
- `id` (uuid)
- `batch_id` (fk -> publication_batches)
- `platform` (enum: telegram, vk, youtube)
- `job_type` (enum: text_post, video_post, mixed_post)
- `status` (enum: queued, processing, published, failed)
- `platform_payload` (jsonb)
- `external_publication_id` (string, nullable)
- `error_message` (text, nullable)
- `created_at`, `updated_at`

## 7. API контракт (MVP)
Все пользовательские endpoints работают под префиксом `/api/v1`.

### System
- `GET /api/v1/health`

### Auth / Session
- `POST /api/v1/auth/telegram/verify`
  - input: `initData`
  - output: `success`, `telegram_user_id`

### News
- `GET /api/v1/news`
  - filters: `source_id`, `page`, `page_size`
- `GET /api/v1/news/{id}`
- `POST /api/v1/news/{id}/generate-post`
  - creates AI job and returns generated text
- `POST /api/v1/news/{id}/publish`
  - input: final text chosen by user
  - creates `publication_batch` for Telegram

### Rubric
- `POST /api/v1/rubric/publish`
  - multipart payload:
    - `telegram_video`
    - `telegram_text`
    - `short_video`
    - `short_caption`
  - creates `publication_batch` with jobs for Telegram, VK and YouTube

### Publication Status
- `GET /api/v1/publications/{batch_id}`
  - returns aggregate batch status and per-platform statuses

## 8. Очереди и воркеры
### Queues
- `parser`
- `ai`
- `publisher`

### Worker responsibilities
- `parser worker`:
  - запускает adapters по `source_id`
  - пишет записи в `content_items`
  - обеспечивает идемпотентность внутри источника
- `ai worker`:
  - генерирует шаблонный текст поста по новости
- `publisher worker`:
  - публикует news batches и rubric batches
  - пишет статусы в `publication_batches` и `publication_jobs`

### Scheduler
- Период запуска parser-задач: каждые 2 часа.
- Scheduler проходит по всем активным источникам и ставит задачи в очередь `parser`.

## 9. Parser Adapter контракт
Единый интерфейс:
1. `fetch(source_config)` -> list raw items
2. `normalize(raw_item)` -> unified schema
3. `run(source)` -> fetch + normalize + persist-ready list

Unified schema:
- `external_id`
- `url`
- `title`
- `raw_text`
- `excerpt`
- `image_url`
- `author_name`
- `published_at`
- `source_payload`

## 10. AI service (MVP stub)
### Роль в MVP
- Генерирует короткий шаблонный текст для Telegram по новости.
- Не хранит результат как отдельный draft в БД.

### Вход
- `title`
- `raw_text`
- `source_name`
- optional `tone/style params`

### Выход
- short telegram post (RU)
- optional hashtags

### Технический режим
- MVP = deterministic/stub генерация.
- Папка `ai-service/` хранит локальную модель и инструкцию запуска.
- Все оркестрационные вызовы к модели выполняет основной backend.

## 11. Безопасность
1. Mini App всегда отправляет `initData`.
2. Backend валидирует `initData` по официальной схеме Telegram Web Apps на основе bot token.
3. Доступ разрешён только если `telegram_user_id == TELEGRAM_ALLOWED_USER_ID`.
4. `TELEGRAM_CHANNEL_ID` задаётся только через env.
5. Все секреты платформ хранятся только в env.
6. Логи не должны содержать токены, refresh tokens и содержимое `initData`.
7. Ограничения на upload:
   - whitelist форматов,
   - max size,
   - reject исполняемые файлы.

## 12. Нефункциональные требования
- Идемпотентность parser/jobs.
- Retry policy у Celery задач.
- Таймауты на внешние источники.
- Structured logs.
- Health endpoint.
- Очистка временных файлов после публикации.
- Базовый audit trail публикаций на уровне batch/job.

## 13. Дорожная карта этапов
Этапы подробно описаны в `docs/IMPLEMENTATION_PLAN.md`.
