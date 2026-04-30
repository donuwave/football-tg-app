# PROJECT SPEC: Football Telegram Content Tool (MVP)

## 1. Цель продукта
Сделать систему, где владелец футбольного Telegram-канала:
1. Автоматически получает ленту новостей из разных источников.
2. Генерирует по новости готовый Telegram-пост через AI.
3. Редактирует и публикует пост прямо из Telegram Mini App.
4. Загружает видео и публикует его (в MVP только в Telegram), с архитектурной готовностью к VK/YouTube Shorts.

## 2. Границы MVP
### Входит в MVP
- Сбор новостей минимум из 1 источника (RSS) через adapter pattern.
- Единый формат parsed item для всех parser adapters.
- Дедупликация новостей по `content_hash`.
- Telegram Mini App c 5 экранами:
  - `NewsList`
  - `NewsDetails`
  - `DraftEditor`
  - `MediaUpload`
  - `PublicationHistory`
- Генерация черновика поста через AI stub service.
- Публикация текста и видео в Telegram-канал через Telegram Bot API.
- Валидация Telegram `initData`.
- Ограничение доступа по `allowed_user_id`.

### Не входит в MVP (но учитывается архитектурно)
- Реальная интеграция VK.
- Реальная интеграция YouTube Shorts.
- Продвинутый AI-пайплайн с векторным поиском и фактчекингом.
- Сложный контент-планер/автопостинг по расписанию.

## 3. Технический стек
- Frontend: Telegram Mini App (`React + Vite`).
- Backend API: `FastAPI`.
- DB: `PostgreSQL`.
- Queue: `Redis + Celery`.
- Workers:
  - `parser worker`
  - `ai worker`
  - `publisher worker`
- Storage:
  - MVP: локальный файловый диск
  - abstraction layer для будущего S3
- Video processing:
  - `FFmpeg` для валидации/подготовки (если нужно транскодирование).

## 4. Архитектура (логическая)
1. **Parser Layer**
   - Каждый источник = отдельный adapter (модуль/класс), реализующий общий интерфейс.
   - В MVP adapter **не является микросервисом**: адаптеры живут внутри общего backend-контекста и исполняются parser worker-ом.
   - Каждый adapter запускается как отдельная celery-задача/инстанс.
2. **Ingestion Layer**
   - Нормализация в единый `ParsedItemDTO`.
   - Расчет `content_hash`.
   - Сохранение в `parsed_items`.
3. **Content Layer**
   - Выдача списка новостей в Mini App.
   - Генерация поста через AI service.
   - Ручная редактура пользователем.
4. **Publication Layer**
   - Создание jobs публикации.
   - Публикация в Telegram.
   - Логирование статусов и ошибок.
5. **Media Layer**
   - Upload видео.
   - Проверка формата/размера.
   - Сохранение в `media_assets`.

## 4.1 Доменные сервисы в продукте
В продукте выделяем 2 доменных сервиса, но технически в MVP это один backend и один Mini App:
1. **Editorial Publisher**
   - важные новости -> AI draft -> ручная редактура -> публикация в Telegram.
2. **Traffic Shorts Publisher**
   - видео + описание -> публикация в video-платформы.
   - В MVP фактическая публикация видео только в Telegram, при этом контракты под VK/YouTube Shorts закладываются сразу.

## 5. Основные сценарии (детализация)
### Сценарий A: Новости -> AI Draft -> Telegram Publish
1. Scheduler/ручной триггер запускает parser jobs.
2. Adapter парсит источник и возвращает normalized list.
3. Backend считает `content_hash`; если дубликат, запись помечается и не идет в активную ленту.
4. Пользователь видит список новостей в `NewsList`.
5. Пользователь открывает новость (`NewsDetails`) и нажимает "Сгенерировать пост".
6. Создается `ai_generation_job` и уходит в `ai` queue.
7. AI worker возвращает короткий пост на русском.
8. Пользователь редактирует текст (`DraftEditor`) и нажимает "Опубликовать".
9. Создается `publication_job` (target: telegram), уходит в `publisher` queue.
10. Publisher worker публикует в канал и сохраняет статус `published/failed`.

### Сценарий B: Upload Video -> Telegram Publish
1. Пользователь загружает видео в `MediaUpload`.
2. Backend валидирует:
   - MIME/type
   - extension
   - max size
3. Сохраняет metadata в `media_assets`, файл в storage.
4. Создает `publication_job` (video).
5. Publisher публикует видео в Telegram.
6. История видна в `PublicationHistory`.

