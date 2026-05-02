import { NewsItem, NewsSource, SourceType } from "../types";
import { requestProtectedJson } from "./protected-api";

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
  mode: string;
}

interface BackendTranslateNewsResponse {
  item_id: string;
  text: string;
  mode: string;
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
  mode: string;
}

export interface PublishNewsResponse {
  itemId: string;
  batchId: string;
  jobId: string;
  status: string;
  platform: string;
  externalPublicationId: string | null;
}

export interface TranslateNewsResponse {
  itemId: string;
  text: string;
  mode: string;
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

export async function fetchNewsFeed(): Promise<NewsFeed> {
  const payload = await requestProtectedJson<BackendNewsFeedResponse>("/api/v1/news");
  return {
    items: payload.items.map(mapItem),
    sources: payload.sources.map(mapSource)
  };
}

export async function generateNewsPost(
  newsId: string,
  instruction: string
): Promise<GenerateNewsPostResponse> {
  const payload = await requestProtectedJson<BackendGenerateNewsPostResponse>(
    `/api/v1/news/${newsId}/generate-post`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ instruction })
    }
  );

  return {
    itemId: payload.item_id,
    text: payload.text,
    mode: payload.mode
  };
}

export async function translateNewsItem(newsId: string): Promise<TranslateNewsResponse> {
  const payload = await requestProtectedJson<BackendTranslateNewsResponse>(
    `/api/v1/news/${newsId}/translate`,
    {
      method: "POST"
    }
  );

  return {
    itemId: payload.item_id,
    text: payload.text,
    mode: payload.mode
  };
}

export async function publishNewsPost(
  newsId: string,
  text: string
): Promise<PublishNewsResponse> {
  const payload = await requestProtectedJson<BackendPublishNewsResponse>(
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
