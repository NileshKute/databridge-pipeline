import { format, formatDistanceToNow } from "date-fns";

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${units[i]}`;
}

export function formatDate(dateStr: string): string {
  return format(new Date(dateStr), "MMM d, yyyy HH:mm");
}

export function formatRelativeDate(dateStr: string): string {
  return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
}

export function statusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: "bg-yellow-500/20 text-yellow-400",
    validating: "bg-blue-500/20 text-blue-400",
    approved: "bg-green-500/20 text-green-400",
    in_progress: "bg-brand-500/20 text-brand-400",
    checksumming: "bg-purple-500/20 text-purple-400",
    completed: "bg-emerald-500/20 text-emerald-400",
    failed: "bg-red-500/20 text-red-400",
    cancelled: "bg-surface-500/20 text-surface-400",
    rejected: "bg-orange-500/20 text-orange-400",
    active: "bg-emerald-500/20 text-emerald-400",
    on_hold: "bg-yellow-500/20 text-yellow-400",
    archived: "bg-surface-500/20 text-surface-400",
  };
  return colors[status] ?? "bg-surface-500/20 text-surface-400";
}

export function priorityColor(priority: string): string {
  const colors: Record<string, string> = {
    low: "bg-surface-500/20 text-surface-400",
    normal: "bg-blue-500/20 text-blue-400",
    high: "bg-orange-500/20 text-orange-400",
    urgent: "bg-red-500/20 text-red-400",
  };
  return colors[priority] ?? "bg-surface-500/20 text-surface-400";
}
