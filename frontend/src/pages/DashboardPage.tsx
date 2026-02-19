import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Search } from "lucide-react";
import { clsx } from "clsx";
import toast from "react-hot-toast";
import PageHeader from "@/components/common/PageHeader";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import StatsGrid from "@/components/dashboard/StatsGrid";
import PipelineVisual from "@/components/dashboard/PipelineVisual";
import TransferTable from "@/components/transfers/TransferTable";
import { useTransferStore } from "@/store/transferStore";
import { useApprovalStore } from "@/store/approvalStore";

const FILTER_PILLS = [
  { value: "", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "scanning", label: "Scanning" },
  { value: "transferred", label: "Transferred" },
] as const;

const PENDING_STATUSES = "pending_team_lead,pending_supervisor,pending_line_producer";

export default function DashboardPage() {
  const navigate = useNavigate();
  const { transfers, stats, isLoading, fetchTransfers, fetchStats } =
    useTransferStore();
  const { approve, reject } = useApprovalStore();

  const [activeFilter, setActiveFilter] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchStats();
    fetchTransfers({ per_page: 15 });
  }, [fetchStats, fetchTransfers]);

  const handleFilter = useCallback(
    (value: string) => {
      setActiveFilter(value);
      const status = value === "pending" ? PENDING_STATUSES : value;
      fetchTransfers({ status: status || undefined, search: search || undefined, per_page: 15, page: 1 });
    },
    [fetchTransfers, search],
  );

  const handleSearch = useCallback(
    (value: string) => {
      setSearch(value);
      const status = activeFilter === "pending" ? PENDING_STATUSES : activeFilter;
      fetchTransfers({ status: status || undefined, search: value || undefined, per_page: 15, page: 1 });
    },
    [fetchTransfers, activeFilter],
  );

  const handleApprove = async (id: number) => {
    try {
      await approve(id);
      toast.success("Transfer approved");
      fetchTransfers({ per_page: 15 });
      fetchStats();
    } catch {
      toast.error("Failed to approve");
    }
  };

  const handleReject = async (id: number) => {
    const reason = window.prompt("Rejection reason:");
    if (!reason) return;
    try {
      await reject(id, reason);
      toast.success("Transfer rejected");
      fetchTransfers({ per_page: 15 });
      fetchStats();
    } catch {
      toast.error("Failed to reject");
    }
  };

  const handleProcess = (id: number) => {
    navigate(`/transfers/${id}`);
  };

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Overview of your data transfer pipeline"
      />

      {/* Stats */}
      <StatsGrid stats={stats} />

      {/* Pipeline */}
      <div className="mt-6">
        <PipelineVisual />
      </div>

      {/* Recent Transfers */}
      <div className="mt-8">
        <div className="bg-bg-card border border-surface-700 rounded-xl">
          <div className="p-5 border-b border-surface-700">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">
                Recent Transfers
              </h3>
              <div className="flex items-center gap-3">
                {/* Filter pills */}
                <div className="flex items-center bg-bg-secondary rounded-lg p-0.5">
                  {FILTER_PILLS.map((pill) => (
                    <button
                      key={pill.value}
                      onClick={() => handleFilter(pill.value)}
                      className={clsx(
                        "px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
                        activeFilter === pill.value
                          ? "bg-accent-cyan/20 text-accent-cyan"
                          : "text-text-muted hover:text-text-secondary",
                      )}
                    >
                      {pill.label}
                    </button>
                  ))}
                </div>
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => handleSearch(e.target.value)}
                    placeholder="Search..."
                    className="input-field pl-8 py-1.5 text-xs w-48"
                  />
                </div>
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="py-16">
              <LoadingSpinner />
            </div>
          ) : (
            <TransferTable
              transfers={transfers}
              showApprovalActions
              onApprove={handleApprove}
              onReject={handleReject}
              onProcess={handleProcess}
            />
          )}
        </div>
      </div>
    </div>
  );
}
