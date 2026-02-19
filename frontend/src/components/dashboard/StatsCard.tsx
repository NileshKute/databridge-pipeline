import { clsx } from "clsx";
import type { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: "brand" | "emerald" | "amber" | "red";
}

const colorMap = {
  brand: "bg-brand-500/20 text-brand-400",
  emerald: "bg-emerald-500/20 text-emerald-400",
  amber: "bg-amber-500/20 text-amber-400",
  red: "bg-red-500/20 text-red-400",
};

export default function StatsCard({ title, value, subtitle, icon: Icon, color = "brand" }: Props) {
  return (
    <div className="card flex items-start gap-4">
      <div className={clsx("p-3 rounded-lg", colorMap[color])}>
        <Icon className="h-6 w-6" />
      </div>
      <div>
        <p className="text-sm text-surface-400">{title}</p>
        <p className="text-2xl font-bold text-surface-100 mt-1">{value}</p>
        {subtitle && <p className="text-xs text-surface-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
}
