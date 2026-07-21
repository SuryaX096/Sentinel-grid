"use client";
import useSWR from "swr";
import { REFRESH_INTERVAL_MS } from "@/lib/constants";
import type { Alert } from "@/lib/types";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function useAlerts(status?: string) {
  const qs = status ? `?status=${status}` : "";
  const { data, error, isLoading, mutate } = useSWR<Alert[]>(`/api/alerts${qs}`, fetcher, {
    refreshInterval: REFRESH_INTERVAL_MS,
    revalidateOnFocus: true,
  });

  return {
    alerts: data ?? [],
    isLoading,
    isError: !!error,
    mutate, // call after approve/dismiss for an optimistic UI update
  };
}
