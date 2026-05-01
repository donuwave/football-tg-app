import { ChevronRight, Film, Newspaper, Radio } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import { useNewsFeed } from "../features/news/useNewsFeed";
import { formatDateTime } from "../lib/date";

export function HomePage() {
  const { apiBaseUrl, authDate, initDataPresent, status, user } = useAuth();
  const { errorMessage, items, sources, status: feedStatus } = useNewsFeed();
  const activeSources = sources.filter((source) => source.isActive);
  const latestSync =
    activeSources
      .map((source) => source.lastSyncedAt)
      .filter((value): value is string => Boolean(value))
      .sort((left, right) => right.localeCompare(left))[0] ?? null;

  return (
    <div className="stack-lg">
      <section className="surface stack-md">
        <div className="surface__header">
          <div>
            <h2 className="section-title">Рабочая панель</h2>
            <p className="muted">
              Один канал. Один контур публикации. Два основных сценария.
            </p>
            <p className="muted">
              owner: {user?.username ? `@${user.username}` : user?.id} • auth:{" "}
              {authDate ? new Date(authDate).toLocaleString("ru-RU") : "n/a"}
            </p>
            {feedStatus === "error" ? <p className="error-text">{errorMessage}</p> : null}
          </div>
        </div>

        <div className="hero-metrics">
          <div className="metric">
            <span className="metric__label">Источников</span>
            <strong className="metric__value">
              {feedStatus === "loading" ? "..." : activeSources.length}
            </strong>
          </div>
          <div className="metric">
            <span className="metric__label">Материалов</span>
            <strong className="metric__value">
              {feedStatus === "loading" ? "..." : items.length}
            </strong>
          </div>
          <div className="metric">
            <span className="metric__label">Последний sync</span>
            <strong className="metric__value">{formatDateTime(latestSync)}</strong>
          </div>
        </div>

        <div className="status-panel">
          <div className="surface__header">
            <div>
              <h3 className="section-title">Debug</h3>
              <p className="muted">Текущее состояние auth и backend URL, зашитые в сборку.</p>
            </div>
          </div>

          <div className="status-panel__row">
            <span>API base URL</span>
            <strong className="status-panel__value">{apiBaseUrl || "missing"}</strong>
          </div>
          <div className="status-panel__row">
            <span>Telegram initData</span>
            <strong>{initDataPresent ? "present" : "missing"}</strong>
          </div>
          <div className="status-panel__row">
            <span>Auth status</span>
            <strong>{status}</strong>
          </div>
          <div className="status-panel__row">
            <span>Owner</span>
            <strong>{user?.username ? `@${user.username}` : user?.id ?? "n/a"}</strong>
          </div>
        </div>
      </section>

      <section className="tile-grid">
        <Link className="feature-tile" to="/news">
          <div className="feature-tile__icon">
            <Newspaper size={20} />
          </div>
          <div className="stack-sm">
            <div className="feature-tile__title-row">
              <h2 className="feature-tile__title">Новости</h2>
              <ChevronRight size={18} />
            </div>
            <p className="muted">
              Лента, генерация текста и публикация выбранной новости в Telegram.
            </p>
            <div className="feature-tile__meta">
              <span>{feedStatus === "loading" ? "..." : items.length} карточки</span>
              <span>
                {feedStatus === "loading" ? "..." : activeSources.length} active sources
              </span>
            </div>
          </div>
        </Link>

        <Link className="feature-tile" to="/rubric">
          <div className="feature-tile__icon feature-tile__icon--accent">
            <Film size={20} />
          </div>
          <div className="stack-sm">
            <div className="feature-tile__title-row">
              <h2 className="feature-tile__title">Рубрика</h2>
              <ChevronRight size={18} />
            </div>
            <p className="muted">
              Два видео, два текста и один запуск публикации в Telegram, VK и
              YouTube.
            </p>
            <div className="feature-tile__meta">
              <span>Telegram video</span>
              <span>short video</span>
            </div>
          </div>
        </Link>
      </section>

      <section className="surface stack-md">
        <div className="surface__header">
          <div>
            <h2 className="section-title">Активные источники</h2>
          </div>
        </div>

        <div className="source-list">
          {feedStatus === "loading" ? <p className="muted">Загрузка источников...</p> : null}
          {activeSources.map((source) => (
            <div className="source-row" key={source.id}>
              <div className="source-row__lead">
                <div className="feature-tile__icon feature-tile__icon--small">
                  <Radio size={16} />
                </div>
                <div>
                  <strong>{source.name}</strong>
                  <p className="muted">
                    {source.sourceType} • {source.externalRef}
                  </p>
                </div>
              </div>
              <span className="pill pill--neutral">
                sync {formatDateTime(source.lastSyncedAt)}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
