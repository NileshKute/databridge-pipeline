import { useEffect, useState, useCallback } from "react";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import PageHeader from "@/components/common/PageHeader";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import EmptyState from "@/components/common/EmptyState";
import apiClient from "@/api/client";
import { formatDateTime } from "@/utils/formatters";
import type { HistoryEntry } from "@/types";

interface ActivityResponse {
  items: HistoryEntry[];
  total: number;
  page: number;
  pages: number;
}

const ACTION_COLORS: Record<string, string> = {
  created: "text-accent-cyan",
  uploaded: "text-cyan-400",
  submitted: "text-cyan-400",
  approved: "text-emerald-400",
  rejected: "text-accent-rose",
  scan_started: "text-blue-400",
  scan_completed: "text-blue-400",
  scan_passed: "text-emerald-400",
  scan_failed: "text-accent-rose",
  transfer_started: "text-accent-violet",
  transfer_completed: "text-accent-violet",
  verified: "text-emerald-400",
  cancelled: "text-text-muted",
  override: "text-accent-amber",
};

export default function ActivityPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const load = useCallback(
    async (p: number, q: string) => {
      setLoading(true);
      try {
        const params: Record<string, unknown> = { page: p, per_page: 30 };
        if (q) params.search = q;
        const { data } = await apiClient.get<ActivityResponse>("/activity/", {
          params,
        });
        setEntries(data.items);
        setTotal(data.total);
        setPage(data.page);
        setPages(data.pages);
      } catch {
        setEntries([]);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    load(1, search);
  }, [load, search]);

  const handleSearch = () => {
    setSearch(searchInput.trim());
  };

  return (
    <div>
      <PageHeader
        title="Activity Log"
        subtitle={`${total} entries`}
      />

      {/* Search bar */}
      <div className="flex items-center gap-3 mb-5 max-w-md">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search by reference, action, or user..."
            className="input-field pl-9 text-sm"
          />
        </div>
        <button onClick={handleSearch} className="btn-secondary text-sm">
          Search
        </button>
      </div>

      {loading ? (
        <div className="py-16">
          <LoadingSpinner />
        </div>
      ) : entries.length === 0 ? (
        <EmptyState
          title="No activity"
          description={search ? "No results for your search" : "No activity recorded yet"}
        />
      ) : (
        <div className="bg-bg-card border border-surface-700 rounded-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-700 text-text-muted">
                  <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider w-[180px]">
                    Timestamp
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider w-[100px]">
                    Transfer
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider w-[100px]">
                    User
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
                    Action
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-xs uppercase tracking-wider">
                    Description
                  </th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => {
                  const actionColor =
                    ACTION_COLORS[entry.action] ?? "text-text-secondary";
                  return (
                    <tr
                      key={entry.id}
                      className="border-b border-surface-800 hover:bg-bg-card-hover/30 transition-colors"
                    >
                      <td className="py-2.5 px-4 font-mono text-xs text-text-muted whitespace-nowrap">
                        {formatDateTime(entry.created_at)}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-xs text-accent-cyan">
                        #{entry.transfer_id}
                      </td>
                      <td className="py-2.5 px-4 text-xs text-accent-cyan">
                        {entry.user_id ? `User #${entry.user_id}` : "System"}
                      </td>
                      <td className="py-2.5 px-4">
                        <span
                          className={`text-xs font-medium capitalize ${actionColor}`}
                        >
                          {entry.action.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-xs text-text-secondary max-w-xs truncate">
                        {entry.description ?? "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {pages > 1 && (
            <div className="flex items-center justify-between px-5 py-4 border-t border-surface-700">
              <p className="text-text-muted text-sm">
                Page {page} of {pages}{" "}
                <span className="text-text-muted">({total} results)</span>
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => load(page - 1, search)}
                  disabled={page <= 1}
                  className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-sm text-text-secondary tabular-nums min-w-[60px] text-center">
                  {page} / {pages}
                </span>
                <button
                  onClick={() => load(page + 1, search)}
                  disabled={page >= pages}
                  className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
