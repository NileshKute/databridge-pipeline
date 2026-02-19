import { useEffect, useState, useCallback } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import PageHeader from "@/components/common/PageHeader";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import TransferTable from "@/components/transfers/TransferTable";
import TransferFilters from "@/components/transfers/TransferFilters";
import { useTransferStore } from "@/store/transferStore";

export default function TransfersPage() {
  const { transfers, pagination, isLoading, fetchTransfers } =
    useTransferStore();

  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [search, setSearch] = useState("");

  const load = useCallback(
    (page?: number) => {
      fetchTransfers({
        status: status || undefined,
        category: category || undefined,
        search: search || undefined,
        page: page ?? 1,
      });
    },
    [fetchTransfers, status, category, search],
  );

  useEffect(() => {
    load(1);
  }, [load]);

  return (
    <div>
      <PageHeader
        title="All Transfers"
        subtitle={`${pagination.total} transfer${pagination.total !== 1 ? "s" : ""} total`}
      />

      <TransferFilters
        status={status}
        category={category}
        priority={priority}
        search={search}
        onStatusChange={(v) => setStatus(v)}
        onCategoryChange={(v) => setCategory(v)}
        onPriorityChange={(v) => setPriority(v)}
        onSearchChange={(v) => setSearch(v)}
      />

      <div className="bg-bg-card border border-surface-700 rounded-xl">
        {isLoading ? (
          <div className="py-16">
            <LoadingSpinner />
          </div>
        ) : (
          <>
            <TransferTable transfers={transfers} showCategory />

            {/* Pagination */}
            {pagination.pages > 1 && (
              <div className="flex items-center justify-between px-5 py-4 border-t border-surface-700">
                <p className="text-text-muted text-sm">
                  Page {pagination.page} of {pagination.pages}{" "}
                  <span className="text-text-muted">
                    ({pagination.total} results)
                  </span>
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => load(pagination.page - 1)}
                    disabled={pagination.page <= 1}
                    className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="text-sm text-text-secondary tabular-nums min-w-[60px] text-center">
                    {pagination.page} / {pagination.pages}
                  </span>
                  <button
                    onClick={() => load(pagination.page + 1)}
                    disabled={pagination.page >= pagination.pages}
                    className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
