# Football TG Content Tool (MVP)

Инструмент для подготовки и публикации контента в футбольный Telegram-канал через Telegram Mini App.

## Stack
- Frontend: React + Vite (Telegram Mini App)
- Backend: FastAPI
- DB: PostgreSQL
- Queue: Redis + Celery
- Workers: parser / ai / publisher
- Storage: local (MVP), абстракция под S3
- Video processing: FFmpeg (подготовлено на уровне архитектуры)

## Структура
- `app-football/` — frontend Mini App
- `backend-football/` — FastAPI + Celery + Alembic
- `parsers-football/` — место для отдельных parser-инстансов/конфигов
- `docs/` — документация и этапы работ

## Быстрый старт (Docker)
1. Скопируйте `.env.example` в `.env` и заполните значения.
2. Запустите:
   - `docker compose up --build`
3. Сервисы:
   - API: `http://localhost:8000`
   - Frontend: `http://localhost:5173`
   - Postgres: `localhost:5432`
   - Redis: `localhost:6379`

Подробности по этапам: `docs/IMPLEMENTATION_PLAN.md`.

