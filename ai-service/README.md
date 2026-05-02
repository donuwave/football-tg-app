# ai-service

Папка под локальную модель и инструкцию её запуска. На текущем этапе backend сам ходит в локальный inference runtime. Отдельный HTTP-сервис внутри репозитория не нужен.

## Текущий режим

Поддержаны два режима:

1. `AI_SERVICE_MODE=stub`
- backend возвращает шаблонный пост;
- подходит для smoke test и UI-разработки.

2. `AI_SERVICE_MODE=ollama`
- backend ходит в локальный `Ollama` по `AI_OLLAMA_BASE_URL`;
- модель выбирается через `AI_OLLAMA_MODEL`;
- пользовательское задание передаётся из Mini App вместе с новостью.

## Быстрый запуск через Ollama

По официальной документации Ollama API по умолчанию поднимается на `http://localhost:11434/api`, а генерация текста идёт через `POST /api/generate`:
- https://docs.ollama.com/api/introduction
- https://docs.ollama.com/api/generate

Локально это можно поднять так:

```bash
ollama serve
ollama pull llama3.1:8b
```

Дальше в `.env`:

```env
AI_SERVICE_MODE=ollama
AI_OLLAMA_BASE_URL=http://host.docker.internal:11434
AI_OLLAMA_MODEL=llama3.1:8b
AI_REQUEST_TIMEOUT_SECONDS=90
```

`host.docker.internal` нужен потому, что backend у нас работает в Docker, а Ollama обычно крутится на хост-машине.

## Как это работает

1. backend получает новость и задание редактора;
2. backend собирает prompt из заголовка, excerpt, raw text, source и published_at;
3. backend вызывает `Ollama` или stub;
4. Mini App получает готовый текст поста и даёт его отредактировать перед публикацией.
