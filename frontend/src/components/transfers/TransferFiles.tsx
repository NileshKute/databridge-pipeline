import { File, ShieldCheck, ShieldAlert, ShieldQuestion } from "lucide-react";
import { clsx } from "clsx";
import { formatFileSize, formatRelativeTime } from "@/utils/formatters";
import type { TransferFile } from "@/types";

interface Props {
  files: TransferFile[];
}

const SCAN_CONFIG: Record<
  string,
  { icon: typeof ShieldCheck; color: string; label: string }
> = {
  clean: {
    icon: ShieldCheck,
    color: "text-emerald-400",
    label: "Clean",
  },
  infected: {
    icon: ShieldAlert,
    color: "text-rose-400",
    label: "Infected",
  },
  pending: {
    icon: ShieldQuestion,
    color: "text-text-muted",
    label: "Pending",
  },
  skipped: {
    icon: ShieldQuestion,
    color: "text-surface-500",
    label: "Skipped",
  },
};

export default function TransferFiles({ files }: Props) {
  if (files.length === 0) {
    return <p className="text-text-muted text-sm py-4">No files uploaded yet.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-surface-700 text-text-muted">
            <th className="text-left py-2.5 px-4 font-medium text-xs uppercase tracking-wider">
              Filename
            </th>
            <th className="text-left py-2.5 px-4 font-medium text-xs uppercase tracking-wider">
              Size
            </th>
            <th className="text-left py-2.5 px-4 font-medium text-xs uppercase tracking-wider">
              Checksum
            </th>
            <th className="text-left py-2.5 px-4 font-medium text-xs uppercase tracking-wider">
              Scan
            </th>
            <th className="text-left py-2.5 px-4 font-medium text-xs uppercase tracking-wider">
              Uploaded
            </th>
          </tr>
        </thead>
        <tbody>
          {files.map((f) => {
            const scan =
              SCAN_CONFIG[f.virus_scan_status] ?? SCAN_CONFIG.pending;
            const ScanIcon = scan.icon;
            return (
              <tr
                key={f.id}
                className="border-b border-surface-800 hover:bg-bg-card-hover/30 transition-colors"
              >
                <td className="py-2.5 px-4">
                  <div className="flex items-center gap-2">
                    <File className="w-4 h-4 text-text-muted shrink-0" />
                    <span className="text-text-primary font-mono text-xs truncate max-w-[240px]">
                      {f.filename}
                    </span>
                  </div>
                </td>
                <td className="py-2.5 px-4 text-text-secondary tabular-nums whitespace-nowrap">
                  {formatFileSize(f.size_bytes)}
                </td>
                <td className="py-2.5 px-4">
                  {f.checksum_sha256 ? (
                    <span
                      className="font-mono text-xs text-text-muted"
                      title={f.checksum_sha256}
                    >
                      {f.checksum_sha256.slice(0, 12)}...
                    </span>
                  ) : (
                    <span className="text-text-muted text-xs">—</span>
                  )}
                </td>
                <td className="py-2.5 px-4">
                  <div className={clsx("flex items-center gap-1.5", scan.color)}>
                    <ScanIcon className="w-3.5 h-3.5" />
                    <span className="text-xs font-medium">{scan.label}</span>
                  </div>
                </td>
                <td className="py-2.5 px-4 text-text-muted text-xs whitespace-nowrap">
                  {formatRelativeTime(f.uploaded_at)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
