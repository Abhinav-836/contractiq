"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { alertsAPI, analysisAPI, contractsAPI, obligationsAPI } from "./api";

// Everything a finished (or deleted) review can change.
const REVIEW_KEYS = ["contracts", "contractStats", "obligations", "obligationStats", "alerts", "alertStats"];

export function useInvalidateAll() {
  const qc = useQueryClient();
  return () => REVIEW_KEYS.forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
}

const pollWhileProcessing = (ms) => (query) => {
  const d = query.state.data;
  const busy = Array.isArray(d) ? d.some((c) => c.status === "processing") : d?.status === "processing";
  return busy ? ms : false;
};

/* ---------------- contracts ---------------- */
export const useContracts = (params = { limit: 100 }) =>
  useQuery({
    queryKey: ["contracts", params],
    queryFn: () => contractsAPI.list(params),
    refetchInterval: pollWhileProcessing(4000),
  });

export const useContractStats = () =>
  useQuery({ queryKey: ["contractStats"], queryFn: contractsAPI.stats, refetchInterval: 30000 });

export const useContract = (id) =>
  useQuery({
    queryKey: ["contract", id],
    queryFn: () => contractsAPI.get(id),
    enabled: Boolean(id),
    refetchInterval: pollWhileProcessing(3000),
  });

export const useAnalysis = (contractId, enabled) =>
  useQuery({
    queryKey: ["analysis", contractId],
    queryFn: () => analysisAPI.forContract(contractId),
    enabled: Boolean(contractId) && enabled,
  });

export function useUploadContract() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: ({ file, onProgress }) => contractsAPI.upload(file, onProgress),
    onSuccess: invalidate,
  });
}

export function useDeleteContract() {
  const qc = useQueryClient();
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: contractsAPI.remove,
    onSuccess: (_, id) => {
      qc.removeQueries({ queryKey: ["contract", id] });
      qc.removeQueries({ queryKey: ["analysis", id] });
      invalidate();
    },
  });
}

export function useReanalyze() {
  const qc = useQueryClient();
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: contractsAPI.reanalyze,
    onSuccess: async (_, id) => {
      qc.removeQueries({ queryKey: ["analysis", id] });
      await qc.invalidateQueries({ queryKey: ["contract", id] });
      invalidate();
    },
  });
}

/* ---------------- obligations ---------------- */
export const useObligations = (params = {}) =>
  useQuery({ queryKey: ["obligations", params], queryFn: () => obligationsAPI.list({ limit: 200, ...params }) });

export const useObligationStats = () =>
  useQuery({ queryKey: ["obligationStats"], queryFn: obligationsAPI.stats, refetchInterval: 30000 });

export function useCompleteObligation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: obligationsAPI.complete,
    // Tick it off immediately; roll back if the server refuses.
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["obligations"] });
      const snapshots = qc.getQueriesData({ queryKey: ["obligations"] });
      snapshots.forEach(([key, list]) =>
        qc.setQueryData(key, Array.isArray(list) ? list.map((o) => (o.id === id ? { ...o, status: "completed" } : o)) : list),
      );
      return { snapshots };
    },
    onError: (_e, _id, ctx) => ctx?.snapshots?.forEach(([key, list]) => qc.setQueryData(key, list)),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["obligations"] });
      qc.invalidateQueries({ queryKey: ["obligationStats"] });
    },
  });
}

export function useReopenObligation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) => obligationsAPI.update(id, { status: "pending" }),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["obligations"] });
      qc.invalidateQueries({ queryKey: ["obligationStats"] });
    },
  });
}

/* ---------------- alerts ---------------- */
export const useAlerts = (params = {}) =>
  useQuery({ queryKey: ["alerts", params], queryFn: () => alertsAPI.list({ limit: 200, ...params }), refetchInterval: 60000 });

export const useAlertStats = (enabled = true) =>
  useQuery({ queryKey: ["alertStats"], queryFn: alertsAPI.stats, refetchInterval: 30000, enabled });

function useAlertMutation(fn) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["alerts"] });
      qc.invalidateQueries({ queryKey: ["alertStats"] });
    },
  });
}

export const useMarkAlertRead = () => useAlertMutation(alertsAPI.markRead);
export const useMarkAllAlertsRead = () => useAlertMutation(alertsAPI.markAllRead);
export const useDismissAlert = () => useAlertMutation(alertsAPI.dismiss);