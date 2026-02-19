import apiClient from "./client";
import type { Transfer, TransferListResponse, TransferStats } from "@/types";

interface TransferCreatePayload {
  name: string;
  category?: string;
  priority?: string;
  notes?: string;
  shotgrid_project_id?: number;
  shotgrid_entity_type?: string;
  shotgrid_entity_id?: number;
}

interface TransferListParams {
  status?: string;
  category?: string;
  search?: string;
  page?: number;
  per_page?: number;
}

export const transfersApi = {
  list: async (params: TransferListParams = {}): Promise<TransferListResponse> => {
    const { data } = await apiClient.get<TransferListResponse>("/transfers/", { params });
    return data;
  },

  get: async (id: number): Promise<Transfer> => {
    const { data } = await apiClient.get<Transfer>(`/transfers/${id}`);
    return data;
  },

  create: async (payload: TransferCreatePayload): Promise<Transfer> => {
    const { data } = await apiClient.post<Transfer>("/transfers/", payload);
    return data;
  },

  update: async (id: number, payload: Partial<TransferCreatePayload>): Promise<Transfer> => {
    const { data } = await apiClient.put<Transfer>(`/transfers/${id}`, payload);
    return data;
  },

  cancel: async (id: number): Promise<{ message: string }> => {
    const { data } = await apiClient.delete<{ message: string }>(`/transfers/${id}`);
    return data;
  },

  stats: async (): Promise<TransferStats> => {
    const { data } = await apiClient.get<TransferStats>("/transfers/stats");
    return data;
  },

  uploadFiles: async (id: number, files: File[]): Promise<unknown> => {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    const { data } = await apiClient.post(`/transfers/${id}/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
};
