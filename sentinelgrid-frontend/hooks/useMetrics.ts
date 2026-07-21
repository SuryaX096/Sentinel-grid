"use client";
import useSWR from "swr";
import { REFRESH_INTERVAL_MS } from "@/lib/constants";
import type { Metrics } from "@/lib/types";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function useMetrics() {
  const { data, error, isLoading } = useSWR<Metrics>("/api/metrics", fetcher, {
    refreshInterval: REFRESH_INTERVAL_MS,
  });

  return { metrics: data, isLoading, isError: !!error };
}
