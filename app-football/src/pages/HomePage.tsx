import { ChevronRight, Film, Newspaper, Radio } from "lucide-react";
import { Link } from "react-router-dom";
import { newsItems, newsSources } from "../data/mocks";

export function HomePage() {
  const activeSources = newsSources.filter((source) => source.isActive);
  const latestSync = activeSources[0]?.lastSyncedAt ?? "n/a";

  return (
    <div className="stack-lg">
      <section className="surface stack-md">
        <div className="surface__header">
          <div>
            <h2 className="section-title">Рабочая панель</h2>
            <p className="muted">
              Один канал. Один контур публикации. Два основных сценария.
            </p>
          </div>
        </div>

        <div className="hero-metrics">
          <div className="metric">
            <span className="metric__label">Источников</span>
            <strong className="metric__value">{activeSources.length}</strong>
          </div>
          <div className="metric">
            <span className="metric__label">Материалов</span>
            <strong className="metric__value">{newsItems.length}</strong>
          </div>
          <div className="metric">
            <span className="metric__label">Последний sync</span>
            <strong className="metric__value">{latestSync}</strong>
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
              <span>{newsItems.length} карточки</span>
              <span>{activeSources.length} active sources</span>
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
              <span className="pill pill--neutral">sync {source.lastSyncedAt}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
