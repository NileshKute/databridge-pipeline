import { useState, type FormEvent } from "react";
import { X, Check, AlertTriangle, Loader2 } from "lucide-react";
import { clsx } from "clsx";

interface Props {
  mode: "approve" | "reject";
  transferName: string;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (text: string) => Promise<void>;
}

export default function ApprovalModal({
  mode,
  transferName,
  isOpen,
  onClose,
  onConfirm,
}: Props) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const isApprove = mode === "approve";
  const canSubmit = isApprove || text.trim().length >= 10;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!isApprove && text.trim().length < 10) {
      setError("Reason must be at least 10 characters");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await onConfirm(text.trim());
      setText("");
      onClose();
    } catch {
      setError("Action failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (loading) return;
    setText("");
    setError("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-bg-card border border-surface-700 rounded-xl shadow-2xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-700">
          <div className="flex items-center gap-2">
            {isApprove ? (
              <Check className="w-5 h-5 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-accent-rose" />
            )}
            <h3 className="text-base font-semibold text-text-primary">
              {isApprove ? "Approve Transfer" : "Reject Transfer"}
            </h3>
          </div>
          <button
            onClick={handleClose}
            className="p-1 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit}>
          <div className="px-5 py-4 space-y-4">
            <p className="text-sm text-text-secondary">
              {isApprove
                ? "You are approving"
                : "You are rejecting"}{" "}
              <span className="font-medium text-text-primary">
                {transferName}
              </span>
            </p>

            <div>
              <label className="block text-xs font-medium text-text-muted mb-1.5 uppercase tracking-wider">
                {isApprove ? "Comment (optional)" : "Reason (required)"}
              </label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={3}
                placeholder={
                  isApprove
                    ? "Add an optional comment..."
                    : "Please provide a detailed reason (min 10 characters)..."
                }
                className="input-field resize-none text-sm"
              />
              {!isApprove && text.length > 0 && text.length < 10 && (
                <p className="text-xs text-accent-rose mt-1">
                  {10 - text.length} more character{10 - text.length !== 1 ? "s" : ""} required
                </p>
              )}
            </div>

            {error && (
              <div className="bg-rose-950/50 border border-rose-800 rounded-lg p-2.5 text-accent-rose text-xs">
                {error}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-surface-700">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="btn-secondary text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !canSubmit}
              className={clsx(
                "flex items-center gap-1.5 font-medium py-2 px-4 rounded-lg text-sm text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed",
                isApprove
                  ? "bg-emerald-600 hover:bg-emerald-700"
                  : "bg-rose-600 hover:bg-rose-700",
              )}
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : isApprove ? (
                <Check className="w-4 h-4" />
              ) : (
                <X className="w-4 h-4" />
              )}
              {isApprove ? "Approve" : "Reject"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
