import { clsx } from "clsx";
import { STATUS_CONFIG } from "@/utils/constants";

interface Props {
  status: string;
  className?: string;
}

const DOT_COLORS: Record<string, string> = {
  cyan: "bg-cyan-400",
  amber: "bg-amber-400",
  emerald: "bg-emerald-400",
  blue: "bg-blue-400",
  rose: "bg-rose-400",
  violet: "bg-violet-400",
  gray: "bg-surface-400",
};

const BG_COLORS: Record<string, string> = {
  cyan: "bg-cyan-950/60 text-cyan-300 border-cyan-800/50",
  amber: "bg-amber-950/60 text-amber-300 border-amber-800/50",
  emerald: "bg-emerald-950/60 text-emerald-300 border-emerald-800/50",
  blue: "bg-blue-950/60 text-blue-300 border-blue-800/50",
  rose: "bg-rose-950/60 text-rose-300 border-rose-800/50",
  violet: "bg-violet-950/60 text-violet-300 border-violet-800/50",
  gray: "bg-surface-800 text-surface-300 border-surface-600",
};

export default function StatusBadge({ status, className }: Props) {
  const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG];
  const color = config?.color ?? "gray";
  const label = config?.label ?? status.replace(/_/g, " ");
  const pulse = config?.dotPulse ?? false;

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border",
        BG_COLORS[color],
        className,
      )}
    >
      <span
        className={clsx(
          "w-1.5 h-1.5 rounded-full shrink-0",
          DOT_COLORS[color],
          pulse && "animate-pulse",
        )}
      />
      {label}
    </span>
  );
}
