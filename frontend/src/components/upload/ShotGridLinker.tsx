import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import apiClient from "@/api/client";

interface SGProject {
  id: number;
  name: string;
  sg_status?: string;
  [key: string]: unknown;
}

interface SGSequence {
  id: number;
  code: string;
  sg_status_list?: string;
  [key: string]: unknown;
}

interface SGShot {
  id: number;
  code: string;
  sg_sequence?: { id: number; name?: string };
  [key: string]: unknown;
}

interface SGTask {
  id: number;
  content: string;
  [key: string]: unknown;
}

export interface ShotGridSelection {
  projectId: number | null;
  projectName: string | null;
  sequenceId: number | null;
  sequenceCode: string | null;
  shotId: number | null;
  shotCode: string | null;
  taskId: number | null;
  taskName: string | null;
}

interface Props {
  value: ShotGridSelection;
  onChange: (v: ShotGridSelection) => void;
}

export default function ShotGridLinker({ value, onChange }: Props) {
  const [projects, setProjects] = useState<SGProject[]>([]);
  const [sequences, setSequences] = useState<SGSequence[]>([]);
  const [shots, setShots] = useState<SGShot[]>([]);
  const [tasks, setTasks] = useState<SGTask[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [loadingSequences, setLoadingSequences] = useState(false);
  const [loadingShots, setLoadingShots] = useState(false);
  const [loadingTasks, setLoadingTasks] = useState(false);

  useEffect(() => {
    setLoadingProjects(true);
    apiClient
      .get<{ projects: SGProject[] }>("/shotgrid/projects")
      .then(({ data }) => setProjects(data?.projects ?? []))
      .catch(() => setProjects([]))
      .finally(() => setLoadingProjects(false));
  }, []);

  useEffect(() => {
    if (!value.projectId) {
      setSequences([]);
      return;
    }
    setLoadingSequences(true);
    apiClient
      .get<{ sequences: SGSequence[] }>(`/shotgrid/projects/${value.projectId}/sequences`)
      .then(({ data }) => setSequences(data?.sequences ?? []))
      .catch(() => setSequences([]))
      .finally(() => setLoadingSequences(false));
  }, [value.projectId]);

  useEffect(() => {
    if (!value.projectId || !value.sequenceCode) {
      setShots([]);
      return;
    }
    setLoadingShots(true);
    apiClient
      .get<{ shots: SGShot[] }>(`/shotgrid/projects/${value.projectId}/shots`, {
        params: { sequence: value.sequenceCode },
      })
      .then(({ data }) => setShots(data?.shots ?? []))
      .catch(() => setShots([]))
      .finally(() => setLoadingShots(false));
  }, [value.projectId, value.sequenceCode]);

  useEffect(() => {
    if (!value.shotId) {
      setTasks([]);
      return;
    }
    setLoadingTasks(true);
    apiClient
      .get<{ tasks: SGTask[] }>(`/shotgrid/entities/Shot/${value.shotId}/tasks`)
      .then(({ data }) => setTasks(data?.tasks ?? []))
      .catch(() => setTasks([]))
      .finally(() => setLoadingTasks(false));
  }, [value.shotId]);

  const handleProjectChange = (id: string) => {
    const pid = id ? Number(id) : null;
    const project = projects.find((p) => p.id === pid);
    onChange({
      projectId: pid,
      projectName: project?.name ?? null,
      sequenceId: null,
      sequenceCode: null,
      shotId: null,
      shotCode: null,
      taskId: null,
      taskName: null,
    });
  };

  const handleSequenceChange = (id: string) => {
    const sid = id ? Number(id) : null;
    const seq = sequences.find((s) => s.id === sid);
    onChange({
      ...value,
      sequenceId: sid,
      sequenceCode: seq?.code ?? null,
      shotId: null,
      shotCode: null,
      taskId: null,
      taskName: null,
    });
  };

  const handleShotChange = (id: string) => {
    const shotId = id ? Number(id) : null;
    const shot = shots.find((s) => s.id === shotId);
    onChange({
      ...value,
      shotId,
      shotCode: shot?.code ?? null,
      taskId: null,
      taskName: null,
    });
  };

  const handleTaskChange = (id: string) => {
    const taskId = id ? Number(id) : null;
    const task = tasks.find((t) => t.id === taskId);
    onChange({
      ...value,
      taskId,
      taskName: task?.content ?? null,
    });
  };

  return (
    <div className="space-y-4 p-4 rounded-xl border border-surface-700 bg-surface-900/50">
      <p className="text-xs font-medium text-text-muted uppercase tracking-wider">
        ShotGrid — Project <span className="text-accent-rose">*</span>
      </p>

      {/* Project — required */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1.5">
          Project <span className="text-accent-rose">*</span>
        </label>
        {loadingProjects ? (
          <div className="flex items-center gap-2 text-text-muted text-sm py-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading projects...
          </div>
        ) : (
          <select
            value={value.projectId ?? ""}
            onChange={(e) => handleProjectChange(e.target.value)}
            className="input-field text-sm w-full"
            required
          >
            <option value="">Select project...</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} {p.sg_status ? `(${p.sg_status})` : ""}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Sequence */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1.5">
          Sequence
        </label>
        {!value.projectId ? (
          <p className="text-text-muted text-sm">Select a project first.</p>
        ) : loadingSequences ? (
          <div className="flex items-center gap-2 text-text-muted text-sm py-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading sequences...
          </div>
        ) : (
          <select
            value={value.sequenceId ?? ""}
            onChange={(e) => handleSequenceChange(e.target.value)}
            className="input-field text-sm w-full"
          >
            <option value="">Select sequence (optional)...</option>
            {sequences.map((s) => (
              <option key={s.id} value={s.id}>
                {s.code} {s.sg_status_list ? `(${s.sg_status_list})` : ""}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Shot */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1.5">
          Shot
        </label>
        {!value.projectId || !value.sequenceCode ? (
          <p className="text-text-muted text-sm">
            {!value.projectId ? "Select a project first." : "Select a sequence to filter shots."}
          </p>
        ) : loadingShots ? (
          <div className="flex items-center gap-2 text-text-muted text-sm py-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading shots...
          </div>
        ) : (
          <select
            value={value.shotId ?? ""}
            onChange={(e) => handleShotChange(e.target.value)}
            className="input-field text-sm w-full"
          >
            <option value="">Select shot (optional)...</option>
            {shots.map((s) => (
              <option key={s.id} value={s.id}>
                {s.code}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Task */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1.5">
          Task
        </label>
        {!value.shotId ? (
          <p className="text-text-muted text-sm">Select a shot first.</p>
        ) : loadingTasks ? (
          <div className="flex items-center gap-2 text-text-muted text-sm py-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading tasks...
          </div>
        ) : (
          <select
            value={value.taskId ?? ""}
            onChange={(e) => handleTaskChange(e.target.value)}
            className="input-field text-sm w-full"
          >
            <option value="">Select task (optional)...</option>
            {tasks.map((t) => (
              <option key={t.id} value={t.id}>
                {t.content}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Selected summary */}
      {(value.projectName || value.sequenceCode || value.shotCode) && (
        <div className="bg-primary-900/20 border border-primary-800/40 rounded-lg p-3">
          <p className="text-xs text-text-muted uppercase tracking-wider mb-1">
            Selected
          </p>
          <p className="text-sm text-primary-400">
            {value.projectName}
            {value.sequenceCode && ` → ${value.sequenceCode}`}
            {value.shotCode && ` → ${value.shotCode}`}
            {value.taskName && ` → ${value.taskName}`}
          </p>
        </div>
      )}
    </div>
  );
}
