import { Bot, CheckCircle2, Rss, Send } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { newsItems, newsSources } from "../data/mocks";
import { PublishStatus, SourceType } from "../types";

type NewsFilter = "all" | SourceType;

const sourceTypeLabels: Record<NewsFilter, string> = {
  all: "Все",
  rss: "RSS",
  x: "X",
  website: "Site"
};

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export function NewsPage() {
  const { newsId } = useParams();
  const navigate = useNavigate();
  const [filter, setFilter] = useState<NewsFilter>("all");
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [publishState, setPublishState] = useState<Record<string, PublishStatus>>(
    {}
  );

  const filteredNews = useMemo(() => {
    if (filter === "all") {
      return newsItems;
    }

    const allowedSourceIds = new Set(
      newsSources
        .filter((source) => source.sourceType === filter)
        .map((source) => source.id)
    );

    return newsItems.filter((item) => allowedSourceIds.has(item.sourceId));
  }, [filter]);

  const selectedNews =
    filteredNews.find((item) => item.id === newsId) ?? filteredNews[0] ?? null;

  useEffect(() => {
    if (!selectedNews) {
      return;
    }

    if (!newsId || newsId !== selectedNews.id) {
      navigate(`/news/${selectedNews.id}`, { replace: true });
    }
  }, [navigate, newsId, selectedNews]);

  if (!selectedNews) {
    return (
      <section className="surface">
        <p className="muted">Нет материалов для выбранного фильтра.</p>
      </section>
    );
  }

  const selectedSource = newsSources.find(
    (source) => source.id === selectedNews.sourceId
  );
  const currentDraft = drafts[selectedNews.id] ?? "";
  const currentStatus = publishState[selectedNews.id] ?? "idle";

  async function handlePublish() {
    if (!currentDraft.trim()) {
      return;
    }

    setPublishState((current) => ({
      ...current,
      [selectedNews.id]: "processing"
    }));
    await wait(900);
    setPublishState((current) => ({
      ...current,
      [selectedNews.id]: "published"
    }));
  }

  return (
    <div className="news-layout">
      <section className="surface stack-md">
        <div className="surface__header surface__header--wrap">
          <div>
            <h2 className="section-title">Лента</h2>
            <p className="muted">{filteredNews.length} материалов в текущем срезе</p>
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

        <div className="news-list">
          {filteredNews.map((item) => {
            const itemSource = newsSources.find((source) => source.id === item.sourceId);
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
                    {itemSource?.sourceType ?? "source"}
                  </span>
                  <span className="muted">{item.publishedAt}</span>
                </div>
                <strong className="news-card__title">{item.title}</strong>
                <p className="news-card__excerpt">{item.excerpt}</p>
                <div className="news-card__footer">
                  <span>{itemSource?.name ?? "Unknown source"}</span>
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
              {selectedSource?.name} • {selectedNews.publishedAt}
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
                image hint: {selectedNews.imageHint} • source ref:{" "}
                {selectedSource?.externalRef}
              </p>
            </div>
          </div>

          <div className="stack-md">
            <div className="compose-actions">
              <button
                className="button button--secondary"
                onClick={() =>
                  setDrafts((current) => ({
                    ...current,
                    [selectedNews.id]: selectedNews.aiSuggestion
                  }))
                }
                type="button"
              >
                <Bot size={16} />
                AI шаблон
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
