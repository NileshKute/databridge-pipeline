import { clsx } from "clsx";

interface Props {
  percent: number;
  className?: string;
  showLabel?: boolean;
}

export default function ProgressBar({ percent, className, showLabel = true }: Props) {
  const clamped = Math.min(100, Math.max(0, percent));
  return (
    <div className={clsx("w-full", className)}>
      <div className="flex items-center gap-2">
        <div className="flex-1 bg-surface-700 rounded-full h-2 overflow-hidden">
          <div
            className={clsx(
              "h-full rounded-full transition-all duration-500",
              clamped === 100 ? "bg-emerald-500" : "bg-brand-500",
            )}
            style={{ width: `${clamped}%` }}
          />
        </div>
        {showLabel && (
          <span className="text-xs text-surface-400 tabular-nums w-12 text-right">
            {clamped.toFixed(1)}%
          </span>
        )}
      </div>
    </div>
  );
}
