import {
  ReactNode,
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";
import {
  ApiConfigurationError,
  AuthUser,
  TelegramForbiddenError,
  TelegramUnauthorizedError,
  verifyTelegramAuth
} from "../lib/auth-api";
import { apiBaseUrl, isDevAuthBypassEnabled } from "../lib/config";
import { getTelegramWebApp, prepareTelegramWebApp } from "../lib/telegram";

type AuthStatus =
  | "loading"
  | "authorized"
  | "forbidden"
  | "missing_api_base_url"
  | "no_telegram_context"
  | "unauthorized"
  | "error";

interface AuthState {
  status: AuthStatus;
  user: AuthUser | null;
  authDate: string | null;
  errorMessage: string | null;
  initDataPresent: boolean;
  apiBaseUrl: string;
  retryAuth: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

const devBypassUser: AuthUser = {
  id: 0,
  first_name: "Local",
  username: "dev_bypass"
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authDate, setAuthDate] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [initDataPresent, setInitDataPresent] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let isCancelled = false;

    async function bootstrapAuth() {
      setStatus("loading");
      setUser(null);
      setAuthDate(null);
      setErrorMessage(null);

      if (!apiBaseUrl) {
        setInitDataPresent(false);
        setStatus("missing_api_base_url");
        return;
      }

      const webApp = getTelegramWebApp();
      const initData = webApp?.initData?.trim() ?? "";
      setInitDataPresent(Boolean(initData));

      if (!webApp || !initData) {
        if (isDevAuthBypassEnabled) {
          setStatus("authorized");
          setUser(devBypassUser);
          setAuthDate(new Date().toISOString());
          return;
        }

        setStatus("no_telegram_context");
        return;
      }

      prepareTelegramWebApp(webApp);

      try {
        const response = await verifyTelegramAuth(initData);

        if (isCancelled) {
          return;
        }

        setStatus("authorized");
        setUser(response.user);
        setAuthDate(response.auth_date);
      } catch (error) {
        if (isCancelled) {
          return;
        }

        if (error instanceof ApiConfigurationError) {
          setStatus("missing_api_base_url");
          setErrorMessage(error.message);
          return;
        }

        if (error instanceof TelegramForbiddenError) {
          setStatus("forbidden");
          setErrorMessage(error.message);
          return;
        }

        if (error instanceof TelegramUnauthorizedError) {
          setStatus("unauthorized");
          setErrorMessage(error.message);
          return;
        }

        setStatus("error");
        setErrorMessage(
          error instanceof Error ? error.message : "Unknown authorization error."
        );
      }
    }

    void bootstrapAuth();

    return () => {
      isCancelled = true;
    };
  }, [attempt]);

  const value = useMemo<AuthState>(
    () => ({
      status,
      user,
      authDate,
      errorMessage,
      initDataPresent,
      apiBaseUrl,
      retryAuth: () => setAttempt((current) => current + 1)
    }),
    [authDate, errorMessage, initDataPresent, status, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}
