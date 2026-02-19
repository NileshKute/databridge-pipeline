import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, Send } from "lucide-react";
import { clsx } from "clsx";
import toast from "react-hot-toast";
import PageHeader from "@/components/common/PageHeader";
import FileUploader from "@/components/upload/FileUploader";
import ShotGridLinker, {
  type ShotGridSelection,
} from "@/components/upload/ShotGridLinker";
import { transfersApi } from "@/api/transfers";
import apiClient from "@/api/client";
import { CATEGORY_OPTIONS, PRIORITY_OPTIONS } from "@/utils/constants";

export default function UploadPage() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);

  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("normal");
  const [notes, setNotes] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [sg, setSg] = useState<ShotGridSelection>({
    projectId: null,
    entityType: "Shot",
    entityId: null,
    entityName: null,
  });

  const canSubmit = name.trim().length > 0 && files.length > 0 && !submitting;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    try {
      const transfer = await transfersApi.create({
        name: name.trim(),
        category: category || undefined,
        priority,
        notes: notes.trim() || undefined,
        shotgrid_project_id: sg.projectId ?? undefined,
        shotgrid_entity_type: sg.entityId ? sg.entityType : undefined,
        shotgrid_entity_id: sg.entityId ?? undefined,
      });

      await transfersApi.uploadFiles(transfer.id, files);

      if (sg.entityId && sg.projectId) {
        try {
          await apiClient.post("/shotgrid/link", {
            transfer_id: transfer.id,
            entity_type: sg.entityType,
            entity_id: sg.entityId,
          });
        } catch {
          // SG linking is non-critical
        }
      }

      toast.success("Transfer submitted to pipeline!");
      navigate(`/transfers/${transfer.id}`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Failed to create transfer";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Upload"
        subtitle="Create a new transfer and upload files to the pipeline"
      />

      <form onSubmit={handleSubmit} className="max-w-[640px] space-y-6">
        {/* Package name */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1.5">
            Package Name <span className="text-accent-rose">*</span>
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Shot_010_comp_v003"
            className="input-field"
            required
          />
        </div>

        {/* Category + Priority row */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1.5">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="input-field text-sm"
            >
              <option value="">Select category...</option>
              {CATEGORY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1.5">
              Priority
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className={clsx(
                "input-field text-sm",
                priority === "urgent" && "text-accent-rose border-rose-700",
              )}
            >
              {PRIORITY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* ShotGrid Linking */}
        <ShotGridLinker value={sg} onChange={setSg} />

        {/* File upload */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1.5">
            Files <span className="text-accent-rose">*</span>
          </label>
          <FileUploader files={files} onChange={setFiles} />
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1.5">
            Notes
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            placeholder="Any notes for the reviewers..."
            className="input-field resize-none text-sm"
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={!canSubmit}
          className="w-full py-3 rounded-lg font-medium text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 flex items-center justify-center gap-2"
        >
          {submitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Submitting...
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              Submit to Pipeline
            </>
          )}
        </button>
      </form>
    </div>
  );
}
