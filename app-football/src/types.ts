export type SourceType = "rss" | "x" | "website";

export type PublishStatus = "idle" | "processing" | "published" | "failed";

export type BatchStatus =
  | "idle"
  | "validating"
  | "processing"
  | "completed"
  | "failed";

export interface NewsSource {
  id: string;
  name: string;
  sourceType: SourceType;
  externalRef: string | null;
  isActive: boolean;
  lastSyncedAt: string | null;
}

export interface NewsItem {
  id: string;
  sourceId: string;
  title: string;
  excerpt: string | null;
  rawText: string;
  publishedAt: string | null;
  status: string;
  imageHint: string | null;
  source: NewsSource;
}
