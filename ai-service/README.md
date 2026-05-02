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

Для русского текста я перевёл дефолтную конфигурацию на `qwen2.5`. На официальной странице Ollama указано, что `Qwen2.5` поддерживает более 29 языков, включая русский:
- https://ollama.com/library/qwen2.5

Локально это можно поднять так:

```bash
ollama serve
ollama pull qwen2.5:3b
```

Дальше в `.env`:

```env
AI_SERVICE_MODE=ollama
AI_OLLAMA_BASE_URL=http://host.docker.internal:11434
AI_OLLAMA_MODEL=qwen2.5:3b
AI_REQUEST_TIMEOUT_SECONDS=90
AI_OLLAMA_KEEP_ALIVE=10m
AI_OLLAMA_TEMPERATURE=0.35
AI_OLLAMA_TOP_P=0.9
```

Если качество покажется слабым, следующий шаг без переделки кода — просто переключить `AI_OLLAMA_MODEL` на `qwen2.5:7b`.

`host.docker.internal` нужен потому, что backend у нас работает в Docker, а Ollama обычно крутится на хост-машине.

## Как это работает

1. backend получает новость и задание редактора;
2. backend собирает prompt из заголовка, excerpt, raw text, source и published_at;
3. backend вызывает `Ollama` или stub;
4. Mini App получает готовый текст поста и даёт его отредактировать перед публикацией.
