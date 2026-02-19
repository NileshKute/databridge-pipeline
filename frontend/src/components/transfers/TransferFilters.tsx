import { Search } from "lucide-react";
import { CATEGORY_OPTIONS, PRIORITY_OPTIONS } from "@/utils/constants";

interface Props {
  status: string;
  category: string;
  priority: string;
  search: string;
  onStatusChange: (v: string) => void;
  onCategoryChange: (v: string) => void;
  onPriorityChange: (v: string) => void;
  onSearchChange: (v: string) => void;
}

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "uploaded", label: "Uploaded" },
  { value: "pending_team_lead", label: "Pending TL" },
  { value: "pending_supervisor", label: "Pending SV" },
  { value: "pending_line_producer", label: "Pending LP" },
  { value: "approved", label: "Approved" },
  { value: "scanning", label: "Scanning" },
  { value: "scan_passed", label: "Scan Passed" },
  { value: "ready_for_transfer", label: "Ready" },
  { value: "transferring", label: "Transferring" },
  { value: "transferred", label: "Transferred" },
  { value: "rejected", label: "Rejected" },
  { value: "cancelled", label: "Cancelled" },
];

export default function TransferFilters({
  status,
  category,
  priority,
  search,
  onStatusChange,
  onCategoryChange,
  onPriorityChange,
  onSearchChange,
}: Props) {
  return (
    <div className="flex flex-wrap items-center gap-3 mb-5">
      <select
        value={status}
        onChange={(e) => onStatusChange(e.target.value)}
        className="input-field w-auto min-w-[150px] text-sm"
      >
        {STATUS_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>

      <select
        value={category}
        onChange={(e) => onCategoryChange(e.target.value)}
        className="input-field w-auto min-w-[140px] text-sm"
      >
        <option value="">All Categories</option>
        {CATEGORY_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>

      <select
        value={priority}
        onChange={(e) => onPriorityChange(e.target.value)}
        className="input-field w-auto min-w-[130px] text-sm"
      >
        <option value="">All Priorities</option>
        {PRIORITY_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>

      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
        <input
          type="text"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search transfers..."
          className="input-field pl-9 text-sm"
        />
      </div>
    </div>
  );
}
