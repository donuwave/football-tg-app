import { CheckCircle2, Film, Send, Upload } from "lucide-react";
import { ChangeEvent, useState } from "react";
import { initialShortCaption, initialTelegramText } from "../data/mocks";
import { BatchStatus, PublishStatus } from "../types";

interface PlatformState {
  telegram: PublishStatus;
  vk: PublishStatus;
  youtube: PublishStatus;
}

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export function RubricPage() {
  const [telegramText, setTelegramText] = useState(initialTelegramText);
  const [shortCaption, setShortCaption] = useState(initialShortCaption);
  const [telegramVideoName, setTelegramVideoName] = useState("");
  const [shortVideoName, setShortVideoName] = useState("");
  const [batchStatus, setBatchStatus] = useState<BatchStatus>("idle");
  const [error, setError] = useState("");
  const [platforms, setPlatforms] = useState<PlatformState>({
    telegram: "idle",
    vk: "idle",
    youtube: "idle"
  });

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
    target: "telegram" | "short"
  ) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setError("");

    if (target === "telegram") {
      setTelegramVideoName(file.name);
      return;
    }

    setShortVideoName(file.name);
  }

  async function handlePublish() {
    if (
      !telegramVideoName ||
      !shortVideoName ||
      !telegramText.trim() ||
      !shortCaption.trim()
    ) {
      setError("Нужно заполнить все 4 поля.");
      setBatchStatus("failed");
      return;
    }

    setError("");
    setBatchStatus("validating");
    setPlatforms({
      telegram: "idle",
      vk: "idle",
      youtube: "idle"
    });

    await wait(500);
    setBatchStatus("processing");
    setPlatforms({
      telegram: "processing",
      vk: "processing",
      youtube: "processing"
    });

    await wait(500);
    setPlatforms({
      telegram: "published",
      vk: "processing",
      youtube: "processing"
    });

    await wait(500);
    setPlatforms({
      telegram: "published",
      vk: "published",
      youtube: "processing"
    });

    await wait(500);
    setPlatforms({
      telegram: "published",
      vk: "published",
      youtube: "published"
    });
    setBatchStatus("completed");
  }

  return (
    <div className="stack-lg">
      <section className="surface stack-md">
        <div className="surface__header">
          <div>
            <h2 className="section-title">Пакет публикации</h2>
            <p className="muted">
              Один запуск создаёт публикацию для Telegram, VK и YouTube.
            </p>
          </div>
          {batchStatus === "completed" ? (
            <span className="pill pill--success">
              <CheckCircle2 size={14} />
              Готово
            </span>
          ) : null}
        </div>

        <div className="rubric-grid">
          <div className="stack-md">
            <div className="detail-block">
              <span className="detail-block__label">Telegram video</span>
              <label className="upload-card">
                <input
                  accept="video/*"
                  hidden
                  onChange={(event) => handleFileChange(event, "telegram")}
                  type="file"
                />
                <Upload size={18} />
                <div>
                  <strong>
                    {telegramVideoName || "Выбрать видео для Telegram"}
                  </strong>
                  <p className="muted">Исходное видео для поста в канале.</p>
                </div>
              </label>
            </div>

            <label className="stack-sm">
              <span className="detail-block__label">Telegram text</span>
              <textarea
                className="textarea textarea--large"
                onChange={(event) => setTelegramText(event.target.value)}
                placeholder="Текст поста для Telegram."
                value={telegramText}
              />
            </label>
          </div>

          <div className="stack-md">
            <div className="detail-block">
              <span className="detail-block__label">Short video</span>
              <label className="upload-card upload-card--accent">
                <input
                  accept="video/*"
                  hidden
                  onChange={(event) => handleFileChange(event, "short")}
                  type="file"
                />
                <Film size={18} />
                <div>
                  <strong>{shortVideoName || "Выбрать short для VK / YouTube"}</strong>
                  <p className="muted">
                    Один файл используется для VK и YouTube.
                  </p>
                </div>
              </label>
            </div>

            <label className="stack-sm">
              <span className="detail-block__label">Short caption</span>
              <textarea
                className="textarea textarea--large"
                onChange={(event) => setShortCaption(event.target.value)}
                placeholder="Описание для VK и YouTube."
                value={shortCaption}
              />
            </label>
          </div>
        </div>
      </section>

      <section className="surface stack-md">
        <div className="surface__header surface__header--wrap">
          <div>
            <h2 className="section-title">Статус отправки</h2>
            <p className="muted">Фронтенд сейчас работает на моковом пайплайне.</p>
          </div>

          <button
            className="button button--primary"
            disabled={batchStatus === "processing" || batchStatus === "validating"}
            onClick={handlePublish}
            type="button"
          >
            <Send size={16} />
            {batchStatus === "processing" || batchStatus === "validating"
              ? "Публикация..."
              : "Опубликовать"}
          </button>
        </div>

        {error ? <p className="error-text">{error}</p> : null}

        <div className="platform-grid">
          <div className="status-panel">
            <div className="status-panel__row">
              <span>Telegram</span>
              <strong>{platforms.telegram}</strong>
            </div>
            <div className="status-panel__row">
              <span>VK</span>
              <strong>{platforms.vk}</strong>
            </div>
            <div className="status-panel__row">
              <span>YouTube</span>
              <strong>{platforms.youtube}</strong>
            </div>
            <div className="status-panel__row">
              <span>Batch</span>
              <strong>{batchStatus}</strong>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
