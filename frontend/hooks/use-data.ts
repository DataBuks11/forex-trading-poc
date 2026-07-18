"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => {
      const { data } = await api.get("/dashboard");
      return data;
    },
    refetchInterval: 10000,
  });
}

export function useMT5Status() {
  return useQuery({
    queryKey: ["mt5-status"],
    queryFn: async () => {
      const { data } = await api.get("/mt5/status");
      return data;
    },
    refetchInterval: 10000,
  });
}

export function useMT5Positions() {
  return useQuery({
    queryKey: ["mt5-positions"],
    queryFn: async () => {
      const { data } = await api.get("/mt5/positions");
      return data;
    },
    refetchInterval: 5000,
  });
}

export function useTradeHistory(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["trade-history", params],
    queryFn: async () => {
      const { data } = await api.get("/trades/history", { params });
      return data;
    },
    refetchInterval: 10000,
  });
}

export function useOpenTrades() {
  return useQuery({
    queryKey: ["open-trades"],
    queryFn: async () => {
      const { data } = await api.get("/trades/open");
      return data;
    },
    refetchInterval: 5000,
  });
}

export function useActivityLog() {
  return useQuery({
    queryKey: ["activity-log"],
    queryFn: async () => {
      const { data } = await api.get("/activity");
      return data;
    },
    refetchInterval: 10000,
  });
}

export function useWebhookHistory() {
  return useQuery({
    queryKey: ["webhook-history"],
    queryFn: async () => {
      const { data } = await api.get("/webhook/history");
      return data;
    },
    refetchInterval: 10000,
  });
}

export function useWebhookSettings() {
  return useQuery({
    queryKey: ["webhook-settings"],
    queryFn: async () => {
      const { data } = await api.get("/webhook/settings");
      return data;
    },
  });
}

export function useLastSignal() {
  return useQuery({
    queryKey: ["last-signal"],
    queryFn: async () => {
      const { data } = await api.get("/webhook/last-signal");
      return data;
    },
    refetchInterval: 5000,
  });
}

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: async () => {
      const { data } = await api.get("/settings");
      return data;
    },
  });
}
