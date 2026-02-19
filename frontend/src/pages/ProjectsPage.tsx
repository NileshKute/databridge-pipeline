import { useEffect } from "react";
import { FolderKanban } from "lucide-react";
import StatusBadge from "@/components/common/StatusBadge";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import EmptyState from "@/components/common/EmptyState";
import { useProjectStore } from "@/store/projectStore";
import { formatDate } from "@/utils/format";

export default function ProjectsPage() {
  const { projects, isLoading, fetchProjects } = useProjectStore();

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-surface-100">Projects</h1>
        <p className="text-surface-400 mt-1">Studio projects configured for data transfers.</p>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : projects.length === 0 ? (
        <EmptyState
          title="No projects"
          description="No projects have been configured yet."
          icon={FolderKanban}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <div key={project.id} className="card hover:border-surface-600 transition-colors">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-surface-200">{project.name}</h3>
                  <p className="text-sm font-mono text-surface-400">{project.code}</p>
                </div>
                <StatusBadge status={project.status} />
              </div>
              {project.description && (
                <p className="text-sm text-surface-400 mb-3 line-clamp-2">{project.description}</p>
              )}
              <div className="space-y-1.5 text-xs text-surface-500">
                <p className="font-mono truncate" title={project.staging_path}>
                  Staging: {project.staging_path}
                </p>
                <p className="font-mono truncate" title={project.production_path}>
                  Prod: {project.production_path}
                </p>
                <p>Created: {formatDate(project.created_at)}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
