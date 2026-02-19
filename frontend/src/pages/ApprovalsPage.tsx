import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle, Eye, FolderSync } from "lucide-react";
import toast from "react-hot-toast";
import PageHeader from "@/components/common/PageHeader";
import StatusBadge from "@/components/common/StatusBadge";
import PriorityBadge from "@/components/common/PriorityBadge";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import ApprovalModal from "@/components/approvals/ApprovalModal";
import { useApprovalStore } from "@/store/approvalStore";
import { formatRelativeTime } from "@/utils/formatters";
import type { Transfer } from "@/types";

export default function ApprovalsPage() {
  const navigate = useNavigate();
  const { pendingApprovals, pendingCount, isLoading, fetchPending, approve, reject } =
    useApprovalStore();

  const [modalTransfer, setModalTransfer] = useState<Transfer | null>(null);
  const [modalMode, setModalMode] = useState<"approve" | "reject">("approve");

  useEffect(() => {
    fetchPending();
  }, [fetchPending]);

  const openModal = (transfer: Transfer, mode: "approve" | "reject") => {
    setModalTransfer(transfer);
    setModalMode(mode);
  };

  const handleConfirm = async (text: string) => {
    if (!modalTransfer) return;
    if (modalMode === "approve") {
      await approve(modalTransfer.id, text || undefined);
      toast.success("Transfer approved");
    } else {
      await reject(modalTransfer.id, text);
      toast.success("Transfer rejected");
    }
  };

  return (
    <div>
      <PageHeader
        title="My Approvals"
        subtitle={`${pendingCount} pending approval${pendingCount !== 1 ? "s" : ""}`}
      />

      {isLoading ? (
        <div className="py-16">
          <LoadingSpinner />
        </div>
      ) : pendingApprovals.length === 0 ? (
        <EmptyState
          title="All caught up!"
          description="No transfers are waiting for your approval"
          icon={CheckCircle}
        />
      ) : (
        <div className="bg-bg-card border border-surface-700 rounded-xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-700 text-text-muted">
                <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
                  File / Package
                </th>
                <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
                  Artist
                </th>
                <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
                  Status
                </th>
                <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
                  Priority
                </th>
                <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
                  Submitted
                </th>
                <th className="text-right py-3 px-4 font-medium text-xs uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {pendingApprovals.map((t) => (
                <tr
                  key={t.id}
                  className="border-b border-surface-800 hover:bg-bg-card-hover/50 transition-colors"
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
                        <p className="text-text-muted text-xs">{t.reference}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-text-secondary text-sm">
                    {t.artist_name}
                  </td>
                  <td className="py-3 px-4">
                    <StatusBadge status={t.status} />
                  </td>
                  <td className="py-3 px-4">
                    <PriorityBadge priority={t.priority} />
                  </td>
                  <td className="py-3 px-4 text-text-muted text-xs whitespace-nowrap">
                    {formatRelativeTime(t.created_at)}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => navigate(`/transfers/${t.id}`)}
                        className="p-1.5 rounded-lg text-text-muted hover:text-accent-cyan hover:bg-cyan-950/30 transition-colors"
                        title="View"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => openModal(t, "approve")}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-950/60 text-emerald-300 hover:bg-emerald-900/60 transition-colors"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => openModal(t, "reject")}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium bg-rose-950/60 text-rose-300 hover:bg-rose-900/60 transition-colors"
                      >
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ApprovalModal
        mode={modalMode}
        transferName={modalTransfer?.name ?? ""}
        isOpen={!!modalTransfer}
        onClose={() => setModalTransfer(null)}
        onConfirm={handleConfirm}
      />
    </div>
  );
}
