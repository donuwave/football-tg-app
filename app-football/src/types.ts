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
  externalRef: string;
  isActive: boolean;
  lastSyncedAt: string;
}

export interface NewsItem {
  id: string;
  sourceId: string;
  title: string;
  excerpt: string;
  rawText: string;
  publishedAt: string;
  imageHint: string;
  aiSuggestion: string;
}
