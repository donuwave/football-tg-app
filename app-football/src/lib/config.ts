function normalizeBaseUrl(rawValue?: string) {
  if (!rawValue) {
    return "";
  }

  return rawValue.trim().replace(/\/+$/, "");
}

export const apiBaseUrl = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL);
export const isDevAuthBypassEnabled =
  import.meta.env.DEV && import.meta.env.VITE_ENABLE_DEV_AUTH_BYPASS === "true";
