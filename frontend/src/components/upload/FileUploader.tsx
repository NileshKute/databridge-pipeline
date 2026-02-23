import { useCallback, useRef, useState, type DragEvent } from "react";
import { Upload, X, FileIcon } from "lucide-react";
import { clsx } from "clsx";
import toast from "react-hot-toast";
import { formatFileSize } from "@/utils/formatters";

const ALLOWED_EXTENSIONS = [
  ".jpg", ".jpeg", ".png", ".exr", ".tif", ".tiff", ".dpx", ".hdr", ".psd", ".tga",
  ".mov", ".mp4", ".avi", ".mxf", ".mkv",
  ".abc", ".fbx", ".obj", ".usd", ".usda", ".usdc", ".ma", ".mb",
];

function validateFile(file: File): string | null {
  const parts = file.name.split(".");
  const ext = parts.length > 1 ? "." + (parts.pop() ?? "").toLowerCase() : "";
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return `"${file.name}" — format ${ext || "(none)"} is not allowed. Only VFX formats (images, video, 3D) are accepted.`;
  }
  return null;
}

interface Props {
  files: File[];
  onChange: (files: File[]) => void;
}

export default function FileUploader({ files, onChange }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const addFiles = useCallback(
    (incoming: FileList | File[]) => {
      const arr = Array.from(incoming);
      const existing = new Set(files.map((f) => `${f.name}::${f.size}`));
      const valid: File[] = [];
      const errors: string[] = [];
      arr.forEach((file) => {
        if (existing.has(`${file.name}::${file.size}`)) return;
        const err = validateFile(file);
        if (err) errors.push(err);
        else {
          valid.push(file);
          existing.add(`${file.name}::${file.size}`);
        }
      });
      if (errors.length > 0) toast.error(errors.slice(0, 3).join("\n") + (errors.length > 3 ? ` (+${errors.length - 3} more)` : ""));
      if (valid.length > 0) onChange([...files, ...valid]);
    },
    [files, onChange],
  );

  const remove = (idx: number) => {
    onChange(files.filter((_, i) => i !== idx));
  };

  const handleDrag = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragIn = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items?.length) setDragging(true);
  };

  const handleDragOut = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
    if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files);
  };

  return (
    <div>
      {/* Drop zone */}
      <div
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={clsx(
          "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all",
          dragging
            ? "border-primary-500 bg-primary-900/20"
            : "border-surface-600 hover:border-surface-500 bg-surface-850/50",
        )}
      >
        <Upload
          className={clsx(
            "w-8 h-8 mx-auto mb-3",
            dragging ? "text-primary-400" : "text-text-muted",
          )}
        />
        <p className="text-sm text-text-secondary">
          <span className="font-medium text-primary-400">Click to browse</span>{" "}
          or drag & drop VFX files here
        </p>
        <p className="text-xs text-text-muted mt-1">
          Images: JPG, PNG, EXR, TIFF, DPX, HDR, PSD, TGA · Video: MOV, MP4, AVI, MXF, MKV · 3D: ABC, FBX, OBJ, USD, MA, MB
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.length) addFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.map((f, i) => (
            <div
              key={`${f.name}-${i}`}
              className="flex items-center justify-between bg-surface-850 rounded-lg px-3 py-2 border border-surface-700"
            >
              <div className="flex items-center gap-2 min-w-0">
                <FileIcon className="w-4 h-4 text-text-muted shrink-0" />
                <span className="text-sm text-text-primary truncate">
                  {f.name}
                </span>
                <span className="text-xs text-text-muted shrink-0">
                  {formatFileSize(f.size)}
                </span>
              </div>
              <button
                type="button"
                onClick={() => remove(i)}
                className="p-1 rounded hover:bg-rose-950/40 text-text-muted hover:text-accent-rose transition-colors shrink-0"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
          <p className="text-xs text-text-muted">
            {files.length} file{files.length !== 1 ? "s" : ""} &middot;{" "}
            {formatFileSize(files.reduce((s, f) => s + f.size, 0))} total
          </p>
        </div>
      )}
    </div>
  );
}