## 6. Модель данных (черновой контракт)
### `news_sources`
- `id` (uuid)
- `name` (string, unique)
- `source_type` (enum: rss, twitter, website, ...)
- `base_url` (string)
- `is_active` (bool)
- `adapter_config` (jsonb)
- `created_at`, `updated_at`

### `parsed_items`
- `id` (uuid)
- `source_id` (fk -> news_sources)
- `external_id` (string, nullable)
- `url` (text)
- `title` (text)
- `raw_text` (text)
- `image_url` (text, nullable)
- `category` (string, nullable)
- `published_at` (timestamp, nullable)
- `content_hash` (string, indexed)
- `is_duplicate` (bool, default false)
- `status` (enum: new, ai_generated, published, archived)
- `created_at`, `updated_at`

Retention policy (MVP):
- История новостей не хранится долгосрочно.
- Записи в `parsed_items` автоматически удаляются через 7 дней после `created_at`.
- Реализуется периодической celery-задачей очистки (например, 1 раз в сутки).

### `draft_posts`
- `id` (uuid)
- `parsed_item_id` (fk -> parsed_items)
- `ai_text` (text)
- `edited_text` (text, nullable)
- `generation_status` (enum: pending, done, failed)
- `created_by_telegram_user_id` (bigint)
- `created_at`, `updated_at`

### `media_assets`
- `id` (uuid)
- `owner_telegram_user_id` (bigint)
- `media_type` (enum: image, video)
- `file_path` (text)
- `mime_type` (string)
- `size_bytes` (bigint)
- `duration_sec` (int, nullable)
- `title` (string, nullable)
- `description` (text, nullable)
- `created_at`

### `publication_jobs`
- `id` (uuid)
- `job_type` (enum: text_post, video_post)
- `platform` (enum: telegram, vk, youtube_shorts)
- `status` (enum: queued, processing, published, failed)
- `parsed_item_id` (fk, nullable)
- `draft_post_id` (fk, nullable)
- `media_asset_id` (fk, nullable)
- `platform_payload` (jsonb)
- `error_message` (text, nullable)
- `published_message_id` (string, nullable)
- `created_at`, `updated_at`

## 7. API контракт (MVP)
### Auth / Session
- `POST /api/v1/auth/telegram/verify`
  - input: `initData`
  - output: session token / success flag

### News
- `GET /api/v1/news`
  - filter: source, status, category, page
- `GET /api/v1/news/{id}`
- `POST /api/v1/news/{id}/generate-draft`
  - creates AI job
- `GET /api/v1/news/{id}/draft`

### Drafts
- `PATCH /api/v1/drafts/{id}`
  - update edited text

### Publications
- `POST /api/v1/publications/telegram/text`
- `POST /api/v1/publications/telegram/video`
- `GET /api/v1/publications/history`

### Media
- `POST /api/v1/media/upload` (multipart)
- `GET /api/v1/media/{id}`

## 8. Очереди и воркеры
### Queues
- `parser`
- `ai`
- `publisher`

### Worker responsibilities
- `parser worker`:
  - запускает adapters
  - пишет parsed items
  - дедуп по hash
- `ai worker`:
  - генерация черновика поста
  - обновление `draft_posts`
- `publisher worker`:
  - отправка в Telegram
  - логирование результата в `publication_jobs`

## 9. Parser Adapter контракт
Единый интерфейс:
1. `fetch()` -> list raw items
2. `normalize(raw_item)` -> unified schema
3. `run()` -> fetch + normalize + return list

Unified schema:
- `external_id`
- `url`
- `title`
- `raw_text`
- `image_url`
- `published_at`
- `category`

## 10. AI service (MVP stub)
Вход:
- title
- raw_text
- source
- optional tone/style params

Выход:
- short telegram post (RU)
- optional hashtags

MVP режим: deterministic/stub генерация.  
Следующий этап: отдельный AI микросервис с промпт-шаблонами и retry policy.

## 11. Безопасность
1. Mini App всегда отправляет `initData`.
2. Backend валидирует подпись `initData` через `TELEGRAM_WEBAPP_SECRET`.
3. Доступ только если `telegram_user_id == TELEGRAM_ALLOWED_USER_ID`.
4. Все секреты только через env.
5. Логи без утечки токенов.
6. Ограничения на upload:
   - whitelist форматов
   - max size
   - reject исполняемые файлы

## 12. Нефункциональные требования
- Идемпотентность parser/jobs.
- Retry policy у Celery задач.
- Таймауты на внешние источники.
- Базовый audit trail (кто/когда публиковал).
- Наблюдаемость:
  - structured logs
  - health endpoints

## 13. Дорожная карта этапов
Этапы подробно в `docs/IMPLEMENTATION_PLAN.md`.
