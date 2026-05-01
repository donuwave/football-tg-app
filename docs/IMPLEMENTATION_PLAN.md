# Implementation Plan (MVP)

## Этап 0. Уточнение требований
**Цель:** зафиксировать продуктовые и технические решения до начала кода.

### Что уже зафиксировано
1. Базовый API префикс: `/api/v1`.
2. Один владелец и один Telegram-канал.
3. Telegram `initData` валидируется по официальной схеме.
4. Новости и `Рубрика` — две основные зоны продукта.
5. `События` как отдельная сущность исключены.
6. Кросс-источниковой дедупликации нет.
7. Идемпотентность внутри источника обязательна.
8. Парсинг работает автоматически каждые 2 часа.
9. `Рубрика` публикует в Telegram, VK и YouTube.
10. AI на первом этапе шаблонный.

### Осталось уточнить перед кодом
1. Первый конкретный RSS-источник для smoke-теста.
2. Лимиты размеров и длительности для Telegram-видео и short-видео.
3. Минимальный набор VK/YouTube credential flow для локальной разработки.

### Результат
- `PROJECT_SPEC.md` согласован и не противоречит реализации.

---

## Этап 1. Frontend shell на моках
**Цель:** быстро собрать Telegram Mini App каркас и UX без зависимости от backend.

### Задачи
1. Инициализировать `app-football` на `React + Vite`.
2. Собрать базовую навигацию Mini App.
3. Сделать главную страницу с 2 плитками:
   - `Новости`
   - `Рубрика`
4. Сделать экран новостей:
   - список,
   - карточка новости,
   - compose-область для текста.
5. Сделать экран `Рубрика`:
   - 2 video inputs,
   - 2 text inputs,
   - 1 action button `Опубликовать`.
6. Использовать моковые данные и моковые статусы публикации.

### Acceptance criteria
1. Mini App shell запускается локально.
2. Пользователь может пройти оба UX-флоу без backend.
3. Структура frontend готова к подключению API.

---

## Этап 2. Backend skeleton
**Цель:** поднять базовый backend-каркас и инфраструктуру приложения.

### Задачи
1. Инициализировать `backend-football` на `FastAPI`.
2. Подключить `.env`.
3. Поднять базовый `GET /api/v1/health`.
4. Подключить Celery app и очереди:
   - `parser`
   - `ai`
   - `publisher`
5. Подготовить базовый scheduler-контур под запуск задач раз в 2 часа.

### Acceptance criteria
1. Backend стартует локально.
2. `GET /api/v1/health` возвращает `ok`.
3. Все worker-процессы поднимаются.

---

## Этап 3. Data layer + миграции
**Цель:** зафиксировать основную модель данных.

### Задачи
1. SQLAlchemy модели:
   - `news_sources`
   - `content_items`
   - `publication_batches`
   - `publication_jobs`
2. Alembic initial migration.
3. Индексы и ограничения:
   - `(source_id, external_id)` unique when present
   - `(source_id, url)` fallback unique when needed
   - `publication_batches.status`
   - `publication_jobs.status`
4. Retention для новостей:
   - автоудаление `content_items` старше 7 дней
   - периодическая cleanup-задача

### Acceptance criteria
1. `alembic upgrade head` проходит.
2. Таблицы и индексы созданы.
3. CRUD smoke test проходит.
4. Очистка старых новостей выполняется по расписанию.

---

## Этап 4. Parser framework
**Цель:** запустить ingestion pipeline под рост числа источников.

### Задачи
1. Общий parser interface.
2. Реестр adapters по `source_type`.
3. RSS adapter как первый рабочий adapter.
4. Celery task для обработки одного `source_id`.
5. Scheduler раз в 2 часа ставит задачи по всем активным источникам.
6. Идемпотентность внутри источника.

### Acceptance criteria
1. После запуска parser-задач в `content_items` появляются записи.
2. Повторный запуск одного источника не плодит копии.
3. Один adapter может обслужить несколько sources одного типа.

---

## Этап 5. News API + AI stub
**Цель:** закрыть backend flow для новости.

