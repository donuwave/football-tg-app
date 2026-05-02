import {
  ArrowLeft,
  Bot,
  CheckCircle2,
  RefreshCw,
  Rss,
  Send
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useNewsFeed } from "../features/news/useNewsFeed";
import { formatDateTime } from "../lib/date";
import { generateNewsPost, publishNewsPost } from "../lib/news-api";
import { PublishStatus, SourceType } from "../types";

type NewsFilter = "all" | SourceType;

const sourceTypeLabels: Record<NewsFilter, string> = {
  all: "Все",
  rss: "RSS",
  x: "X",
  website: "Сайт"
};

const publishStatusLabels: Record<PublishStatus, string> = {
  idle: "Черновик",
  processing: "Публикуется",
  published: "Опубликовано",
  failed: "Ошибка"
};

const itemStatusLabels: Record<string, string> = {
  new: "Новая",
  published: "Опубликована",
  archived: "В архиве"
};

const aiModeLabels: Record<string, string> = {
  stub: "Шаблон",
  ollama: "Ollama"
};

function normalizeFilter(value: string | null): NewsFilter {
  if (value === "rss" || value === "x" || value === "website") {
    return value;
  }

  return "all";
}

export function NewsPage() {
  const { newsId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    errorMessage,
    items,
    patchItem,
    refresh,
    status: feedStatus
  } = useNewsFeed();
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [instructions, setInstructions] = useState<Record<string, string>>({});
  const [generationState, setGenerationState] = useState<Record<string, boolean>>({});
  const [publishState, setPublishState] = useState<Record<string, PublishStatus>>(
    {}
  );
  const [generationMode, setGenerationMode] = useState<Record<string, string>>({});
  const [actionError, setActionError] = useState("");
  const filter = normalizeFilter(searchParams.get("filter"));

  const filteredNews = useMemo(() => {
    if (filter === "all") {
      return items;
    }

    return items.filter((item) => item.source.sourceType === filter);
  }, [filter, items]);

  const selectedNews = useMemo(
    () => items.find((item) => item.id === newsId) ?? null,
    [items, newsId]
  );

  const currentDraft = selectedNews ? drafts[selectedNews.id] ?? "" : "";
  const currentInstruction = selectedNews
    ? instructions[selectedNews.id] ??
      "Сделай короткий пост для Telegram на русском языке, без эмодзи, с акцентом на главный факт."
    : "";
  const currentStatus: PublishStatus = selectedNews
    ? publishState[selectedNews.id] ??
      (selectedNews.status === "published" ? "published" : "idle")
    : "idle";
  const isGenerating = selectedNews ? generationState[selectedNews.id] ?? false : false;
  const currentGenerationMode = selectedNews
    ? generationMode[selectedNews.id] ?? null
    : null;

  function setFilter(nextFilter: NewsFilter) {
    const nextParams = new URLSearchParams(searchParams);
    if (nextFilter === "all") {
      nextParams.delete("filter");
    } else {
      nextParams.set("filter", nextFilter);
    }
    setSearchParams(nextParams, { replace: true });
  }

  function openNews(nextNewsId: string) {
    const query = searchParams.toString();
    navigate(`/news/${nextNewsId}${query ? `?${query}` : ""}`);
  }

  function goToList() {
    const query = searchParams.toString();
    navigate(`/news${query ? `?${query}` : ""}`);
  }

  async function handlePublish() {
    if (!selectedNews || !currentDraft.trim()) {
      return;
    }

    setActionError("");
    setPublishState((current) => ({
      ...current,
      [selectedNews.id]: "processing"
    }));

    try {
      await publishNewsPost(selectedNews.id, currentDraft);
      patchItem(selectedNews.id, { status: "published" });
      setPublishState((current) => ({
        ...current,
        [selectedNews.id]: "published"
      }));
    } catch (error) {
      setPublishState((current) => ({
        ...current,
        [selectedNews.id]: "failed"
      }));
      setActionError(error instanceof Error ? error.message : "Не удалось опубликовать пост.");
    }
  }

  async function handleGenerate() {
    if (!selectedNews) {
      return;
    }

    setActionError("");
    setGenerationState((current) => ({
      ...current,
      [selectedNews.id]: true
    }));

    try {
      const result = await generateNewsPost(selectedNews.id, currentInstruction);
      setDrafts((current) => ({
        ...current,
        [selectedNews.id]: result.text
      }));
      setGenerationMode((current) => ({
        ...current,
        [selectedNews.id]: result.mode
      }));
    } catch (error) {
      setActionError(
        error instanceof Error ? error.message : "Не удалось сгенерировать текст."
      );
    } finally {
      setGenerationState((current) => ({
        ...current,
        [selectedNews.id]: false
      }));
    }
  }

  if (feedStatus === "loading") {
    return (
      <section className="surface">
        <p className="muted">Загрузка ленты новостей...</p>
      </section>
    );
  }

  if (feedStatus === "error") {
    return (
      <section className="surface stack-sm">
        <h2 className="section-title">Не удалось загрузить новости</h2>
        <p className="error-text">{errorMessage}</p>
      </section>
    );
  }

  if (!newsId) {
    return (
      <section className="surface stack-md">
        <div className="surface__header surface__header--wrap">
          <div>
            <h2 className="section-title">Лента новостей</h2>
            <p className="muted">{filteredNews.length} материалов в текущем фильтре</p>
          </div>
          <div className="control-cluster">
            <div className="chip-group">
              {(Object.keys(sourceTypeLabels) as NewsFilter[]).map((key) => (
                <button
                  key={key}
                  className={`chip-button${filter === key ? " chip-button--active" : ""}`}
                  onClick={() => setFilter(key)}
                  type="button"
                >
                  {sourceTypeLabels[key]}
                </button>
              ))}
            </div>
            <button className="button button--secondary" onClick={() => void refresh()} type="button">
              <RefreshCw size={16} />
              Обновить
            </button>
          </div>
        </div>

        {filteredNews.length === 0 ? (
          <div className="detail-block">
            <span className="detail-block__label">Список пуст</span>
            <p>
              По текущему фильтру материалов нет. Фильтр сохранён, можешь сменить его
              или дождаться следующей синхронизации.
            </p>
          </div>
        ) : (
          <div className="news-list">
            {filteredNews.map((item) => (
              <button
                className="news-card"
                key={item.id}
                onClick={() => openNews(item.id)}
                type="button"
              >
                <div className="news-card__head">
                  <span className="pill pill--neutral">
                    <Rss size={14} />
                    {sourceTypeLabels[item.source.sourceType]}
                  </span>
                  <span className="muted">{formatDateTime(item.publishedAt)}</span>
                </div>
                <strong className="news-card__title">{item.title}</strong>
                <p className="news-card__excerpt">{item.excerpt ?? item.rawText}</p>
                <div className="news-card__footer">
                  <span>{item.source.name}</span>
                  <span className="muted">{itemStatusLabels[item.status] ?? item.status}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </section>
    );
  }

  if (!selectedNews) {
    return (
      <section className="surface stack-md">
        <div className="surface__header">
          <div>
            <h2 className="section-title">Новость не найдена</h2>
            <p className="muted">
              Материал пропал из ленты или ещё не загрузился после синхронизации.
            </p>
          </div>
        </div>
        <button className="button button--secondary" onClick={goToList} type="button">
          <ArrowLeft size={16} />
          Вернуться к ленте
        </button>
      </section>
    );
  }

  return (
    <div className="stack-lg">
      <section className="surface stack-md">
        <div className="surface__header surface__header--wrap">
          <div className="stack-sm">
            <button className="button button--secondary button--inline" onClick={goToList} type="button">
              <ArrowLeft size={16} />
              К ленте
            </button>
            <div>
              <h2 className="section-title">{selectedNews.title}</h2>
              <p className="muted">
                {selectedNews.source.name} • {formatDateTime(selectedNews.publishedAt)}
              </p>
            </div>
          </div>
          {currentStatus === "published" ? (
            <span className="pill pill--success">
              <CheckCircle2 size={14} />
              Опубликовано
            </span>
          ) : null}
        </div>

        <div className="detail-grid">
          <div className="stack-md">
            <div className="detail-block">
              <span className="detail-block__label">Оригинальный материал</span>
              <p>{selectedNews.rawText}</p>
            </div>
            <div className="detail-block">
              <span className="detail-block__label">Данные источника</span>
              <p className="muted">
                Тип: {sourceTypeLabels[selectedNews.source.sourceType]} • референс:{" "}
                {selectedNews.source.externalRef ?? "нет"}
              </p>
              <p className="muted">
                Подсказка по изображению: {selectedNews.imageHint ?? "нет"}
              </p>
              {selectedNews.source.externalRef ? (
                <p className="muted">Источник: {selectedNews.source.externalRef}</p>
              ) : null}
            </div>
          </div>

          <div className="stack-md">
            <div className="compose-actions">
              <button
                className="button button--secondary"
                disabled={isGenerating}
                onClick={handleGenerate}
                type="button"
              >
                <Bot size={16} />
                {isGenerating ? "Генерация..." : "Сгенерировать текст"}
              </button>

              <button
                className="button button--primary"
                disabled={!currentDraft.trim() || currentStatus === "processing"}
                onClick={handlePublish}
                type="button"
              >
                <Send size={16} />
                {currentStatus === "processing"
                  ? "Публикация..."
                  : "Опубликовать в Telegram"}
              </button>
            </div>

            {actionError ? <p className="error-text">{actionError}</p> : null}
            {currentGenerationMode ? (
              <p className="muted">
                Режим AI: {aiModeLabels[currentGenerationMode] ?? currentGenerationMode}
              </p>
            ) : null}

            <label className="stack-sm">
              <span className="detail-block__label">Задание для AI</span>
              <textarea
                className="textarea textarea--instruction"
                onChange={(event) =>
                  setInstructions((current) => ({
                    ...current,
                    [selectedNews.id]: event.target.value
                  }))
                }
                placeholder="Например: сделай короткий пост без эмодзи с акцентом на трансферный инсайд."
                value={currentInstruction}
              />
            </label>

            <label className="stack-sm">
              <span className="detail-block__label">Текст поста</span>
              <textarea
                className="textarea"
                onChange={(event) =>
                  setDrafts((current) => ({
                    ...current,
                    [selectedNews.id]: event.target.value
                  }))
                }
                placeholder="Сгенерируй или напиши финальный текст публикации."
                value={currentDraft}
              />
            </label>

            <div className="status-panel">
              <div className="status-panel__row">
                <span>Канал Telegram</span>
                <strong>Готов</strong>
              </div>
              <div className="status-panel__row">
                <span>Текст поста</span>
                <strong>{currentDraft.trim() ? "Готов" : "Пусто"}</strong>
              </div>
              <div className="status-panel__row">
                <span>Статус публикации</span>
                <strong>{publishStatusLabels[currentStatus]}</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="surface stack-md">
        <div className="surface__header surface__header--wrap">
          <div>
            <h2 className="section-title">Текущий фильтр ленты</h2>
            <p className="muted">
              Фильтр сохранён, даже если по нему сейчас нет материалов.
            </p>
          </div>
          <div className="chip-group">
            {(Object.keys(sourceTypeLabels) as NewsFilter[]).map((key) => (
              <button
                key={key}
                className={`chip-button${filter === key ? " chip-button--active" : ""}`}
                onClick={() => setFilter(key)}
                type="button"
              >
                {sourceTypeLabels[key]}
              </button>
            ))}
          </div>
        </div>
        <p className="muted">
          Вернуться к списку:{" "}
          <Link className="inline-link" to={`/news${searchParams.toString() ? `?${searchParams.toString()}` : ""}`}>
            открыть ленту
          </Link>
        </p>
      </section>
    </div>
  );
}
