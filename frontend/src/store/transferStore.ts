import { create } from "zustand";
import { transfersApi } from "@/api/transfers";
import type { Transfer, TransferStats } from "@/types";

interface Pagination {
  page: number;
  perPage: number;
  total: number;
  pages: number;
}

interface TransferState {
  transfers: Transfer[];
  currentTransfer: Transfer | null;
  stats: TransferStats | null;
  isLoading: boolean;
  error: string | null;
  pagination: Pagination;

  fetchTransfers: (filters?: {
    status?: string;
    category?: string;
    search?: string;
    page?: number;
    per_page?: number;
  }) => Promise<void>;
  fetchTransfer: (id: number) => Promise<void>;
  fetchStats: () => Promise<void>;
  createTransfer: (data: {
    name: string;
    category?: string;
    priority?: string;
    notes?: string;
    shotgrid_project_id?: number;
    shotgrid_entity_type?: string;
    shotgrid_entity_id?: number;
  }) => Promise<Transfer>;
}

export const useTransferStore = create<TransferState>((set, get) => ({
  transfers: [],
  currentTransfer: null,
  stats: null,
  isLoading: false,
  error: null,
  pagination: { page: 1, perPage: 20, total: 0, pages: 0 },

  fetchTransfers: async (filters) => {
    set({ isLoading: true, error: null });
    try {
      const resp = await transfersApi.list({
        status: filters?.status,
        category: filters?.category,
        search: filters?.search,
        page: filters?.page ?? get().pagination.page,
        per_page: filters?.per_page ?? get().pagination.perPage,
      });
      set({
        transfers: resp.items,
        pagination: {
          page: resp.page,
          perPage: resp.per_page,
          total: resp.total,
          pages: resp.pages,
        },
        isLoading: false,
      });
    } catch {
      set({ error: "Failed to fetch transfers", isLoading: false });
    }
  },

  fetchTransfer: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const transfer = await transfersApi.get(id);
      set({ currentTransfer: transfer, isLoading: false });
    } catch {
      set({ error: "Failed to fetch transfer", isLoading: false });
    }
  },

  fetchStats: async () => {
    try {
      const stats = await transfersApi.stats();
      set({ stats });
    } catch {
      // Non-critical — don't set loading state
    }
  },

  createTransfer: async (data) => {
    const transfer = await transfersApi.create(data);
    await get().fetchTransfers();
    return transfer;
  },
}));
