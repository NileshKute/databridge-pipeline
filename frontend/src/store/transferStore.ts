import { create } from "zustand";
import { transfersApi } from "@/api/transfers";
import type { Transfer, TransferListItem } from "@/types";

interface TransferState {
  transfers: TransferListItem[];
  currentTransfer: Transfer | null;
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  isLoading: boolean;
  error: string | null;
  fetchTransfers: (params?: { project_id?: number; status?: string; page?: number }) => Promise<void>;
  fetchTransfer: (id: number) => Promise<void>;
  approveTransfer: (id: number) => Promise<void>;
  startTransfer: (id: number) => Promise<void>;
  cancelTransfer: (id: number) => Promise<void>;
}

export const useTransferStore = create<TransferState>((set, get) => ({
  transfers: [],
  currentTransfer: null,
  total: 0,
  page: 1,
  pageSize: 25,
  totalPages: 0,
  isLoading: false,
  error: null,

  fetchTransfers: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const response = await transfersApi.list({
        page: params?.page ?? get().page,
        page_size: get().pageSize,
        project_id: params?.project_id,
        status: params?.status,
      });
      set({
        transfers: response.items,
        total: response.total,
        page: response.page,
        totalPages: response.total_pages,
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

  approveTransfer: async (id) => {
    const transfer = await transfersApi.approve(id);
    set({ currentTransfer: transfer });
    await get().fetchTransfers();
  },

  startTransfer: async (id) => {
    const transfer = await transfersApi.start(id);
    set({ currentTransfer: transfer });
    await get().fetchTransfers();
  },

  cancelTransfer: async (id) => {
    await transfersApi.cancel(id);
    await get().fetchTransfers();
  },
}));
