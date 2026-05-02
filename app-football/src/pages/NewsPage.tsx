import { Bot, CheckCircle2, RefreshCw, Rss, Send } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useNewsFeed } from "../features/news/useNewsFeed";
import { formatDateTime } from "../lib/date";
import { generateNewsPost, publishNewsPost } from "../lib/news-api";
import { PublishStatus, SourceType } from "../types";

type NewsFilter = "all" | SourceType;

const sourceTypeLabels: Record<NewsFilter, string> = {
  all: "Все",
  rss: "RSS",
  x: "X",
  website: "Site"
};

export function NewsPage() {
  const { newsId } = useParams();
  const navigate = useNavigate();
  const {
    errorMessage,
    items,
    patchItem,
    refresh,
    status: feedStatus
  } = useNewsFeed();
  const [filter, setFilter] = useState<NewsFilter>("all");
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [instructions, setInstructions] = useState<Record<string, string>>({});
  const [generationState, setGenerationState] = useState<Record<string, boolean>>({});
  const [publishState, setPublishState] = useState<Record<string, PublishStatus>>(
    {}
  );
  const [generationMode, setGenerationMode] = useState<Record<string, string>>({});
  const [actionError, setActionError] = useState("");

  const filteredNews = useMemo(() => {
    if (filter === "all") {
      return items;
    }

    return items.filter((item) => item.source.sourceType === filter);
  }, [filter, items]);

  const selectedNews =
    filteredNews.find((item) => item.id === newsId) ?? filteredNews[0] ?? null;

  useEffect(() => {
    if (feedStatus !== "ready") {
      return;
    }

    if (!selectedNews) {
      return;
    }

    if (!newsId || newsId !== selectedNews.id) {
      navigate(`/news/${selectedNews.id}`, { replace: true });
    }
  }, [feedStatus, navigate, newsId, selectedNews]);

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

  if (!selectedNews) {
    return (
      <section className="surface">
        <p className="muted">Нет материалов для выбранного фильтра.</p>
      </section>
    );
  }

  const selectedSource = selectedNews.source;
  const currentDraft = drafts[selectedNews.id] ?? "";
  const currentInstruction =
    instructions[selectedNews.id] ??
    "Сделай короткий пост для Telegram-канала: 2-4 абзаца, без эмодзи, с сильным первым предложением и аккуратным завершением.";
  const currentStatus =
    publishState[selectedNews.id] ??
    (selectedNews.status === "published" ? "published" : "idle");
  const isGenerating = generationState[selectedNews.id] ?? false;
  const currentGenerationMode = generationMode[selectedNews.id] ?? null;

  async function handlePublish() {
    if (!currentDraft.trim()) {
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
      setActionError(error instanceof Error ? error.message : "Publish request failed.");
    }
  }

  async function handleGenerate() {
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
        error instanceof Error ? error.message : "Generate post request failed."
      );
    } finally {
      setGenerationState((current) => ({
        ...current,
        [selectedNews.id]: false
      }));
    }
  }

  return (
    <div className="news-layout">
      <section className="surface stack-md">
        <div className="surface__header surface__header--wrap">
          <div>
            <h2 className="section-title">Лента</h2>
            <p className="muted">{filteredNews.length} материалов в текущем срезе</p>
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

        <div className="news-list">
          {filteredNews.map((item) => {
            const isActive = item.id === selectedNews.id;

            return (
              <button
                className={`news-card${isActive ? " news-card--active" : ""}`}
                key={item.id}
                onClick={() => navigate(`/news/${item.id}`)}
                type="button"
              >
                <div className="news-card__head">
                  <span className="pill pill--neutral">
                    <Rss size={14} />
                    {item.source.sourceType}
                  </span>
                  <span className="muted">{formatDateTime(item.publishedAt)}</span>
                </div>
                <strong className="news-card__title">{item.title}</strong>
                <p className="news-card__excerpt">{item.excerpt ?? item.rawText}</p>
                <div className="news-card__footer">
                  <span>{item.source.name}</span>
                </div>
              </button>
            );
          })}
        </div>
      </section>

      <section className="surface stack-md">
        <div className="surface__header">
          <div>
            <h2 className="section-title">{selectedNews.title}</h2>
            <p className="muted">
              {selectedSource?.name} • {formatDateTime(selectedNews.publishedAt)}
            </p>
          </div>
          {currentStatus === "published" ? (
            <span className="pill pill--success">
              <CheckCircle2 size={14} />
              Отправлено
            </span>
          ) : null}
        </div>

        <div className="detail-grid">
          <div className="stack-md">
            <div className="detail-block">
              <span className="detail-block__label">Оригинал</span>
              <p>{selectedNews.rawText}</p>
            </div>
            <div className="detail-block">
              <span className="detail-block__label">Подсказка</span>
              <p className="muted">
                image hint: {selectedNews.imageHint ?? "n/a"} • source ref:{" "}
                {selectedSource?.externalRef ?? "n/a"}
              </p>
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
                {isGenerating ? "Генерация..." : "AI шаблон"}
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
              <p className="muted">provider: {currentGenerationMode}</p>
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
                placeholder="Например: сделай короткий пост, без эмодзи, с акцентом на трансферный инсайд."
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
                <span>Telegram channel</span>
                <strong>ready</strong>
              </div>
              <div className="status-panel__row">
                <span>AI result</span>
                <strong>{currentDraft.trim() ? "prepared" : "empty"}</strong>
              </div>
              <div className="status-panel__row">
                <span>Publish status</span>
                <strong>{currentStatus}</strong>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
