import { AlertTriangle, LoaderCircle, RefreshCcw, ShieldCheck } from "lucide-react";
import { useAuth } from "./AuthProvider";

const stateText: Record<
  Exclude<
    ReturnType<typeof useAuth>["status"],
    "authorized"
  >,
  { title: string; description: string }
> = {
  loading: {
    title: "Проверка доступа",
    description: "Идёт верификация Telegram Mini App сессии."
  },
  forbidden: {
    title: "Доступ запрещён",
    description: "Этот Telegram user id не совпадает с id владельца приложения."
  },
  missing_api_base_url: {
    title: "Не настроен API URL",
    description: "Фронтенд не знает, куда отправлять запрос на проверку backend."
  },
  no_telegram_context: {
    title: "Нет Telegram контекста",
    description:
      "Mini App должен быть открыт из Telegram. В обычном браузере initData не приходит."
  },
  unauthorized: {
    title: "Невалидная Telegram сессия",
    description: "Backend отклонил initData или он устарел."
  },
  error: {
    title: "Ошибка связи с backend",
    description: "Проверь доступность API и CORS для текущего домена фронтенда."
  }
};

const statusLabels = {
  loading: "Проверка",
  forbidden: "Запрещён",
  missing_api_base_url: "Не настроен API URL",
  no_telegram_context: "Нет Telegram-контекста",
  unauthorized: "Сессия невалидна",
  error: "Ошибка"
} as const;

export function AuthGate() {
  const auth = useAuth();

  if (auth.status === "authorized") {
    return null;
  }

  const icon =
    auth.status === "loading" ? (
      <LoaderCircle className="spin" size={22} />
    ) : (
      <AlertTriangle size={22} />
    );
  const state = stateText[auth.status];

  return (
    <div className="auth-screen">
      <section className="auth-card">
        <div className="auth-card__icon">{icon}</div>
        <div className="stack-sm">
          <span className="auth-card__eyebrow">
            <ShieldCheck size={14} />
            Telegram авторизация
          </span>
          <h1 className="auth-card__title">{state.title}</h1>
          <p className="muted">{state.description}</p>
        </div>

        <div className="status-panel">
          <div className="status-panel__row">
            <span>Базовый URL API</span>
            <strong>{auth.apiBaseUrl || "не задан"}</strong>
          </div>
          <div className="status-panel__row">
            <span>Telegram initData</span>
            <strong>{auth.initDataPresent ? "есть" : "нет"}</strong>
          </div>
          <div className="status-panel__row">
            <span>Статус</span>
            <strong>{statusLabels[auth.status]}</strong>
          </div>
        </div>

        {auth.errorMessage ? <p className="error-text">{auth.errorMessage}</p> : null}

        <button className="button button--secondary" onClick={auth.retryAuth} type="button">
          <RefreshCcw size={16} />
          Повторить
        </button>
      </section>
    </div>
  );
}
