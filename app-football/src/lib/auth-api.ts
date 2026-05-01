import { apiBaseUrl } from "./config";

export interface AuthUser {
  id: number;
  first_name?: string | null;
  last_name?: string | null;
  username?: string | null;
  language_code?: string | null;
  is_premium?: boolean | null;
}

export interface TelegramAuthResponse {
  success: boolean;
  allowed: boolean;
  telegram_user_id: number;
  auth_date: string;
  query_id?: string | null;
  user: AuthUser;
}

export class ApiConfigurationError extends Error {}
export class TelegramForbiddenError extends Error {}
export class TelegramUnauthorizedError extends Error {}

export async function verifyTelegramAuth(
  initData: string
): Promise<TelegramAuthResponse> {
  if (!apiBaseUrl) {
    throw new ApiConfigurationError("VITE_API_BASE_URL is not configured.");
  }

  const response = await fetch(`${apiBaseUrl}/api/v1/auth/telegram/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ initData })
  });

  if (response.status === 403) {
    throw new TelegramForbiddenError("Telegram user is not allowed.");
  }

  if (response.status === 401) {
    throw new TelegramUnauthorizedError("Telegram initData is invalid.");
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Backend auth request failed.");
  }

  return (await response.json()) as TelegramAuthResponse;
}
