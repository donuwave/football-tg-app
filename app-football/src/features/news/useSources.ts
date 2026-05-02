import { useCallback, useEffect, useState } from "react";
import { ConfiguredSource, SourceSyncResult } from "../../types";
import {
  createRssSource,
  fetchSources,
  syncSource,
  updateSourceActiveState
} from "../../lib/sources-api";

type SourcesStatus = "loading" | "ready" | "error";

export function useSources() {
  const [items, setItems] = useState<ConfiguredSource[]>([]);
  const [status, setStatus] = useState<SourcesStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setStatus("loading");
    setErrorMessage(null);

    try {
      const response = await fetchSources();
      setItems(response);
      setStatus("ready");
    } catch (error) {
      setStatus("error");
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to load sources."
      );
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const create = useCallback(
    async (payload: { name: string; feedUrl: string; externalRef?: string }) => {
      const source = await createRssSource(payload);
      setItems((current) => [source, ...current]);
      return source;
    },
    []
  );

  const syncNow = useCallback(async (sourceId: string): Promise<SourceSyncResult> => {
    const result = await syncSource(sourceId);
    setItems((current) =>
      current.map((item) => (item.id === sourceId ? result.source : item))
    );
    return result;
  }, []);

  const setActiveState = useCallback(async (sourceId: string, isActive: boolean) => {
    const source = await updateSourceActiveState(sourceId, isActive);
    setItems((current) =>
      current.map((item) => (item.id === sourceId ? source : item))
    );
    return source;
  }, []);

  return {
    items,
    status,
    errorMessage,
    refresh: load,
    create,
    syncNow,
    setActiveState
  };
}
