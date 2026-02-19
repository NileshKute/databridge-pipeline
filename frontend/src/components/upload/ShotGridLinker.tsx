import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp, Film, Box, Loader2 } from "lucide-react";
import { clsx } from "clsx";
import apiClient from "@/api/client";

interface SGProject {
  id: number;
  name: string;
  [key: string]: unknown;
}

interface SGEntity {
  id: number;
  code?: string;
  name?: string;
  [key: string]: unknown;
}

export interface ShotGridSelection {
  projectId: number | null;
  entityType: "Shot" | "Asset";
  entityId: number | null;
  entityName: string | null;
}

interface Props {
  value: ShotGridSelection;
  onChange: (v: ShotGridSelection) => void;
}

export default function ShotGridLinker({ value, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [projects, setProjects] = useState<SGProject[]>([]);
  const [entities, setEntities] = useState<SGEntity[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [loadingEntities, setLoadingEntities] = useState(false);

  useEffect(() => {
    if (!open || projects.length > 0) return;
    setLoadingProjects(true);
    apiClient
      .get<SGProject[]>("/shotgrid/projects")
      .then(({ data }) => setProjects(data))
      .catch(() => setProjects([]))
      .finally(() => setLoadingProjects(false));
  }, [open, projects.length]);

  useEffect(() => {
    if (!value.projectId) {
      setEntities([]);
      return;
    }
    setLoadingEntities(true);
    const endpoint =
      value.entityType === "Shot"
        ? `/shotgrid/projects/${value.projectId}/shots`
        : `/shotgrid/projects/${value.projectId}/assets`;
    apiClient
      .get<SGEntity[]>(endpoint)
      .then(({ data }) => setEntities(data))
      .catch(() => setEntities([]))
      .finally(() => setLoadingEntities(false));
  }, [value.projectId, value.entityType]);

  const handleProjectChange = (id: string) => {
    const pid = id ? Number(id) : null;
    onChange({ ...value, projectId: pid, entityId: null, entityName: null });
  };

  const handleTypeChange = (type: "Shot" | "Asset") => {
    onChange({ ...value, entityType: type, entityId: null, entityName: null });
  };

  const handleEntityChange = (id: string) => {
    const eid = id ? Number(id) : null;
    const entity = entities.find((e) => e.id === eid);
    const name = entity?.code ?? entity?.name ?? null;
    onChange({ ...value, entityId: eid, entityName: name });
  };

  const selectedEntity = entities.find((e) => e.id === value.entityId);

  return (
    <div className="border border-surface-700 rounded-xl overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full px-4 py-3 text-sm text-text-secondary hover:bg-bg-card-hover/30 transition-colors"
      >
        <span className="font-medium">ShotGrid Linking</span>
        <div className="flex items-center gap-2">
          {value.entityName && (
            <span className="text-xs text-accent-cyan">{value.entityName}</span>
          )}
          {open ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </div>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-4 border-t border-surface-700 pt-4">
          {/* Project */}
          <div>
            <label className="block text-xs font-medium text-text-muted mb-1.5 uppercase tracking-wider">
              Project
            </label>
            {loadingProjects ? (
              <div className="flex items-center gap-2 text-text-muted text-sm py-2">
                <Loader2 className="w-4 h-4 animate-spin" /> Loading projects...
              </div>
            ) : (
              <select
                value={value.projectId ?? ""}
                onChange={(e) => handleProjectChange(e.target.value)}
                className="input-field text-sm"
              >
                <option value="">Select a project...</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Entity type toggle */}
          {value.projectId && (
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1.5 uppercase tracking-wider">
                Entity Type
              </label>
              <div className="flex items-center bg-bg-secondary rounded-lg p-0.5 w-fit">
                <button
                  type="button"
                  onClick={() => handleTypeChange("Shot")}
                  className={clsx(
                    "flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium transition-colors",
                    value.entityType === "Shot"
                      ? "bg-accent-cyan/20 text-accent-cyan"
                      : "text-text-muted hover:text-text-secondary",
                  )}
                >
                  <Film className="w-4 h-4" /> Shot
                </button>
                <button
                  type="button"
                  onClick={() => handleTypeChange("Asset")}
                  className={clsx(
                    "flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium transition-colors",
                    value.entityType === "Asset"
                      ? "bg-accent-cyan/20 text-accent-cyan"
                      : "text-text-muted hover:text-text-secondary",
                  )}
                >
                  <Box className="w-4 h-4" /> Asset
                </button>
              </div>
            </div>
          )}

          {/* Entity selector */}
          {value.projectId && (
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1.5 uppercase tracking-wider">
                {value.entityType}
              </label>
              {loadingEntities ? (
                <div className="flex items-center gap-2 text-text-muted text-sm py-2">
                  <Loader2 className="w-4 h-4 animate-spin" /> Loading{" "}
                  {value.entityType.toLowerCase()}s...
                </div>
              ) : (
                <select
                  value={value.entityId ?? ""}
                  onChange={(e) => handleEntityChange(e.target.value)}
                  className="input-field text-sm"
                >
                  <option value="">
                    Select a {value.entityType.toLowerCase()}...
                  </option>
                  {entities.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.code ?? e.name ?? `#${e.id}`}
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          {/* Selected entity info card */}
          {selectedEntity && (
            <div className="bg-cyan-950/20 border border-cyan-800/40 rounded-lg p-3">
              <p className="text-xs text-text-muted uppercase tracking-wider mb-1">
                Linked {value.entityType}
              </p>
              <p className="text-sm font-medium text-accent-cyan">
                {selectedEntity.code ?? selectedEntity.name ?? `#${selectedEntity.id}`}
              </p>
              <p className="text-xs text-text-muted mt-0.5">
                ID: {selectedEntity.id}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
