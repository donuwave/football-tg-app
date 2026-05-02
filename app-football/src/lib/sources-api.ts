import { ConfiguredSource, SourceSyncResult } from "../types";
import { requestProtectedJson } from "./protected-api";

interface BackendSource {
  id: string;
  name: string;
  source_type: "rss" | "x" | "website";
  base_url: string | null;
  external_ref: string | null;
  is_active: boolean;
  adapter_config: Record<string, unknown>;
  last_synced_at: string | null;
  last_sync_status: "never_run" | "ok" | "failed";
  last_error_message: string | null;
  created_at: string;
  updated_at: string;
}

interface BackendSourceListResponse {
  items: BackendSource[];
}

interface BackendSourceSyncResponse {
  source: BackendSource;
  fetched_count: number;
  inserted_count: number;
  updated_count: number;
  skipped_count: number;
  sync_status: "never_run" | "ok" | "failed";
}

function mapSource(source: BackendSource): ConfiguredSource {
  return {
    id: source.id,
    name: source.name,
    sourceType: source.source_type,
    baseUrl: source.base_url,
    externalRef: source.external_ref,
    isActive: source.is_active,
    adapterConfig: source.adapter_config,
    lastSyncedAt: source.last_synced_at,
    lastSyncStatus: source.last_sync_status,
    lastErrorMessage: source.last_error_message,
    createdAt: source.created_at,
    updatedAt: source.updated_at
  };
}

export async function fetchSources(): Promise<ConfiguredSource[]> {
  const payload = await requestProtectedJson<BackendSourceListResponse>("/api/v1/sources");
  return payload.items.map(mapSource);
}

export async function createRssSource(payload: {
  name: string;
  feedUrl: string;
  externalRef?: string;
}): Promise<ConfiguredSource> {
  const response = await requestProtectedJson<BackendSource>("/api/v1/sources", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      name: payload.name,
      source_type: "rss",
      external_ref: payload.externalRef || null,
      adapter_config: {
        feed_url: payload.feedUrl
      }
    })
  });

  return mapSource(response);
}

export async function updateSourceActiveState(
  sourceId: string,
  isActive: boolean
): Promise<ConfiguredSource> {
  const response = await requestProtectedJson<BackendSource>(
    `/api/v1/sources/${sourceId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ is_active: isActive })
    }
  );

  return mapSource(response);
}

export async function syncSource(sourceId: string): Promise<SourceSyncResult> {
  const response = await requestProtectedJson<BackendSourceSyncResponse>(
    `/api/v1/sources/${sourceId}/sync`,
    {
      method: "POST"
    }
  );

  return {
    source: mapSource(response.source),
    fetchedCount: response.fetched_count,
    insertedCount: response.inserted_count,
    updatedCount: response.updated_count,
    skippedCount: response.skipped_count,
    syncStatus: response.sync_status
  };
}
