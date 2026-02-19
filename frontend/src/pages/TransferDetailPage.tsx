import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  Play,
  XCircle,
  FileText,
  HardDrive,
} from "lucide-react";
import toast from "react-hot-toast";
import StatusBadge from "@/components/common/StatusBadge";
import PriorityBadge from "@/components/common/PriorityBadge";
import ProgressBar from "@/components/common/ProgressBar";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import { useTransferStore } from "@/store/transferStore";
import { useAuthStore } from "@/store/authStore";
import { formatBytes, formatDate } from "@/utils/format";
import { usePolling } from "@/hooks/usePolling";

export default function TransferDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const {
    currentTransfer: transfer,
    fetchTransfer,
    approveTransfer,
    startTransfer,
    cancelTransfer,
    isLoading,
  } = useTransferStore();

  const transferId = Number(id);
  const isActive = transfer?.status === "in_progress" || transfer?.status === "checksumming";
  const canApprove =
    transfer?.status === "pending" &&
    user &&
    ["lead", "supervisor", "producer", "admin"].includes(user.role);
  const canStart = transfer?.status === "approved" && canApprove;
  const canCancel =
    transfer &&
    !["completed", "cancelled", "failed"].includes(transfer.status);

  useEffect(() => {
    fetchTransfer(transferId);
  }, [fetchTransfer, transferId]);

  usePolling(() => fetchTransfer(transferId), 3000, isActive);

  const handleApprove = async () => {
    try {
      await approveTransfer(transferId);
      toast.success("Transfer approved");
    } catch {
      toast.error("Failed to approve");
    }
  };

  const handleStart = async () => {
    try {
      await startTransfer(transferId);
      toast.success("Transfer started");
    } catch {
      toast.error("Failed to start transfer");
    }
  };

  const handleCancel = async () => {
    try {
      await cancelTransfer(transferId);
      toast.success("Transfer cancelled");
      navigate("/transfers");
    } catch {
      toast.error("Failed to cancel");
    }
  };

  if (isLoading || !transfer) return <LoadingSpinner size="lg" className="mt-20" />;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate("/transfers")} className="p-2 hover:bg-surface-800 rounded-lg transition-colors">
          <ArrowLeft className="h-5 w-5 text-surface-400" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-surface-100">{transfer.title}</h1>
            <StatusBadge status={transfer.status} />
            <PriorityBadge priority={transfer.priority} />
          </div>
          <p className="text-surface-400 font-mono text-sm mt-1">{transfer.reference_id}</p>
        </div>
        <div className="flex gap-2">
          {canApprove && (
            <button onClick={handleApprove} className="btn-primary flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" /> Approve
            </button>
          )}
          {canStart && (
            <button onClick={handleStart} className="btn-primary flex items-center gap-2">
              <Play className="h-4 w-4" /> Start Transfer
            </button>
          )}
          {canCancel && (
            <button onClick={handleCancel} className="btn-danger flex items-center gap-2">
              <XCircle className="h-4 w-4" /> Cancel
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-surface-200 mb-4">Transfer Progress</h2>
            <ProgressBar percent={transfer.progress_percent} className="mb-3" />
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-surface-100">{transfer.file_count}</p>
                <p className="text-xs text-surface-400">Total Files</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-surface-100">{formatBytes(transfer.transferred_bytes)}</p>
                <p className="text-xs text-surface-400">Transferred</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-surface-100">{formatBytes(transfer.total_size_bytes)}</p>
                <p className="text-xs text-surface-400">Total Size</p>
              </div>
            </div>
          </div>

          {transfer.error_message && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
              <p className="text-red-400 text-sm font-medium">Error</p>
              <p className="text-red-300 text-sm mt-1">{transfer.error_message}</p>
            </div>
          )}

          <div className="card">
            <h2 className="text-lg font-semibold text-surface-200 mb-4">
              <FileText className="inline h-5 w-5 mr-2 text-brand-400" />
              Files ({transfer.files.length})
            </h2>
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-surface-800">
                  <tr className="border-b border-surface-700 text-surface-400">
                    <th className="text-left py-2 px-3 font-medium">Path</th>
                    <th className="text-left py-2 px-3 font-medium">Size</th>
                    <th className="text-left py-2 px-3 font-medium">Checksum</th>
                    <th className="text-left py-2 px-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {transfer.files.map((f) => (
                    <tr key={f.id} className="border-b border-surface-800">
                      <td className="py-2 px-3 font-mono text-xs text-surface-300 max-w-xs truncate">
                        {f.relative_path}
                      </td>
                      <td className="py-2 px-3 text-surface-400 tabular-nums text-xs">
                        {formatBytes(f.file_size_bytes)}
                      </td>
                      <td className="py-2 px-3">
                        {f.checksum_verified === true && (
                          <span className="text-emerald-400 text-xs">Verified</span>
                        )}
                        {f.checksum_verified === false && (
                          <span className="text-red-400 text-xs">Mismatch</span>
                        )}
                        {f.checksum_verified === null && (
                          <span className="text-surface-500 text-xs">Pending</span>
                        )}
                      </td>
                      <td className="py-2 px-3">
                        {f.transferred ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                        ) : (
                          <span className="text-surface-500 text-xs">Waiting</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card space-y-4">
            <h2 className="text-lg font-semibold text-surface-200">Details</h2>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-surface-400">Source</dt>
                <dd className="text-surface-200 font-mono text-xs mt-0.5 flex items-center gap-1.5">
                  <HardDrive className="h-3.5 w-3.5 text-surface-500" />
                  {transfer.source_path}
                </dd>
              </div>
              <div>
                <dt className="text-surface-400">Destination</dt>
                <dd className="text-surface-200 font-mono text-xs mt-0.5 flex items-center gap-1.5">
                  <HardDrive className="h-3.5 w-3.5 text-surface-500" />
                  {transfer.destination_path}
                </dd>
              </div>
              {transfer.description && (
                <div>
                  <dt className="text-surface-400">Description</dt>
                  <dd className="text-surface-300 mt-0.5">{transfer.description}</dd>
                </div>
              )}
              <div>
                <dt className="text-surface-400">Created</dt>
                <dd className="text-surface-300">{formatDate(transfer.created_at)}</dd>
              </div>
              {transfer.started_at && (
                <div>
                  <dt className="text-surface-400">Started</dt>
                  <dd className="text-surface-300">{formatDate(transfer.started_at)}</dd>
                </div>
              )}
              {transfer.completed_at && (
                <div>
                  <dt className="text-surface-400">Completed</dt>
                  <dd className="text-surface-300">{formatDate(transfer.completed_at)}</dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}
