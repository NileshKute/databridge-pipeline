import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import toast from "react-hot-toast";
import { transfersApi } from "@/api/transfers";
import { useProjectStore } from "@/store/projectStore";

export default function NewTransferPage() {
  const navigate = useNavigate();
  const { projects, fetchProjects } = useProjectStore();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [form, setForm] = useState({
    project_id: "",
    title: "",
    description: "",
    priority: "normal",
    source_path: "",
    destination_path: "",
  });

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const transfer = await transfersApi.create({
        ...form,
        project_id: Number(form.project_id),
      });
      toast.success(`Transfer ${transfer.reference_id} created`);
      navigate(`/transfers/${transfer.id}`);
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Failed to create transfer";
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate("/transfers")} className="p-2 hover:bg-surface-800 rounded-lg transition-colors">
          <ArrowLeft className="h-5 w-5 text-surface-400" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-surface-100">New Transfer</h1>
          <p className="text-surface-400 mt-1">Create a new data transfer request.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-5">
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-1.5">Project</label>
          <select name="project_id" value={form.project_id} onChange={handleChange} className="input-field" required>
            <option value="">Select a project</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.code})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-surface-300 mb-1.5">Title</label>
          <input
            name="title"
            value={form.title}
            onChange={handleChange}
            className="input-field"
            placeholder="e.g., Shot 010 final comp delivery"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-surface-300 mb-1.5">Description</label>
          <textarea
            name="description"
            value={form.description}
            onChange={handleChange}
            className="input-field min-h-[80px] resize-y"
            placeholder="Optional description..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-surface-300 mb-1.5">Priority</label>
          <select name="priority" value={form.priority} onChange={handleChange} className="input-field">
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-surface-300 mb-1.5">Source Path (Staging)</label>
          <input
            name="source_path"
            value={form.source_path}
            onChange={handleChange}
            className="input-field font-mono text-sm"
            placeholder="/mnt/staging/PROJECT/shots/010/comp/v005"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-surface-300 mb-1.5">Destination Path (Production)</label>
          <input
            name="destination_path"
            value={form.destination_path}
            onChange={handleChange}
            className="input-field font-mono text-sm"
            placeholder="/mnt/production/PROJECT/shots/010/comp/v005"
            required
          />
        </div>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={isSubmitting} className="btn-primary">
            {isSubmitting ? "Creating..." : "Create Transfer"}
          </button>
          <button type="button" onClick={() => navigate("/transfers")} className="btn-secondary">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
