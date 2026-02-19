import {
  ArrowRightLeft,
  CheckCircle2,
  Clock,
  Hourglass,
  XCircle,
} from "lucide-react";
import { clsx } from "clsx";
import type { TransferStats } from "@/types";

interface Props {
  stats: TransferStats | null;
}

interface StatCard {
  label: string;
  value: string | number;
  sub: string;
  icon: React.ComponentType<{ className?: string }>;
  accent: string;
  border: string;
}

export default function StatsGrid({ stats }: Props) {
  const cards: StatCard[] = [
    {
      label: "TOTAL TRANSFERS",
      value: stats?.total ?? "—",
      sub: "All time",
      icon: ArrowRightLeft,
      accent: "text-accent-cyan",
      border: "border-t-cyan-400",
    },
    {
      label: "PENDING APPROVAL",
      value: stats?.pending ?? "—",
      sub: "Awaiting review",
      icon: Hourglass,
      accent: "text-accent-amber",
      border: "border-t-amber-400",
    },
    {
      label: "COMPLETED",
      value: stats?.transferred ?? "—",
      sub: "Successfully delivered",
      icon: CheckCircle2,
      accent: "text-accent-emerald",
      border: "border-t-emerald-400",
    },
    {
      label: "REJECTED",
      value: stats?.rejected ?? "—",
      sub: "Sent back for revision",
      icon: XCircle,
      accent: "text-accent-rose",
      border: "border-t-rose-400",
    },
    {
      label: "AVG PIPELINE TIME",
      value:
        stats?.avg_time_hours != null
          ? `${stats.avg_time_hours.toFixed(1)}h`
          : "—",
      sub: "Upload to production",
      icon: Clock,
      accent: "text-accent-violet",
      border: "border-t-violet-400",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {cards.map((c) => (
        <div
          key={c.label}
          className={clsx(
            "bg-bg-card border border-surface-700 rounded-xl p-5 border-t-2",
            c.border,
          )}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-semibold tracking-widest text-text-muted uppercase">
              {c.label}
            </span>
            <c.icon className={clsx("w-4 h-4", c.accent)} />
          </div>
          <p className={clsx("text-3xl font-bold font-mono", c.accent)}>
            {c.value}
          </p>
          <p className="text-xs text-text-muted mt-1">{c.sub}</p>
        </div>
      ))}
    </div>
  );
}
