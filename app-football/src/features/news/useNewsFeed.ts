import { useCallback, useEffect, useState } from "react";
import { NewsItem, NewsSource } from "../../types";
import { fetchNewsFeed } from "../../lib/news-api";

type FeedStatus = "loading" | "ready" | "error";

export function useNewsFeed() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [sources, setSources] = useState<NewsSource[]>([]);
  const [status, setStatus] = useState<FeedStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setStatus("loading");
    setErrorMessage(null);

    try {
      const feed = await fetchNewsFeed();
      setItems(feed.items);
      setSources(feed.sources);
      setStatus("ready");
    } catch (error) {
      setStatus("error");
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to load news feed."
      );
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const patchItem = useCallback(
    (itemId: string, patch: Partial<NewsItem>) => {
      setItems((current) =>
        current.map((item) => (item.id === itemId ? { ...item, ...patch } : item))
      );
    },
    []
  );

  return {
    items,
    sources,
    status,
    errorMessage,
    refresh: load,
    patchItem
  };
}
