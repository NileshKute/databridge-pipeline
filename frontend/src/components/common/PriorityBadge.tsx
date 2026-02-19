import { clsx } from "clsx";
import { getPriorityColor } from "@/utils/formatters";

interface Props {
  priority: string;
  className?: string;
}

export default function PriorityBadge({ priority, className }: Props) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium capitalize",
        getPriorityColor(priority),
        className,
      )}
    >
      {priority}
    </span>
  );
}
