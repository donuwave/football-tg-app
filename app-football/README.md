# app-football

Frontend Telegram Mini App.

## Цель
Дать владельцу канала два рабочих сценария:
1. открыть ленту новостей, сгенерировать текст и опубликовать новость в Telegram;
2. открыть `Рубрику`, загрузить 2 видео, заполнить 2 текста и одной кнопкой отправить публикацию в Telegram, VK и YouTube.

## Планируемые разделы UI
- `Home`
- `NewsList`
- `NewsDetails / Compose`
- `RubricComposer`

## Ближайший этап
Сначала frontend собирается на моках, затем подключается к backend API `/api/v1`.

## Runtime env
- `VITE_API_BASE_URL` — публичный URL backend API
- `VITE_ENABLE_DEV_AUTH_BYPASS=true` — опциональный локальный bypass, чтобы не блокировать разработку вне Telegram
