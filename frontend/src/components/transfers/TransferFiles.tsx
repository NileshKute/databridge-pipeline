import { useEffect, useRef, useState } from "react";
import { File, Play, ShieldCheck, ShieldAlert, ShieldQuestion } from "lucide-react";
import { clsx } from "clsx";
import apiClient from "@/api/client";
import { formatFileSize, formatRelativeTime } from "@/utils/formatters";
import type { TransferFile } from "@/types";
import FilePreviewModal from "./FilePreviewModal";

const IMAGE_EXTS = ["jpg", "jpeg", "png", "tif", "tiff", "tga", "exr", "dpx", "hdr", "psd"];
const VIDEO_EXTS = ["mov", "mp4", "avi", "mxf", "mkv"];

function fileKind(filename: string): "image" | "video" | "other" {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";
  if (IMAGE_EXTS.includes(ext)) return "image";
  if (VIDEO_EXTS.includes(ext)) return "video";
  return "other";
}

interface Props {
  transferId: number;
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

function FilePreviewCell({
  transferId,
  file,
  onClick,
}: {
  transferId: number;
  file: TransferFile;
  onClick: () => void;
}) {
  const [thumbUrl, setThumbUrl] = useState<string | null>(null);
  const thumbUrlRef = useRef<string | null>(null);
  const kind = fileKind(file.filename);

  useEffect(() => {
    if (kind !== "image") return;
    apiClient
      .get(`/transfers/${transferId}/files/${file.id}/thumbnail`, { responseType: "blob" })
      .then((res) => {
        const u = URL.createObjectURL(res.data);
        thumbUrlRef.current = u;
        setThumbUrl(u);
      })
      .catch(() => {});
    return () => {
      if (thumbUrlRef.current) {
        URL.revokeObjectURL(thumbUrlRef.current);
        thumbUrlRef.current = null;
      }
      setThumbUrl(null);
    };
  }, [transferId, file.id, kind]);

  if (kind === "image") {
    return (
      <button
        type="button"
        onClick={onClick}
        className="w-16 h-16 rounded-lg border border-surface-600 overflow-hidden bg-surface-850 hover:border-surface-500 transition-colors flex items-center justify-center shrink-0"
      >
        {thumbUrl ? (
          <img
            src={thumbUrl}
            alt=""
            className="w-full h-full object-cover"
          />
        ) : (
          <span className="text-text-muted text-xs">…</span>
        )}
      </button>
    );
  }
  if (kind === "video") {
    return (
      <button
        type="button"
        onClick={onClick}
        className="w-16 h-16 rounded-lg border border-surface-600 bg-surface-850 hover:border-surface-500 transition-colors flex items-center justify-center shrink-0 relative"
      >
        <Play className="w-6 h-6 text-white drop-shadow-md" />
      </button>
    );
  }
  return (
    <div className="w-16 h-16 rounded-lg border border-surface-600 bg-surface-850 flex items-center justify-center shrink-0">
      <File className="w-6 h-6 text-text-muted" />
    </div>
  );
}

export default function TransferFiles({ transferId, files }: Props) {
  const [previewFile, setPreviewFile] = useState<TransferFile | null>(null);
  const list = files ?? [];
  if (list.length === 0) {
    return <p className="text-text-muted text-sm py-4">No files uploaded yet.</p>;
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-700 text-text-muted">
              <th className="text-left py-2.5 px-4 font-medium text-xs uppercase tracking-wider w-20">
                Preview
              </th>
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
            {list.map((f) => {
              const scan =
                SCAN_CONFIG[f.virus_scan_status] ?? SCAN_CONFIG.pending;
              const ScanIcon = scan.icon;
              const kind = fileKind(f.filename);
              const canPreview = kind === "image" || kind === "video";
              return (
                <tr
                  key={f.id}
                  className="border-b border-surface-800 hover:bg-surface-800 transition-colors"
                >
                  <td className="py-2.5 px-4">
                    {canPreview ? (
                      <FilePreviewCell
                        transferId={transferId}
                        file={f}
                        onClick={() => setPreviewFile(f)}
                      />
                    ) : (
                      <div className="w-16 h-16 rounded-lg border border-surface-600 bg-surface-850 flex items-center justify-center shrink-0">
                        <File className="w-6 h-6 text-text-muted" />
                      </div>
                    )}
                  </td>
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
      {previewFile && (
        <FilePreviewModal
          transferId={transferId}
          file={previewFile}
          onClose={() => setPreviewFile(null)}
        />
      )}
    </>
  );
}
