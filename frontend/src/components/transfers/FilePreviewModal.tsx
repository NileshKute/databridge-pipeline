import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import apiClient from "@/api/client";
import { formatFileSize } from "@/utils/formatters";
import type { TransferFile } from "@/types";

const IMAGE_EXTS = ["jpg", "jpeg", "png", "tif", "tiff", "tga", "exr", "dpx", "hdr", "psd"];
const VIDEO_EXTS = ["mov", "mp4", "avi", "mxf", "mkv"];

function getFileKind(filename: string): "image" | "video" | "other" {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";
  if (IMAGE_EXTS.includes(ext)) return "image";
  if (VIDEO_EXTS.includes(ext)) return "video";
  return "other";
}

interface Props {
  transferId: number;
  file: TransferFile;
  onClose: () => void;
}

export default function FilePreviewModal({ transferId, file, onClose }: Props) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const blobUrlRef = useRef<string | null>(null);
  const kind = getFileKind(file.filename);

  useEffect(() => {
    if (kind === "other") {
      setError("Preview not available for this file type.");
      return;
    }
    setError(null);
    const url = `/transfers/${transferId}/files/${file.id}/preview`;
    apiClient
      .get(url, { responseType: "blob" })
      .then((res) => {
        const u = URL.createObjectURL(res.data);
        blobUrlRef.current = u;
        setBlobUrl(u);
      })
      .catch(() => setError("Failed to load preview"));

    return () => {
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
        blobUrlRef.current = null;
      }
      setBlobUrl(null);
    };
  }, [transferId, file.id, kind]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="File preview"
    >
      <div
        className="relative max-h-full max-w-full rounded-lg bg-surface-900 shadow-xl border border-surface-700 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-4 px-4 py-2 border-b border-surface-700 bg-surface-850">
          <span className="text-text-primary font-mono text-sm truncate flex-1" title={file.filename}>
            {file.filename}
          </span>
          <span className="text-text-muted text-xs whitespace-nowrap">
            {formatFileSize(file.size_bytes)}
          </span>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded hover:bg-surface-700 text-text-muted hover:text-text-primary transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4 flex items-center justify-center min-h-[200px] max-h-[85vh] max-w-full">
          {error && (
            <p className="text-rose-400 text-sm">{error}</p>
          )}
          {!error && kind === "image" && blobUrl && (
            <img
              src={blobUrl}
              alt={file.filename}
              className="max-h-[80vh] max-w-full object-contain rounded"
            />
          )}
          {!error && kind === "video" && blobUrl && (
            <video
              ref={videoRef}
              src={blobUrl}
              controls
              className="max-h-[80vh] max-w-full rounded"
              preload="metadata"
            />
          )}
          {!error && kind === "other" && (
            <p className="text-text-muted text-sm">No preview for 3D/scene files.</p>
          )}
        </div>
      </div>
    </div>
  );
}
