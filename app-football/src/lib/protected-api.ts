import { apiBaseUrl, isDevAuthBypassEnabled } from "./config";
import { getTelegramWebApp } from "./telegram";

export class BackendApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "BackendApiError";
    this.status = status;
  }
}

export class MissingTelegramInitDataError extends Error {
  constructor() {
    super("Telegram initData is missing for authenticated API request.");
    this.name = "MissingTelegramInitDataError";
  }
}

function buildAuthHeaders() {
  const initData = getTelegramWebApp()?.initData?.trim() ?? "";

  if (!initData) {
    if (isDevAuthBypassEnabled) {
      return {};
    }

    throw new MissingTelegramInitDataError();
  }

  return {
    "X-Telegram-Init-Data": initData
  };
}

export async function requestProtectedJson<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  if (!apiBaseUrl) {
    throw new BackendApiError("VITE_API_BASE_URL is not configured.", 0);
  }

  const headers = new Headers(init?.headers);
  for (const [key, value] of Object.entries(buildAuthHeaders())) {
    headers.set(key, value);
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers
  });

  if (!response.ok) {
    const text = await response.text();
    throw new BackendApiError(text || "Backend request failed.", response.status);
  }

  return (await response.json()) as T;
}
