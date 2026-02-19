import apiClient from "./client";
import type { PaginatedResponse, Project } from "@/types";

interface ProjectCreatePayload {
  name: string;
  code: string;
  description?: string;
  shotgrid_id?: number;
  staging_path: string;
  production_path: string;
}

export const projectsApi = {
  list: async (page = 1, pageSize = 50): Promise<PaginatedResponse<Project>> => {
    const { data } = await apiClient.get<PaginatedResponse<Project>>("/projects/", {
      params: { page, page_size: pageSize },
    });
    return data;
  },

  get: async (id: number): Promise<Project> => {
    const { data } = await apiClient.get<Project>(`/projects/${id}`);
    return data;
  },

  create: async (payload: ProjectCreatePayload): Promise<Project> => {
    const { data } = await apiClient.post<Project>("/projects/", payload);
    return data;
  },

  update: async (id: number, payload: Partial<ProjectCreatePayload>): Promise<Project> => {
    const { data } = await apiClient.patch<Project>(`/projects/${id}`, payload);
    return data;
  },
};
