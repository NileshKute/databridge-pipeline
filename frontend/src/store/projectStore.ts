import { create } from "zustand";
import { projectsApi } from "@/api/projects";
import type { Project } from "@/types";

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  isLoading: boolean;
  error: string | null;
  fetchProjects: () => Promise<void>;
  fetchProject: (id: number) => Promise<void>;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  currentProject: null,
  isLoading: false,
  error: null,

  fetchProjects: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await projectsApi.list();
      set({ projects: response.items, isLoading: false });
    } catch {
      set({ error: "Failed to fetch projects", isLoading: false });
    }
  },

  fetchProject: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const project = await projectsApi.get(id);
      set({ currentProject: project, isLoading: false });
    } catch {
      set({ error: "Failed to fetch project", isLoading: false });
    }
  },
}));
