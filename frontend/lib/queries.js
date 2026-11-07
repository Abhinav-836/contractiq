"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { alertsAPI, analysisAPI, approvalsAPI, contractsAPI, obligationsAPI, workspacesAPI } from "./api";
import { useSession } from "./session";
import { useWorkspaceId } from "./workspace";

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
/* ---------------- workspaces ---------------- */
export const useWorkspaces = (enabled = true) =>
  useQuery({ queryKey: ["workspaces"], queryFn: workspacesAPI.list, enabled, staleTime: 60_000 });

/**
 * The workspace being viewed and what the user may do in it. Until the list
 * loads, actions are shown (the server still enforces every permission).
 */
export function useActiveWorkspace() {
  const session = useSession();
  const storedId = useWorkspaceId();
  const { data, isLoading, isFetching } = useWorkspaces(Boolean(session?.token));
  const workspaces = data || [];
  const active =
    workspaces.find((w) => w.id === storedId) || workspaces.find((w) => w.is_personal) || workspaces[0] || null;
  const role = active?.role;
  return {
    workspaces,
    active,
    storedId,
    isLoading,
    isFetching,
    role,
    userId: session?.user?.id,
    canEdit: role ? role !== "viewer" : true,
    canAdmin: role === "owner" || role === "admin",
    isOwner: role === "owner",
  };
}

export const useMembers = (workspaceId) =>
  useQuery({ queryKey: ["members", workspaceId], queryFn: () => workspacesAPI.members(workspaceId), enabled: Boolean(workspaceId) });

export const useInvites = (workspaceId, enabled) =>
  useQuery({
    queryKey: ["invites", workspaceId],
    queryFn: () => workspacesAPI.invites(workspaceId),
    enabled: Boolean(workspaceId) && enabled,
  });

/** Mutation that refreshes the workspace list, members and invites afterwards. */
export function useWorkspaceMutation(fn) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["workspaces"] });
      qc.invalidateQueries({ queryKey: ["members"] });
      qc.invalidateQueries({ queryKey: ["invites"] });
    },
  });
}

/* ---------------- approvals ---------------- */
export const useApprovals = (params = {}) =>
  useQuery({ queryKey: ["approvals", params], queryFn: () => approvalsAPI.list(params), refetchInterval: 60_000 });

export const useApprovalStats = (enabled = true) =>
  useQuery({ queryKey: ["approvalStats"], queryFn: approvalsAPI.stats, refetchInterval: 30_000, enabled });

export const useContractApprovals = (contractId, enabled = true) =>
  useQuery({
    queryKey: ["contractApprovals", contractId],
    queryFn: () => approvalsAPI.forContract(contractId),
    enabled: Boolean(contractId) && enabled,
  });

/** Anything that changes an approval also changes badges, lists and the contract's status. */
export function useApprovalMutation(fn) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSettled: () =>
      ["approvals", "approvalStats", "contractApprovals", "contracts", "contract"].forEach((k) =>
        qc.invalidateQueries({ queryKey: [k] }),
      ),
  });
}
