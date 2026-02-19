import { useNavigate } from "react-router-dom";
import StatusBadge from "@/components/common/StatusBadge";
import PriorityBadge from "@/components/common/PriorityBadge";
import ProgressBar from "@/components/common/ProgressBar";
import { formatBytes, formatRelativeDate } from "@/utils/format";
import type { TransferListItem } from "@/types";

interface Props {
  transfers: TransferListItem[];
}

export default function TransferTable({ transfers }: Props) {
  const navigate = useNavigate();

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-surface-700 text-surface-400">
            <th className="text-left py-3 px-4 font-medium">Reference</th>
            <th className="text-left py-3 px-4 font-medium">Title</th>
            <th className="text-left py-3 px-4 font-medium">Status</th>
            <th className="text-left py-3 px-4 font-medium">Priority</th>
            <th className="text-left py-3 px-4 font-medium">Size</th>
            <th className="text-left py-3 px-4 font-medium">Files</th>
            <th className="text-left py-3 px-4 font-medium">Progress</th>
            <th className="text-left py-3 px-4 font-medium">Created</th>
          </tr>
        </thead>
        <tbody>
          {transfers.map((t) => (
            <tr
              key={t.id}
              onClick={() => navigate(`/transfers/${t.id}`)}
              className="border-b border-surface-800 hover:bg-surface-800/50 cursor-pointer transition-colors"
            >
              <td className="py-3 px-4 font-mono text-brand-400 text-xs">{t.reference_id}</td>
              <td className="py-3 px-4 text-surface-200 max-w-xs truncate">{t.title}</td>
              <td className="py-3 px-4">
                <StatusBadge status={t.status} />
              </td>
              <td className="py-3 px-4">
                <PriorityBadge priority={t.priority} />
              </td>
              <td className="py-3 px-4 text-surface-300 tabular-nums">{formatBytes(t.total_size_bytes)}</td>
              <td className="py-3 px-4 text-surface-300 tabular-nums">{t.file_count}</td>
              <td className="py-3 px-4 w-36">
                <ProgressBar percent={t.progress_percent} />
              </td>
              <td className="py-3 px-4 text-surface-400 text-xs">{formatRelativeDate(t.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
