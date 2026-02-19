import { create } from "zustand";
import apiClient from "@/api/client";
import type { Transfer } from "@/types";

interface ApprovalState {
  pendingApprovals: Transfer[];
  pendingCount: number;
  isLoading: boolean;

  fetchPending: () => Promise<void>;
  fetchPendingCount: () => Promise<void>;
  approve: (transferId: number, comment?: string) => Promise<Transfer>;
  reject: (transferId: number, reason: string) => Promise<Transfer>;
}

export const useApprovalStore = create<ApprovalState>((set, get) => ({
  pendingApprovals: [],
  pendingCount: 0,
  isLoading: false,

  fetchPending: async () => {
    set({ isLoading: true });
    try {
      const { data } = await apiClient.get<Transfer[]>("/approvals/pending");
      set({ pendingApprovals: data, pendingCount: data.length, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchPendingCount: async () => {
    try {
      const { data } = await apiClient.get<{ count: number }>("/approvals/pending/count");
      set({ pendingCount: data.count });
    } catch {
      // Non-critical
    }
  },

  approve: async (transferId, comment) => {
    const { data } = await apiClient.post<Transfer>(
      `/approvals/${transferId}/approve`,
      { comment: comment ?? null },
    );
    await get().fetchPending();
    return data;
  },

  reject: async (transferId, reason) => {
    const { data } = await apiClient.post<Transfer>(
      `/approvals/${transferId}/reject`,
      { reason },
    );
    await get().fetchPending();
    return data;
  },
}));
