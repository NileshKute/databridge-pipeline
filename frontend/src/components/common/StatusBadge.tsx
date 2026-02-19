import { clsx } from "clsx";
import { statusColor } from "@/utils/format";

interface Props {
  status: string;
  className?: string;
}

export default function StatusBadge({ status, className }: Props) {
  return (
    <span className={clsx("badge", statusColor(status), className)}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
