# DEPLOYMENT: Football TG Content Tool

Документ описывает деплой MVP для одного владельца (single-owner) на одном VPS.

## 1. Целевая схема
- 1 сервер (VPS)
- 1 домен (например `tg-football.yourdomain.com`)
- HTTPS (обязательно)
- Docker Compose со сервисами:
  - `frontend` (React Mini App)
  - `backend` (FastAPI)
  - `postgres`
  - `redis`
  - `parser-worker`
  - `ai-worker`
  - `publisher-worker`

## 2. Требования
1. VPS: Ubuntu 22.04+ (или аналог), 2 CPU / 4 GB RAM минимум.
2. Docker + Docker Compose plugin.
3. Домен с A-record на IP VPS.
4. Telegram bot token и `allowed_user_id`.

## 3. Переменные окружения
Создай `.env` в корне проекта (рядом с `docker-compose.yml`) на базе `.env.example`.

Ключевые переменные:
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `REDIS_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHANNEL_ID`
- `TELEGRAM_WEBAPP_SECRET`
- `TELEGRAM_ALLOWED_USER_ID`
- `LOCAL_STORAGE_PATH`

## 4. Подготовка сервера
1. Обновить систему:
```bash
sudo apt update && sudo apt upgrade -y
```
2. Установить Docker:
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```
3. Перелогиниться, проверить:
```bash
docker --version
docker compose version
```

## 5. Деплой приложения
1. Склонировать репозиторий:
```bash
git clone <your_repo_url> football-tg-app
cd football-tg-app
```
2. Создать `.env`:
```bash
cp .env.example .env
```
3. Заполнить секреты и параметры.
4. Поднять сервисы:
```bash
docker compose up -d --build
```
5. Проверить статус:
```bash
docker compose ps
docker compose logs -f backend
```

## 6. HTTPS и reverse proxy
Для Telegram Mini App нужен HTTPS. Рекомендуемый вариант: Nginx + Certbot.

### Пример Nginx-конфига
- `frontend` отдавать как основной сайт.
- `backend` проксировать на `/api`.

Пример (схематично):
```nginx
server {
    server_name tg-football.yourdomain.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
        proxy_pass http://127.0.0.1:5173/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Далее выпустить сертификат:
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
sudo certbot --nginx -d tg-football.yourdomain.com
```

## 7. Настройка Telegram Mini App
1. Открыть BotFather.
2. Для бота задать кнопку/меню с `Web App URL`:
   - `https://tg-football.yourdomain.com`
3. В backend:
   - включить валидацию `initData`,
   - разрешить только `TELEGRAM_ALLOWED_USER_ID`.

## 8. Проверка после деплоя (checklist)
1. `https://tg-football.yourdomain.com` открывается с валидным SSL.
2. `GET /api/health` возвращает `ok`.
3. Mini App открывается из Telegram-кнопки.
4. Неавторизованный user_id получает отказ.
5. Parser worker пишет новости в БД.
6. Генерация draft работает.
7. Публикация текста в Telegram работает.
8. Upload видео и публикация в Telegram работает.

## 9. Обновление сервиса
```bash
git pull
docker compose up -d --build
docker compose logs -f backend
```

## 10. Бэкапы
Минимум для MVP:
1. Бэкап PostgreSQL (ежедневно):
```bash
docker exec -t <postgres_container> pg_dump -U <user> <db> > backup.sql
```
2. Бэкап папки storage (если важны видео/медиа):
```bash
tar -czf storage-backup.tar.gz storage/
```

## 11. Что можно упростить/усилить позже
- Перенести фронт-статику на Vercel/Netlify, backend оставить на VPS.
- Перейти с local storage на S3.
- Добавить мониторинг (Sentry + Grafana/Loki).
- Добавить CI/CD (GitHub Actions).

