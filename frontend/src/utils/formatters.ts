import { format, formatDistanceToNow, parseISO } from "date-fns";

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const val = bytes / Math.pow(1024, i);
  return `${val.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return "—";
  const d = typeof date === "string" ? parseISO(date) : date;
  return format(d, "MMM d, yyyy");
}

export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return "—";
  const d = typeof date === "string" ? parseISO(date) : date;
  return format(d, "MMM d, yyyy HH:mm");
}

export function formatRelativeTime(date: string | Date | null | undefined): string {
  if (!date) return "—";
  const d = typeof date === "string" ? parseISO(date) : date;
  return formatDistanceToNow(d, { addSuffix: true });
}

const STATUS_COLORS: Record<string, string> = {
  uploaded: "text-accent-cyan bg-cyan-950 border-cyan-800",
  pending_team_lead: "text-accent-amber bg-amber-950 border-amber-800",
  pending_supervisor: "text-accent-amber bg-amber-950 border-amber-800",
  pending_line_producer: "text-accent-amber bg-amber-950 border-amber-800",
  approved: "text-accent-emerald bg-emerald-950 border-emerald-800",
  scanning: "text-blue-400 bg-blue-950 border-blue-800",
  scan_passed: "text-accent-emerald bg-emerald-950 border-emerald-800",
  scan_failed: "text-accent-rose bg-rose-950 border-rose-800",
  copying: "text-blue-400 bg-blue-950 border-blue-800",
  ready_for_transfer: "text-accent-cyan bg-cyan-950 border-cyan-800",
  transferring: "text-blue-400 bg-blue-950 border-blue-800",
  verifying: "text-blue-400 bg-blue-950 border-blue-800",
  transferred: "text-accent-violet bg-violet-950 border-violet-800",
  rejected: "text-accent-rose bg-rose-950 border-rose-800",
  cancelled: "text-text-muted bg-surface-800 border-surface-600",
};

export function getStatusColor(status: string): string {
  return STATUS_COLORS[status] ?? "text-text-secondary bg-surface-800 border-surface-600";
}

const STATUS_LABELS: Record<string, string> = {
  uploaded: "Uploaded",
  pending_team_lead: "Pending Team Lead",
  pending_supervisor: "Pending Supervisor",
  pending_line_producer: "Pending Line Producer",
  approved: "Approved",
  scanning: "Scanning",
  scan_passed: "Scan Passed",
  scan_failed: "Scan Failed",
  copying: "Copying",
  ready_for_transfer: "Ready for Transfer",
  transferring: "Transferring",
  verifying: "Verifying",
  transferred: "Transferred",
  rejected: "Rejected",
  cancelled: "Cancelled",
};

export function getStatusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

const PRIORITY_COLORS: Record<string, string> = {
  low: "text-surface-400 bg-surface-800",
  normal: "text-blue-400 bg-blue-950",
  high: "text-accent-amber bg-amber-950",
  urgent: "text-accent-rose bg-rose-950",
};

export function getPriorityColor(priority: string): string {
  return PRIORITY_COLORS[priority] ?? "text-text-secondary bg-surface-800";
}
