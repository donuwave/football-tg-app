# DEPLOYMENT: Football TG Publishing Tool

Документ описывает целевую схему деплоя MVP после появления кода. Модель остаётся single-owner: один владелец, один Telegram-канал, один VPS.

## 1. Целевая схема
- 1 сервер (VPS)
- 1 домен, например `tg-football.yourdomain.com`
- HTTPS обязателен для Telegram Mini App
- Docker Compose со сервисами:
  - `frontend` (React Mini App)
  - `backend` (FastAPI)
  - `postgres`
  - `redis`
  - `parser-worker`
  - `ai-worker`
  - `publisher-worker`

Дополнительно:
- `FFmpeg` должен быть доступен внутри backend/publisher runtime для обработки short-видео.

## 2. Требования
1. VPS: Ubuntu 22.04+ (или аналог), 2 CPU / 4 GB RAM минимум.
2. Docker + Docker Compose plugin.
3. Домен с A-record на IP VPS.
4. Telegram bot token и `TELEGRAM_ALLOWED_USER_ID`.
5. Рабочие credentials для:
   - VK,
   - YouTube.

## 3. Переменные окружения
Создай `.env` в корне проекта на базе `.env.example`.

Ключевые переменные:
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `REDIS_URL`
- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHANNEL_ID`
- `TELEGRAM_ALLOWED_USER_ID`
- `VK_ACCESS_TOKEN`
- `VK_GROUP_ID`
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`
- `YOUTUBE_CHANNEL_ID`
- `LOCAL_STORAGE_PATH`
- `PARSER_INTERVAL_MINUTES`

Примечания:
- `LOCAL_STORAGE_PATH` используется как временная рабочая директория, а не как долговременное media storage.
- Telegram `initData` валидируется по официальной схеме на основе bot token, отдельный `WEBAPP_SECRET` не нужен.

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
3. Заполнить секреты и параметры платформ.
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
Для Telegram Mini App нужен HTTPS. Базовый вариант: Nginx + Certbot.

### Пример Nginx-конфига
- `frontend` отдаётся как основной сайт.
- `backend` проксируется под `/api`.

Схематично:
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

Выпуск сертификата:
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
sudo certbot --nginx -d tg-football.yourdomain.com
```

## 7. Настройка Telegram Mini App
1. Открыть BotFather.
2. Для бота задать кнопку или menu button с `Web App URL`:
   - `https://tg-football.yourdomain.com`
3. В backend:
   - включить официальную валидацию `initData`,
   - разрешить только `TELEGRAM_ALLOWED_USER_ID`,
   - использовать один фиксированный `TELEGRAM_CHANNEL_ID`.

## 8. Проверка после деплоя (checklist)
1. `https://tg-football.yourdomain.com` открывается с валидным SSL.
2. `GET /api/v1/health` возвращает `ok`.
3. Mini App открывается из Telegram-кнопки.
4. Неавторизованный user id получает отказ.
5. Scheduler раз в 2 часа ставит parser tasks.
6. Parser worker пишет новости в БД.
7. Генерация news-текста работает.
8. Публикация новости в Telegram работает.
9. `Рубрика` публикуется в Telegram, VK и YouTube.
10. Временные файлы после rubric publish корректно очищаются или помечаются на cleanup.

## 9. Обновление сервиса
```bash
git pull
docker compose up -d --build
docker compose logs -f backend
```

## 10. Бэкапы
Минимум для MVP:
1. Бэкап PostgreSQL:
```bash
docker exec -t <postgres_container> pg_dump -U <user> <db> > backup.sql
```
2. Бэкап временной директории не обязателен, так как она не является постоянным хранилищем.

## 11. Что можно усилить позже
- Вынести фронтенд-статику на отдельный hosting.
- Перейти с локальной временной директории на object storage для pipeline.
- Добавить TikTok publisher.
- Добавить мониторинг и трассировку задач.
- Добавить CI/CD.
