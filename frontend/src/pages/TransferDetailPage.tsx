import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Check,
  X,
  Play,
  AlertTriangle,
  Clock,
  FolderSync,
  FileText,
  Shield,
  History,
} from "lucide-react";
import { clsx } from "clsx";
import toast from "react-hot-toast";
import PageHeader from "@/components/common/PageHeader";
import StatusBadge from "@/components/common/StatusBadge";
import PriorityBadge from "@/components/common/PriorityBadge";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import TransferFiles from "@/components/transfers/TransferFiles";
import TransferTimeline from "@/components/transfers/TransferTimeline";
import { useTransferStore } from "@/store/transferStore";
import { useApprovalStore } from "@/store/approvalStore";
import { useRole } from "@/hooks/useAuth";
import {
  formatFileSize,
  formatDate,
  formatDateTime,
  formatRelativeTime,
} from "@/utils/formatters";
import { ROLE_CONFIG, CATEGORY_OPTIONS } from "@/utils/constants";
import apiClient from "@/api/client";
import type { HistoryEntry, ApprovalChainItem } from "@/types";

export default function TransferDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentTransfer: transfer, isLoading, fetchTransfer } =
    useTransferStore();
  const { approve, reject } = useApprovalStore();
  const { canApprove, canProcess } = useRole();

  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    const tid = Number(id);
    fetchTransfer(tid);
    setHistoryLoading(true);
    apiClient
      .get<{ items: HistoryEntry[] }>("/activity/", {
        params: { transfer_id: tid, per_page: 50 },
      })
      .then(({ data }) => setHistory(data.items))
      .catch(() => setHistory([]))
      .finally(() => setHistoryLoading(false));
  }, [id, fetchTransfer]);

  if (isLoading || !transfer) {
    return (
      <div className="py-24">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const handleApprove = async () => {
    const comment = window.prompt("Approval comment (optional):");
    try {
      await approve(transfer.id, comment ?? undefined);
      toast.success("Transfer approved");
      fetchTransfer(transfer.id);
    } catch {
      toast.error("Failed to approve");
    }
  };

  const handleReject = async () => {
    const reason = window.prompt("Rejection reason (required):");
    if (!reason) return;
    try {
      await reject(transfer.id, reason);
      toast.success("Transfer rejected");
      fetchTransfer(transfer.id);
    } catch {
      toast.error("Failed to reject");
    }
  };

  const categoryLabel =
    CATEGORY_OPTIONS.find((c) => c.value === transfer.category)?.label ??
    transfer.category ??
    "—";

  return (
    <div>
      {/* Back + Header */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1.5 text-text-muted hover:text-text-primary text-sm mb-4 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      <PageHeader title={transfer.name} subtitle={`Transfer ${transfer.reference}`}>
        <StatusBadge status={transfer.status} />
        <PriorityBadge priority={transfer.priority} />
        {canApprove(transfer.status) && (
          <>
            <button
              onClick={handleApprove}
              className="btn-primary flex items-center gap-1.5 text-sm bg-emerald-600 hover:bg-emerald-700"
            >
              <Check className="w-4 h-4" /> Approve
            </button>
            <button
              onClick={handleReject}
              className="btn-danger flex items-center gap-1.5 text-sm"
            >
              <X className="w-4 h-4" /> Reject
            </button>
          </>
        )}
        {canProcess(transfer.status) && (
          <button className="btn-primary flex items-center gap-1.5 text-sm">
            <Play className="w-4 h-4" /> Process
          </button>
        )}
      </PageHeader>

      {/* Info Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <InfoCard title="Transfer Details" icon={FileText}>
          <InfoRow label="ID" value={`#${transfer.id}`} />
          <InfoRow label="Reference" value={transfer.reference} mono />
          <InfoRow label="Category" value={categoryLabel} />
          <InfoRow label="Artist" value={transfer.artist_name} />
          <InfoRow
            label="Size"
            value={formatFileSize(transfer.total_size_bytes)}
          />
          <InfoRow
            label="Files"
            value={`${transfer.total_files} file${transfer.total_files !== 1 ? "s" : ""}`}
          />
          <InfoRow label="Created" value={formatDateTime(transfer.created_at)} />
          <InfoRow label="Updated" value={formatRelativeTime(transfer.updated_at)} />
          {transfer.notes && <InfoRow label="Notes" value={transfer.notes} />}
        </InfoCard>

        <InfoCard title="ShotGrid & Paths" icon={FolderSync}>
          <InfoRow
            label="ShotGrid Project"
            value={
              transfer.shotgrid_project_id
                ? `#${transfer.shotgrid_project_id}`
                : "Not linked"
            }
          />
          <InfoRow
            label="Entity Type"
            value={transfer.shotgrid_entity_type ?? "—"}
          />
          <InfoRow
            label="Entity Name"
            value={transfer.shotgrid_entity_name ?? "Not linked"}
          />
          <InfoRow
            label="Staging Path"
            value={transfer.staging_path ?? "—"}
            mono
          />
          <InfoRow
            label="Production Path"
            value={transfer.production_path ?? "—"}
            mono
          />
          <InfoRow
            label="Transfer Method"
            value={transfer.transfer_method ?? "—"}
          />
          {transfer.transfer_started_at && (
            <InfoRow
              label="Transfer Started"
              value={formatDateTime(transfer.transfer_started_at)}
            />
          )}
          {transfer.transfer_completed_at && (
            <InfoRow
              label="Transfer Completed"
              value={formatDateTime(transfer.transfer_completed_at)}
            />
          )}
        </InfoCard>
      </div>

      {/* Approval Chain */}
      {transfer.approval_chain?.length > 0 && (
        <div className="mt-6">
          <SectionCard title="Approval Chain" icon={Shield}>
            <DetailedApprovalChain chain={transfer.approval_chain} />
          </SectionCard>
        </div>
      )}

      {/* Rejection card */}
      {transfer.status === "rejected" && transfer.rejection_reason && (
        <div className="mt-6 bg-rose-950/30 border border-rose-800/50 rounded-xl p-5">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-accent-rose shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-accent-rose">
                Transfer Rejected
              </h4>
              <p className="text-sm text-rose-200/80 mt-1">
                {transfer.rejection_reason}
              </p>
              {transfer.approval_chain
                ?.filter((a) => a.status === "rejected")
                .map((a, i) => (
                  <p key={i} className="text-xs text-rose-300/60 mt-2">
                    By {a.approver_name ?? "Unknown"} ({ROLE_CONFIG[a.role]?.label ?? a.role})
                    {a.decided_at && ` on ${formatDate(a.decided_at)}`}
                  </p>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* Files */}
      <div className="mt-6">
        <SectionCard title={`Files (${transfer.total_files})`} icon={FileText}>
          <TransferFiles files={transfer.files ?? []} />
        </SectionCard>
      </div>

      {/* Timeline */}
      <div className="mt-6">
        <SectionCard title="Activity Timeline" icon={History}>
          {historyLoading ? (
            <LoadingSpinner size="sm" className="py-8" />
          ) : (
            <TransferTimeline entries={history} />
          )}
        </SectionCard>
      </div>
    </div>
  );
}

/* ---------- sub-components ---------- */

function InfoCard({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-bg-card border border-surface-700 rounded-xl">
      <div className="flex items-center gap-2 px-5 py-3.5 border-b border-surface-700">
        <Icon className="w-4 h-4 text-text-muted" />
        <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">
          {title}
        </h3>
      </div>
      <div className="px-5 py-3 divide-y divide-surface-800">{children}</div>
    </div>
  );
}

function SectionCard({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-bg-card border border-surface-700 rounded-xl">
      <div className="flex items-center gap-2 px-5 py-3.5 border-b border-surface-700">
        <Icon className="w-4 h-4 text-text-muted" />
        <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">
          {title}
        </h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function InfoRow({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start justify-between py-2.5 gap-4">
      <span className="text-xs text-text-muted uppercase tracking-wider shrink-0 pt-0.5">
        {label}
      </span>
      <span
        className={clsx(
          "text-sm text-text-primary text-right break-all",
          mono && "font-mono text-xs",
        )}
      >
        {value}
      </span>
    </div>
  );
}

function DetailedApprovalChain({ chain }: { chain: ApprovalChainItem[] }) {
  return (
    <div className="flex flex-wrap items-start gap-3">
      {chain.map((item, i) => {
        const roleLabel = ROLE_CONFIG[item.role]?.label ?? item.role;
        const isApproved = item.status === "approved";
        const isRejected = item.status === "rejected";
        const isSkipped = item.status === "skipped";
        const isPending = item.status === "pending";
        const isCurrent =
          isPending &&
          (i === 0 ||
            chain[i - 1]?.status === "approved" ||
            chain[i - 1]?.status === "skipped");

        return (
          <div key={i} className="flex items-center gap-3">
            {i > 0 && (
              <div
                className={clsx(
                  "w-6 h-0.5 rounded-full",
                  isApproved || isSkipped ? "bg-emerald-600" : "bg-surface-600",
                )}
              />
            )}
            <div
              className={clsx(
                "border rounded-xl px-4 py-3 min-w-[130px] text-center transition-all",
                isApproved &&
                  "border-emerald-700/60 bg-emerald-950/30",
                isRejected &&
                  "border-rose-700/60 bg-rose-950/30",
                isSkipped && "border-surface-600 bg-surface-800/50",
                isPending &&
                  !isCurrent &&
                  "border-surface-700 bg-surface-800/30",
                isCurrent &&
                  "border-cyan-600/60 bg-cyan-950/30 ring-1 ring-cyan-500/20",
              )}
            >
              <p className="text-xs font-semibold text-text-secondary">
                {roleLabel}
              </p>
              <div className="flex items-center justify-center gap-1 mt-1.5">
                {isApproved && (
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                )}
                {isRejected && <X className="w-3.5 h-3.5 text-rose-400" />}
                {isCurrent && (
                  <Clock className="w-3.5 h-3.5 text-accent-cyan animate-pulse" />
                )}
                <span
                  className={clsx(
                    "text-xs capitalize",
                    isApproved && "text-emerald-400",
                    isRejected && "text-rose-400",
                    isSkipped && "text-surface-500",
                    isPending && !isCurrent && "text-text-muted",
                    isCurrent && "text-accent-cyan",
                  )}
                >
                  {isCurrent ? "Awaiting" : item.status}
                </span>
              </div>
              {item.approver_name && (
                <p className="text-[10px] text-text-muted mt-1.5 truncate max-w-[110px]">
                  {item.approver_name}
                </p>
              )}
              {item.decided_at && (
                <p className="text-[10px] text-text-muted">
                  {formatRelativeTime(item.decided_at)}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
