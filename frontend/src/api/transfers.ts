import apiClient from "./client";
import type {
  PaginatedResponse,
  Transfer,
  TransferListItem,
} from "@/types";

interface TransferCreatePayload {
  project_id: number;
  title: string;
  description?: string;
  priority?: string;
  source_path: string;
  destination_path: string;
  shotgrid_task_id?: number;
  shotgrid_version_id?: number;
}

interface TransferListParams {
  project_id?: number;
  status?: string;
  page?: number;
  page_size?: number;
}

export const transfersApi = {
  list: async (params: TransferListParams = {}): Promise<PaginatedResponse<TransferListItem>> => {
    const { data } = await apiClient.get<PaginatedResponse<TransferListItem>>("/transfers/", { params });
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

  approve: async (id: number): Promise<Transfer> => {
    const { data } = await apiClient.post<Transfer>(`/transfers/${id}/approve`);
    return data;
  },

  start: async (id: number): Promise<Transfer> => {
    const { data } = await apiClient.post<Transfer>(`/transfers/${id}/start`);
    return data;
  },

  cancel: async (id: number): Promise<{ message: string }> => {
    const { data } = await apiClient.post<{ message: string }>(`/transfers/${id}/cancel`);
    return data;
  },
};
