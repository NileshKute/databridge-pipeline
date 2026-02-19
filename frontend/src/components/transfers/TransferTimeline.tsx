import { clsx } from "clsx";
import { formatRelativeTime } from "@/utils/formatters";
import type { HistoryEntry } from "@/types";

interface Props {
  entries: HistoryEntry[];
}

const ACTION_COLORS: Record<string, string> = {
  created: "bg-accent-cyan",
  uploaded: "bg-cyan-400",
  submitted: "bg-cyan-400",
  approved: "bg-emerald-400",
  rejected: "bg-rose-400",
  scan_started: "bg-blue-400",
  scan_completed: "bg-blue-400",
  scan_passed: "bg-emerald-400",
  scan_failed: "bg-rose-400",
  transfer_started: "bg-violet-400",
  transfer_completed: "bg-violet-400",
  verified: "bg-emerald-400",
  cancelled: "bg-surface-400",
  override: "bg-amber-400",
};

export default function TransferTimeline({ entries }: Props) {
  if (entries.length === 0) {
    return (
      <p className="text-text-muted text-sm py-4">No activity yet.</p>
    );
  }

  return (
    <div className="relative">
      <div className="absolute left-[9px] top-3 bottom-3 w-px bg-surface-700" />
      <div className="space-y-4">
        {entries.map((entry) => {
          const dotColor =
            ACTION_COLORS[entry.action] ?? "bg-surface-500";
          return (
            <div key={entry.id} className="flex gap-4 relative">
              <div
                className={clsx(
                  "w-[18px] h-[18px] rounded-full border-2 border-bg-card shrink-0 mt-0.5 z-10",
                  dotColor,
                )}
              />
              <div className="flex-1 min-w-0 pb-1">
                <p className="text-sm text-text-primary">
                  <span className="font-medium capitalize">
                    {entry.action.replace(/_/g, " ")}
                  </span>
                  {entry.description && (
                    <span className="text-text-secondary">
                      {" "}
                      — {entry.description}
                    </span>
                  )}
                </p>
                <p className="text-xs text-text-muted mt-0.5">
                  {entry.user_id ? `User #${entry.user_id}` : "System"}{" "}
                  &middot; {formatRelativeTime(entry.created_at)}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