### Задачи
1. `GET /api/v1/news`
2. `GET /api/v1/news/{id}`
3. `POST /api/v1/news/{id}/generate-post`
4. `POST /api/v1/news/{id}/publish`
5. AI service abstraction.
6. Stub-реализация шаблонной генерации.
7. Celery task для AI-генерации.

### Acceptance criteria
1. Пользователь может получить список новостей.
2. Для выбранной новости генерируется текст.
3. Пользователь может отправить финальный текст на публикацию в Telegram.

---

## Этап 6. Telegram publisher для новостей
**Цель:** сделать реальную публикацию новостного поста.

### Задачи
1. Сервис публикации в Telegram Bot API.
2. Publisher worker flow для `news_post`.
3. Сохранение platform result в `publication_jobs`.
4. Обработка retry и rate-limit ошибок.

### Acceptance criteria
1. Новостной пост реально появляется в Telegram.
2. Batch и job получают итоговые статусы.

---

## Этап 7. Rubric pipeline
**Цель:** реализовать ручную multi-platform публикацию.

### Задачи
1. `POST /api/v1/rubric/publish` (multipart).
2. Валидация 2 загружаемых видео.
3. Временное сохранение файлов в рабочую директорию.
4. FFmpeg-подготовка short-видео при необходимости.
5. Publisher flow для:
   - Telegram,
   - VK,
   - YouTube.
6. Aggregation статусов в `publication_batches`.

### Acceptance criteria
1. Валидная rubric-форма уходит одной командой на все 3 платформы.
2. Ошибки одной платформы не скрывают статусы остальных.
3. Клиент может получить итоговый статус batch-а.

---

## Этап 8. Интеграция frontend <-> backend
**Цель:** заменить моки на реальные API-вызовы.

### Задачи
1. Подключить frontend к `auth/telegram/verify`.
2. Подключить список новостей и детали.
3. Подключить AI compose flow.
4. Подключить news publish flow.
5. Подключить rubric publish flow.
6. Сделать UI ожидания и ошибок для batch status.

### Acceptance criteria
1. Frontend проходит оба MVP-сценария через реальный backend.
2. Пользователь видит статусы публикации без отдельного экрана истории.

---

## Этап 9. Security hardening
**Цель:** закрыть базовые риски доступа и утечек.

### Задачи
1. Валидация Telegram `initData`.
2. Проверка `TELEGRAM_ALLOWED_USER_ID`.
3. Проверка env-only secrets.
4. Санитизация логов и ошибок.
5. Ограничения upload форматов и размеров.

### Acceptance criteria
1. Запросы без валидного `initData` отклоняются.
2. Чужой user id не получает доступ.
3. Секреты не попадают в ответы и логи.

---

## Этап 10. Локальный запуск и деплой-контур
**Цель:** подготовить кодовую базу к запуску локально и к первому VPS-деплою.

### Задачи
1. Собрать рабочий `docker-compose` под backend, workers, postgres, redis и frontend.
2. Подготовить инструкции по локальному запуску.
3. Подготовить env шаблон под Telegram, VK и YouTube.
4. Зафиксировать требования по HTTPS для Mini App.

### Acceptance criteria
1. Проект поднимается локально единым сценарием.
2. Документация по деплою не противоречит реальной конфигурации.

---

## Риски и решения
1. **Много источников одного типа**  
   Решение: registry of sources + adapters per type + job per source.
2. **Один и тот же source приходит повторно каждые 2 часа**  
   Решение: уникальность по `(source_id, external_id)` и fallback по URL.
3. **Rate limits Telegram / VK / YouTube**  
   Решение: publisher queue + retries + per-platform error handling.
4. **Видео не подходит по формату**  
   Решение: upfront validation + FFmpeg preprocessing.
5. **Частичный фейл rubric publish**  
   Решение: `publication_batches` со статусом `partially_failed` и per-platform jobs.

---

## Open Questions
1. Какой первый RSS URL используем для стартового adapter-а?
2. Какие минимальные ограничения задаём на размер и длительность Telegram-видео?
3. Нужны ли автохэштеги в AI-генерации новости?
