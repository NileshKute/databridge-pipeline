import { Check, X } from "lucide-react";
import { clsx } from "clsx";
import type { ApprovalChainItem } from "@/types";

interface Props {
  approvals: ApprovalChainItem[];
  compact?: boolean;
}

const ROLE_ABBREV: Record<string, string> = {
  team_lead: "TL",
  supervisor: "SV",
  line_producer: "LP",
  data_team: "DT",
  it_team: "IT",
};

const ROLE_LABELS: Record<string, string> = {
  team_lead: "Team Lead",
  supervisor: "Supervisor",
  line_producer: "Line Producer",
  data_team: "Data Team",
  it_team: "IT Team",
};

function isCurrentStage(item: ApprovalChainItem, allItems: ApprovalChainItem[]): boolean {
  if (item.status !== "pending") return false;
  const idx = allItems.indexOf(item);
  return idx === 0 || allItems[idx - 1]?.status === "approved" || allItems[idx - 1]?.status === "skipped";
}

export default function ApprovalChain({ approvals, compact = false }: Props) {
  return (
    <div className="flex items-center gap-1">
      {approvals.map((item, i) => {
        const abbrev = ROLE_ABBREV[item.role] ?? item.role.slice(0, 2).toUpperCase();
        const label = ROLE_LABELS[item.role] ?? item.role;
        const current = isCurrentStage(item, approvals);

        return (
          <div key={i} className="flex items-center gap-1">
            {i > 0 && (
              <div
                className={clsx(
                  "w-3 h-px",
                  item.status === "approved" || item.status === "skipped"
                    ? "bg-emerald-600"
                    : "bg-surface-600",
                )}
              />
            )}
            <div
              className={clsx(
                "relative flex items-center justify-center rounded-full border-2 transition-all",
                compact ? "w-7 h-7" : "w-9 h-9",
                item.status === "approved" && "border-emerald-500 bg-emerald-950/40",
                item.status === "rejected" && "border-rose-500 bg-rose-950/40",
                item.status === "skipped" && "border-surface-500 bg-surface-800",
                item.status === "pending" && !current && "border-surface-600 bg-surface-800/50",
                current && "border-accent-cyan bg-cyan-950/40 animate-pulse",
              )}
              title={`${label}: ${item.status}${item.approver_name ? ` (${item.approver_name})` : ""}`}
            >
              {item.status === "approved" ? (
                <Check className={clsx("text-emerald-400", compact ? "w-3 h-3" : "w-4 h-4")} />
              ) : item.status === "rejected" ? (
                <X className={clsx("text-rose-400", compact ? "w-3 h-3" : "w-4 h-4")} />
              ) : (
                <span
                  className={clsx(
                    "font-bold",
                    compact ? "text-[9px]" : "text-[10px]",
                    current ? "text-accent-cyan" : "text-text-muted",
                  )}
                >
                  {abbrev}
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
