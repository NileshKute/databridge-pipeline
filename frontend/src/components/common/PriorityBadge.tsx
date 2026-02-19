import { clsx } from "clsx";
import { priorityColor } from "@/utils/format";

interface Props {
  priority: string;
  className?: string;
}

export default function PriorityBadge({ priority, className }: Props) {
  return (
    <span className={clsx("badge", priorityColor(priority), className)}>
      {priority}
    </span>
  );
}
