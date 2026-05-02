import {
  ChevronRight,
  LoaderCircle,
  Newspaper,
  Radio,
  RefreshCw,
  Settings2
} from "lucide-react";
import { type FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import { useNewsFeed } from "../features/news/useNewsFeed";
import { useSources } from "../features/news/useSources";
import { formatDateTime } from "../lib/date";

export function HomePage() {
  const { apiBaseUrl, authDate, initDataPresent, status, user } = useAuth();
  const {
    errorMessage: feedErrorMessage,
    items,
    refresh: refreshFeed,
    status: feedStatus
  } = useNewsFeed();
  const {
    create,
    errorMessage: sourcesErrorMessage,
    items: sources,
    refresh: refreshSources,
    setActiveState,
    status: sourcesStatus,
    syncNow
  } = useSources();
  const [name, setName] = useState("");
  const [feedUrl, setFeedUrl] = useState("");
  const [externalRef, setExternalRef] = useState("");
  const [formError, setFormError] = useState("");
  const [formStatus, setFormStatus] = useState<"idle" | "saving">("idle");
  const [syncState, setSyncState] = useState<Record<string, boolean>>({});
  const [toggleState, setToggleState] = useState<Record<string, boolean>>({});
  const [lastSyncSummary, setLastSyncSummary] = useState("");
  const activeSources = useMemo(
    () => sources.filter((source) => source.isActive),
    [sources]
  );
  const latestSync =
    activeSources
      .map((source) => source.lastSyncedAt)
      .filter((value): value is string => Boolean(value))
      .sort((left, right) => right.localeCompare(left))[0] ?? null;

  async function handleCreateSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");
    setLastSyncSummary("");
    setFormStatus("saving");

    try {
      await create({
        name,
        feedUrl,
        externalRef
      });
      setName("");
      setFeedUrl("");
      setExternalRef("");
      await refreshSources();
      await refreshFeed();
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Failed to create source."
      );
    } finally {
      setFormStatus("idle");
    }
  }

  async function handleSyncSource(sourceId: string) {
    setLastSyncSummary("");
    setSyncState((current) => ({ ...current, [sourceId]: true }));

    try {
      const result = await syncNow(sourceId);
      setLastSyncSummary(
        `sync ok: +${result.insertedCount} new, ~${result.updatedCount} updated, ${result.skippedCount} skipped`
      );
      await refreshSources();
      await refreshFeed();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Failed to sync source.");
    } finally {
      setSyncState((current) => ({ ...current, [sourceId]: false }));
    }
  }

  async function handleToggleSource(sourceId: string, nextState: boolean) {
    setToggleState((current) => ({ ...current, [sourceId]: true }));

    try {
      await setActiveState(sourceId, nextState);
      await refreshSources();
      await refreshFeed();
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Failed to update source state."
      );
    } finally {
      setToggleState((current) => ({ ...current, [sourceId]: false }));
    }
  }

  function scrollToSources() {
    document.getElementById("sources-panel")?.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
  }

  return (
    <div className="stack-lg">
      <section className="surface stack-md">
        <div className="surface__header">
          <div>
            <h2 className="section-title">Рабочая панель</h2>
            <p className="muted">
              Контур новостей: источники, sync, AI rewrite и публикация в Telegram.
            </p>
            <p className="muted">
              owner: {user?.username ? `@${user.username}` : user?.id} • auth:{" "}
              {authDate ? new Date(authDate).toLocaleString("ru-RU") : "n/a"}
            </p>
            {feedStatus === "error" ? (
              <p className="error-text">{feedErrorMessage}</p>
            ) : null}
            {sourcesStatus === "error" ? (
              <p className="error-text">{sourcesErrorMessage}</p>
            ) : null}
          </div>
        </div>

        <div className="hero-metrics">
          <div className="metric">
            <span className="metric__label">Источников</span>
            <strong className="metric__value">
              {sourcesStatus === "loading" ? "..." : activeSources.length}
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

      <section className="tile-grid tile-grid--two">
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
              Лента материалов, AI rewrite с редакторской задачей и публикация в Telegram.
            </p>
            <div className="feature-tile__meta">
              <span>{feedStatus === "loading" ? "..." : items.length} карточки</span>
              <span>publish ready</span>
            </div>
          </div>
        </Link>

        <button className="feature-tile feature-tile--button" onClick={scrollToSources} type="button">
          <div className="feature-tile__icon feature-tile__icon--accent">
            <Settings2 size={20} />
          </div>
          <div className="stack-sm">
            <div className="feature-tile__title-row">
              <h2 className="feature-tile__title">Источники</h2>
              <ChevronRight size={18} />
            </div>
            <p className="muted">
              Добавление RSS, ручной sync и управление активностью parser-ов.
            </p>
            <div className="feature-tile__meta">
              <span>{sourcesStatus === "loading" ? "..." : sources.length} всего</span>
              <span>auto sync 2h</span>
            </div>
          </div>
        </button>
      </section>

      <section className="surface stack-md" id="sources-panel">
        <div className="surface__header surface__header--wrap">
          <div>
            <h2 className="section-title">Источники новостей</h2>
            <p className="muted">
              Сейчас в UI поддержан `RSS`. Остальные типы можно добавить позже тем же контуром.
            </p>
          </div>
          <button
            className="button button--secondary"
            onClick={() => {
              void refreshSources();
              void refreshFeed();
            }}
            type="button"
          >
            <RefreshCw size={16} />
            Обновить
          </button>
        </div>

        <form className="source-form" onSubmit={handleCreateSource}>
          <label className="field">
            <span className="field__label">Название</span>
            <input
              className="input"
              maxLength={255}
              onChange={(event) => setName(event.target.value)}
              placeholder="BBC Sport RSS"
              required
              value={name}
            />
          </label>

          <label className="field">
            <span className="field__label">RSS URL</span>
            <input
              className="input"
              onChange={(event) => setFeedUrl(event.target.value)}
              placeholder="https://example.com/feed.xml"
              required
              type="url"
              value={feedUrl}
            />
          </label>

          <label className="field">
            <span className="field__label">External ref</span>
            <input
              className="input"
              maxLength={255}
              onChange={(event) => setExternalRef(event.target.value)}
              placeholder="bbc-football"
              value={externalRef}
            />
          </label>

          <div className="source-form__actions">
            <button
              className="button button--primary"
              disabled={formStatus === "saving"}
              type="submit"
            >
              {formStatus === "saving" ? (
                <LoaderCircle className="spin" size={16} />
              ) : (
                <Radio size={16} />
              )}
              Добавить RSS
            </button>
          </div>
        </form>

        {formError ? <p className="error-text">{formError}</p> : null}
        {lastSyncSummary ? <p className="success-text">{lastSyncSummary}</p> : null}

        <div className="source-list">
          {sourcesStatus === "loading" ? <p className="muted">Загрузка источников...</p> : null}
          {sourcesStatus === "ready" && sources.length === 0 ? (
            <p className="muted">
              Источников пока нет. Добавь первую RSS-ленту и запусти sync.
            </p>
          ) : null}

          {sources.map((source) => {
            const feedUrlValue = source.adapterConfig.feed_url;
            const feedUrlLabel =
              typeof feedUrlValue === "string" ? feedUrlValue : source.baseUrl ?? "n/a";
            const isSyncing = syncState[source.id] ?? false;
            const isToggling = toggleState[source.id] ?? false;

            return (
              <div className="source-card" key={source.id}>
                <div className="source-card__main">
                  <div className="source-row__lead">
                    <div className="feature-tile__icon feature-tile__icon--small">
                      <Radio size={16} />
                    </div>
                    <div className="stack-sm">
                      <div className="source-card__title-row">
                        <strong>{source.name}</strong>
                        <span
                          className={`pill ${
                            source.lastSyncStatus === "ok"
                              ? "pill--success"
                              : "pill--neutral"
                          }`}
                        >
                          {source.lastSyncStatus}
                        </span>
                        {!source.isActive ? (
                          <span className="pill pill--neutral">paused</span>
                        ) : null}
                      </div>
                      <p className="muted">
                        {source.sourceType} • {source.externalRef ?? "n/a"}
                      </p>
                      <p className="muted source-card__url">{feedUrlLabel}</p>
                    </div>
                  </div>

                  <div className="source-card__meta">
                    <span className="muted">
                      last sync {formatDateTime(source.lastSyncedAt)}
                    </span>
                    {source.lastErrorMessage ? (
                      <span className="error-text">{source.lastErrorMessage}</span>
                    ) : null}
                  </div>
                </div>

                <div className="source-card__actions">
                  <button
                    className="button button--secondary"
                    disabled={isToggling}
                    onClick={() => void handleToggleSource(source.id, !source.isActive)}
                    type="button"
                  >
                    {isToggling ? (
                      <LoaderCircle className="spin" size={16} />
                    ) : (
                      <Settings2 size={16} />
                    )}
                    {source.isActive ? "Выключить" : "Включить"}
                  </button>
                  <button
                    className="button button--primary"
                    disabled={isSyncing}
                    onClick={() => void handleSyncSource(source.id)}
                    type="button"
                  >
                    {isSyncing ? (
                      <LoaderCircle className="spin" size={16} />
                    ) : (
                      <RefreshCw size={16} />
                    )}
                    Sync
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
