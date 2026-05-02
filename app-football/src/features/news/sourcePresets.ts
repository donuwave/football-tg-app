export interface SourcePreset {
  name: string;
  feedUrl?: string;
  externalRef: string;
  sourceType: "rss" | "website";
  status: "ready" | "planned";
  note: string;
}

export const sourcePresets: SourcePreset[] = [
  {
    name: "Чемпионат / Футбол",
    feedUrl: "https://www.championat.com/rss/news/football/",
    externalRef: "championat-football",
    sourceType: "rss",
    status: "ready",
    note: "Рабочий RSS. Можно подключать уже сейчас."
  },
  {
    name: "Soccer.ru",
    externalRef: "soccer-ru",
    sourceType: "website",
    status: "planned",
    note: "Публичный RSS не подтвердился. Нужен website-adapter."
  },
  {
    name: "UEFA",
    externalRef: "uefa-ru",
    sourceType: "website",
    status: "planned",
    note: "Публичный футбольный RSS не подтвердился. Нужен website-adapter."
  },
  {
    name: "Football24.ua",
    externalRef: "football24-ru",
    sourceType: "website",
    status: "planned",
    note: "Нужен website-adapter. Для агрегаторов у них стоит отдельно проверить правила использования."
  },
  {
    name: "Flashscore / Результаты",
    externalRef: "flashscore-results",
    sourceType: "website",
    status: "planned",
    note: "Это уже не новостная лента, а отдельный results-adapter под матчи и топ-лиги."
  }
];
