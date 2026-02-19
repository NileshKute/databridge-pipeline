import { useNavigate } from "react-router-dom";
import { Eye, FolderSync } from "lucide-react";
import { clsx } from "clsx";
import StatusBadge from "@/components/common/StatusBadge";
import PriorityBadge from "@/components/common/PriorityBadge";
import ApprovalChain from "@/components/common/ApprovalChain";
import EmptyState from "@/components/common/EmptyState";
import { formatFileSize, formatRelativeTime } from "@/utils/formatters";
import { useRole } from "@/hooks/useAuth";
import type { Transfer } from "@/types";

interface Props {
  transfers: Transfer[];
  showCategory?: boolean;
  showApprovalActions?: boolean;
  onApprove?: (id: number) => void;
  onReject?: (id: number) => void;
  onProcess?: (id: number) => void;
}

export default function TransferTable({
  transfers,
  showCategory = false,
  showApprovalActions = false,
  onApprove,
  onReject,
  onProcess,
}: Props) {
  const navigate = useNavigate();
  const { canApprove, canProcess } = useRole();

  if (transfers.length === 0) {
    return (
      <EmptyState
        title="No transfers found"
        description="Try adjusting your filters"
        icon={FolderSync}
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-surface-700 text-text-muted">
            <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
              File / Package
            </th>
            {showCategory && (
              <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
                Category
              </th>
            )}
            <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
              Artist
            </th>
            <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
              Status
            </th>
            <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
              Approvals
            </th>
            <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
              Priority
            </th>
            <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
              Updated
            </th>
            <th className="text-right py-3 px-4 font-medium text-xs uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {transfers.map((t) => (
            <tr
              key={t.id}
              className="border-b border-surface-800 hover:bg-bg-card-hover/50 cursor-pointer transition-colors"
              onClick={() => navigate(`/transfers/${t.id}`)}
            >
              <td className="py-3 px-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-surface-800 flex items-center justify-center shrink-0">
                    <FolderSync className="w-4 h-4 text-accent-cyan" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-text-primary font-medium truncate max-w-[200px]">
                      {t.name}
                    </p>
                    <p className="text-text-muted text-xs">
                      {t.reference} &middot; {formatFileSize(t.total_size_bytes)}{" "}
                      &middot; {t.total_files} file{t.total_files !== 1 ? "s" : ""}
                    </p>
                  </div>
                </div>
              </td>
              {showCategory && (
                <td className="py-3 px-4 text-text-secondary text-xs capitalize">
                  {t.category?.replace(/_/g, " ") ?? "—"}
                </td>
              )}
              <td className="py-3 px-4 text-text-secondary text-sm">
                {t.artist_name}
              </td>
              <td className="py-3 px-4">
                <StatusBadge status={t.status} />
              </td>
              <td className="py-3 px-4">
                {t.approval_chain?.length > 0 ? (
                  <ApprovalChain approvals={t.approval_chain} compact />
                ) : (
                  <span className="text-text-muted text-xs">—</span>
                )}
              </td>
              <td className="py-3 px-4">
                <PriorityBadge priority={t.priority} />
              </td>
              <td className="py-3 px-4 text-text-muted text-xs whitespace-nowrap">
                {formatRelativeTime(t.updated_at)}
              </td>
              <td className="py-3 px-4 text-right">
                <div
                  className="flex items-center justify-end gap-2"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={() => navigate(`/transfers/${t.id}`)}
                    className="p-1.5 rounded-lg text-text-muted hover:text-accent-cyan hover:bg-cyan-950/30 transition-colors"
                    title="View"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  {showApprovalActions && canApprove(t.status) && onApprove && (
                    <button
                      onClick={() => onApprove(t.id)}
                      className={clsx(
                        "px-2.5 py-1 rounded-lg text-xs font-medium transition-colors",
                        "bg-emerald-950/60 text-emerald-300 hover:bg-emerald-900/60",
                      )}
                    >
                      Approve
                    </button>
                  )}
                  {showApprovalActions && canApprove(t.status) && onReject && (
                    <button
                      onClick={() => onReject(t.id)}
                      className={clsx(
                        "px-2.5 py-1 rounded-lg text-xs font-medium transition-colors",
                        "bg-rose-950/60 text-rose-300 hover:bg-rose-900/60",
                      )}
                    >
                      Reject
                    </button>
                  )}
                  {showApprovalActions && canProcess(t.status) && onProcess && (
                    <button
                      onClick={() => onProcess(t.id)}
                      className={clsx(
                        "px-2.5 py-1 rounded-lg text-xs font-medium transition-colors",
                        "bg-blue-950/60 text-blue-300 hover:bg-blue-900/60",
                      )}
                    >
                      Process
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
