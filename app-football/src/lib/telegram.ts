export function getTelegramWebApp(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null;
}

export function prepareTelegramWebApp(webApp: TelegramWebApp) {
  webApp.ready();
  webApp.expand();
}
