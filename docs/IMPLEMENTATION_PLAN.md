# Implementation Plan (MVP)

## Этап 0. Уточнение требований (обязательный)
**Цель:** зафиксировать продуктовые и технические решения до кода.

### Что фиксируем
1. Список источников для MVP (минимум 1 RSS).
2. Модель адаптеров: `adapter != микросервис` в MVP (внутри parser worker).
3. Доменные зоны:
   - `Editorial Publisher` (текстовые важные посты в Telegram)
   - `Traffic Shorts Publisher` (видео-контент для охватных платформ)
4. Ограничения по размеру/формату видео.
5. Стиль AI-генерации (тон, длина, структура поста).
6. Telegram-канал(ы) публикации.
7. Список разрешенных пользователей (для начала один owner).

### Результат
- Подписанный `PROJECT_SPEC.md` + список open questions = 0.

---

## Этап 1. Инфраструктурный каркас
**Цель:** поднять среду разработки и базовые сервисы.

### Задачи
1. `docker-compose`: postgres, redis, backend, 3 workers, frontend.
2. Базовый FastAPI health endpoint.
3. Базовый Celery app + очереди parser/ai/publisher.
4. Подключение `.env`.

### Acceptance criteria
1. `docker compose up --build` стартует без критических ошибок.
2. `GET /health` возвращает `ok`.
3. Все worker-процессы поднимаются.

---

## Этап 2. Data layer + миграции
**Цель:** стабилизировать данные и историю операций.

### Задачи
1. SQLAlchemy модели:
   - `news_sources`
   - `parsed_items`
   - `draft_posts`
   - `media_assets`
   - `publication_jobs`
2. Alembic initial migration.
3. Индексы:
   - `parsed_items.content_hash`
   - `publication_jobs.status`
   - `parsed_items.status`
4. Retention для новостей:
   - автоудаление записей `parsed_items` старше 7 дней.
   - периодическая celery-задача очистки.

### Acceptance criteria
1. `alembic upgrade head` проходит.
2. Таблицы и индексы созданы.
3. CRUD smoke test проходит.
4. Очистка удаляет новости старше 7 дней по расписанию.

---

## Этап 3. Parser framework
**Цель:** запустить ingestion pipeline.

### Задачи
1. Общий parser interface (adapter contract).
2. RSS adapter (пример).
3. Celery task для запуска adapter-а.
4. Дедупликация по `content_hash`.
5. API endpoint для ручного trigger parser-а (для MVP удобно).

### Acceptance criteria
1. После запуска parser задачи в `parsed_items` появляются записи.
2. Повторный запуск не плодит дубликаты.

---

## Этап 4. Mini App backend API
**Цель:** обеспечить весь пользовательский поток для текстовых постов.

### Задачи
1. `GET /news`, `GET /news/{id}`.
2. `POST /news/{id}/generate-draft`.
3. `PATCH /drafts/{id}`.
4. `POST /publications/telegram/text`.
5. `GET /publications/history`.

### Acceptance criteria
1. Полный flow "новость -> draft -> publish" выполняется через API.
2. Статусы jobs корректно переходят `queued -> processing -> published/failed`.

---

## Этап 5. AI service (stub)
**Цель:** встроить управляемую генерацию черновика.

### Задачи
1. AI service abstraction.
2. Stub-реализация для MVP.
3. Celery ai task.
4. Логирование prompt/result метаданных (без секретов).

### Acceptance criteria
1. Для выбранной новости генерируется draft.
2. Ошибки AI не валят API, а отражаются в статусе.

---

## Этап 6. Telegram publisher
**Цель:** публикация текстовых постов в канал.

### Задачи
1. Сервис публикации через Telegram Bot API.
2. Publisher worker task.
3. Сохранение message_id и статуса публикации.
4. Обработка retry и rate-limit ошибок.

### Acceptance criteria
1. Пост реально появляется в канале.
2. В `publication_jobs` записан итог.

---

## Этап 7. Media upload + video publish (Telegram only)
**Цель:** базовая работа с видео.

### Задачи
1. Upload endpoint (multipart).
2. Валидация формата/размера.
3. Сохранение в local storage.
4. Создание video publication job.
5. Публикация видео в Telegram.

### Acceptance criteria
1. Валидное видео грузится и публикуется.
2. Невалидное отклоняется корректной ошибкой.

---

## Этап 8. Frontend Mini App (React + Vite)
**Цель:** закрыть UX основных операций.

### Экраны
1. `NewsList`
2. `NewsDetails`
3. `DraftEditor`
4. `MediaUpload`
5. `PublicationHistory`

### Acceptance criteria
1. Навигация между экранами работает.
2. Пользователь может пройти оба MVP-сценария end-to-end.

---

## Этап 9. Security hardening
**Цель:** закрыть базовые риски.

### Задачи
1. Валидация Telegram initData.
2. Проверка allowed owner user_id.
3. Проверка env-only secrets.
4. Санитизация логов и ответов.

### Acceptance criteria
1. Запросы без валидного initData отклоняются.
2. Чужой user_id не имеет доступа.

---

## Этап 10. Подготовка к расширению (VK / YouTube Shorts)
**Цель:** не блокировать следующий релиз.

### Задачи
1. Интерфейс platform publisher adapter.
2. Заглушки `VkPublisher`, `YoutubeShortsPublisher`.
3. Единый publication dispatcher.

### Acceptance criteria
1. Добавление новой платформы не требует переписывать существующий telegram publisher.

---

## Риски и решения
1. **Источник ломает разметку/лимиты**  
   Решение: adapter isolation + retries + health monitoring per source.
2. **Дубликаты с незначительными отличиями текста**  
   Решение: нормализация текста перед hash + fallback по URL.
3. **Rate limits Telegram API**  
   Решение: backoff retry + очередь publisher.
4. **Большие видео не проходят**  
   Решение: upfront validation + опциональный ffmpeg transcode pipeline.

---

## Open Questions (закрыть до старта кодинга)
1. Какие конкретно источники после RSS в приоритете?
2. Нужна ли модерация/approve шаг перед публикацией видео?
3. Какой целевой лимит длины AI-поста (символы)?
4. Нужны ли хэштеги и автоматические CTA?
5. Нужна ли многоканальная публикация в Telegram (несколько каналов)?
