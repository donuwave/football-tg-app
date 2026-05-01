import { NewsItem, NewsSource, SourceType } from "../types";
import { apiBaseUrl, isDevAuthBypassEnabled } from "./config";
import { getTelegramWebApp } from "./telegram";

interface BackendNewsSource {
  id: string;
  name: string;
  source_type: SourceType;
  external_ref: string | null;
  is_active: boolean;
  last_synced_at: string | null;
}

interface BackendNewsItem {
  id: string;
  source_id: string;
  title: string;
  excerpt: string | null;
  raw_text: string;
  published_at: string | null;
  status: string;
  image_hint: string | null;
  source: BackendNewsSource;
}

interface BackendNewsFeedResponse {
  items: BackendNewsItem[];
  sources: BackendNewsSource[];
}

interface BackendGenerateNewsPostResponse {
  item_id: string;
  text: string;
}

interface BackendPublishNewsResponse {
  item_id: string;
  batch_id: string;
  job_id: string;
  status: string;
  platform: string;
  external_publication_id: string | null;
}

export interface NewsFeed {
  items: NewsItem[];
  sources: NewsSource[];
}

export interface GenerateNewsPostResponse {
  itemId: string;
  text: string;
}

export interface PublishNewsResponse {
  itemId: string;
  batchId: string;
  jobId: string;
  status: string;
  platform: string;
  externalPublicationId: string | null;
}

export class NewsApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "NewsApiError";
    this.status = status;
  }
}

class MissingTelegramInitDataError extends Error {
  constructor() {
    super("Telegram initData is missing for authenticated API request.");
    this.name = "MissingTelegramInitDataError";
  }
}

function mapSource(source: BackendNewsSource): NewsSource {
  return {
    id: source.id,
    name: source.name,
    sourceType: source.source_type,
    externalRef: source.external_ref,
    isActive: source.is_active,
    lastSyncedAt: source.last_synced_at
  };
}

function mapItem(item: BackendNewsItem): NewsItem {
  return {
    id: item.id,
    sourceId: item.source_id,
    title: item.title,
    excerpt: item.excerpt,
    rawText: item.raw_text,
    publishedAt: item.published_at,
    status: item.status,
    imageHint: item.image_hint,
    source: mapSource(item.source)
  };
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

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  if (!apiBaseUrl) {
    throw new NewsApiError("VITE_API_BASE_URL is not configured.", 0);
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
    throw new NewsApiError(text || "Backend request failed.", response.status);
  }

  return (await response.json()) as T;
}

export async function fetchNewsFeed(): Promise<NewsFeed> {
  const payload = await requestJson<BackendNewsFeedResponse>("/api/v1/news");
  return {
    items: payload.items.map(mapItem),
    sources: payload.sources.map(mapSource)
  };
}

export async function generateNewsPost(newsId: string): Promise<GenerateNewsPostResponse> {
  const payload = await requestJson<BackendGenerateNewsPostResponse>(
    `/api/v1/news/${newsId}/generate-post`,
    {
      method: "POST"
    }
  );

  return {
    itemId: payload.item_id,
    text: payload.text
  };
}

export async function publishNewsPost(
  newsId: string,
  text: string
): Promise<PublishNewsResponse> {
  const payload = await requestJson<BackendPublishNewsResponse>(
    `/api/v1/news/${newsId}/publish`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ text })
    }
  );

  return {
    itemId: payload.item_id,
    batchId: payload.batch_id,
    jobId: payload.job_id,
    status: payload.status,
    platform: payload.platform,
    externalPublicationId: payload.external_publication_id
  };
}
