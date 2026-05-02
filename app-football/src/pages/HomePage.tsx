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
import { sourcePresets } from "../features/news/sourcePresets";
import { formatDateTime } from "../lib/date";

const sourceTypeLabels = {
  rss: "RSS",
  x: "X",
  website: "Сайт"
} as const;

const syncStatusLabels = {
  never_run: "Не запускался",
  ok: "Ок",
  failed: "Ошибка"
} as const;

const authStatusLabels = {
  loading: "Проверка",
  authorized: "Разрешён",
  forbidden: "Запрещён",
  missing_api_base_url: "Не настроен API URL",
  no_telegram_context: "Нет Telegram-контекста",
  unauthorized: "Сессия невалидна",
  error: "Ошибка"
} as const;

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
  const [presetState, setPresetState] = useState<Record<string, boolean>>({});
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
        `Синхронизация завершена: +${result.insertedCount} новых, ~${result.updatedCount} обновлено, ${result.skippedCount} пропущено`
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

  async function handleAddPreset(presetName: string) {
    const preset = sourcePresets.find((item) => item.name === presetName);
    if (!preset || !preset.feedUrl || preset.status !== "ready") {
      return;
    }

    setFormError("");
    setLastSyncSummary("");
    setPresetState((current) => ({ ...current, [preset.name]: true }));

    try {
      await create({
        name: preset.name,
        feedUrl: preset.feedUrl,
        externalRef: preset.externalRef
      });
      await refreshSources();
      await refreshFeed();
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Не удалось добавить preset-источник."
      );
    } finally {
      setPresetState((current) => ({ ...current, [preset.name]: false }));
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
              владелец: {user?.username ? `@${user.username}` : user?.id} • вход:{" "}
              {authDate ? new Date(authDate).toLocaleString("ru-RU") : "нет"}
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
              <h3 className="section-title">Отладка</h3>
              <p className="muted">Текущее состояние авторизации и адреса backend.</p>
            </div>
          </div>

          <div className="status-panel__row">
            <span>Базовый URL API</span>
            <strong className="status-panel__value">{apiBaseUrl || "не задан"}</strong>
          </div>
          <div className="status-panel__row">
            <span>Telegram initData</span>
            <strong>{initDataPresent ? "есть" : "нет"}</strong>
          </div>
          <div className="status-panel__row">
            <span>Статус входа</span>
            <strong>{authStatusLabels[status]}</strong>
          </div>
          <div className="status-panel__row">
            <span>Владелец</span>
            <strong>{user?.username ? `@${user.username}` : user?.id ?? "нет"}</strong>
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
              <span>готово к публикации</span>
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
              <span>автосинк каждые 2 часа</span>
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
            <span className="field__label">URL RSS-ленты</span>
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
            <span className="field__label">Референс источника</span>
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

        <div className="stack-sm">
          <div>
            <h3 className="section-title">Быстрые пресеты</h3>
            <p className="muted">
              Из твоего списка сейчас без нового адаптера подтверждён только один рабочий RSS.
            </p>
          </div>
          <div className="source-list">
            {sourcePresets.map((preset) => {
              const isReady = preset.status === "ready" && Boolean(preset.feedUrl);
              const isSaving = presetState[preset.name] ?? false;

              return (
                <div className="source-card" key={preset.name}>
                  <div className="source-card__main">
                    <div className="stack-sm">
                      <div className="source-card__title-row">
                        <strong>{preset.name}</strong>
                        <span
                          className={`pill ${isReady ? "pill--success" : "pill--neutral"}`}
                        >
                          {isReady ? "Готов" : "Нужен адаптер"}
                        </span>
                      </div>
                      <p className="muted">{preset.note}</p>
                      <p className="muted">
                        Тип: {sourceTypeLabels[preset.sourceType]} • ref: {preset.externalRef}
                      </p>
                      {preset.feedUrl ? (
                        <p className="muted">Feed: {preset.feedUrl}</p>
                      ) : null}
                    </div>
                  </div>
                  <div className="source-card__actions">
                    <button
                      className="button button--secondary"
                      disabled={!isReady || isSaving}
                      onClick={() => void handleAddPreset(preset.name)}
                      type="button"
                    >
                      {isSaving ? (
                        <LoaderCircle className="spin" size={16} />
                      ) : (
                        <Radio size={16} />
                      )}
                      {isReady ? "Добавить" : "Позже"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

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
              typeof feedUrlValue === "string" ? feedUrlValue : source.baseUrl ?? "нет";
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
                          {syncStatusLabels[source.lastSyncStatus]}
                        </span>
                        {!source.isActive ? (
                          <span className="pill pill--neutral">Выключен</span>
                        ) : null}
                      </div>
                      <p className="muted">
                        {sourceTypeLabels[source.sourceType]} • {source.externalRef ?? "нет"}
                      </p>
                      <p className="muted source-card__url">{feedUrlLabel}</p>
                    </div>
                  </div>

                  <div className="source-card__meta">
                    <span className="muted">
                      Последняя синхронизация: {formatDateTime(source.lastSyncedAt)}
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
                    Синхронизировать
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
