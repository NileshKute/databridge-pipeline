import { useEffect, useState } from "react";
import {
  ArrowRightLeft,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FolderKanban,
} from "lucide-react";
import StatsCard from "@/components/dashboard/StatsCard";
import TransferTable from "@/components/transfers/TransferTable";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import EmptyState from "@/components/common/EmptyState";
import { useTransferStore } from "@/store/transferStore";
import { useProjectStore } from "@/store/projectStore";
import { useAuthStore } from "@/store/authStore";

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { transfers, fetchTransfers, isLoading } = useTransferStore();
  const { projects, fetchProjects } = useProjectStore();
  const [stats, setStats] = useState({ total: 0, completed: 0, pending: 0, failed: 0 });

  useEffect(() => {
    fetchTransfers();
    fetchProjects();
  }, [fetchTransfers, fetchProjects]);

  useEffect(() => {
    setStats({
      total: transfers.length,
      completed: transfers.filter((t) => t.status === "completed").length,
      pending: transfers.filter((t) => t.status === "pending" || t.status === "approved").length,
      failed: transfers.filter((t) => t.status === "failed").length,
    });
  }, [transfers]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-surface-100">
          Welcome back, {user?.display_name?.split(" ")[0]}
        </h1>
        <p className="text-surface-400 mt-1">Here's an overview of your data pipeline.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard title="Total Transfers" value={stats.total} icon={ArrowRightLeft} color="brand" />
        <StatsCard title="Completed" value={stats.completed} icon={CheckCircle2} color="emerald" />
        <StatsCard title="Pending / Queued" value={stats.pending} icon={Clock} color="amber" />
        <StatsCard title="Failed" value={stats.failed} icon={AlertTriangle} color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 card">
          <h2 className="text-lg font-semibold text-surface-200 mb-4">Recent Transfers</h2>
          {isLoading ? (
            <LoadingSpinner />
          ) : transfers.length === 0 ? (
            <EmptyState title="No transfers yet" description="Create your first data transfer to get started." />
          ) : (
            <TransferTable transfers={transfers.slice(0, 10)} />
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-surface-200 mb-4">
            <FolderKanban className="inline h-5 w-5 mr-2 text-brand-400" />
            Active Projects
          </h2>
          {projects.length === 0 ? (
            <p className="text-surface-400 text-sm">No projects configured.</p>
          ) : (
            <ul className="space-y-3">
              {projects.slice(0, 8).map((p) => (
                <li key={p.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-surface-200">{p.name}</p>
                    <p className="text-xs text-surface-400 font-mono">{p.code}</p>
                  </div>
                  <span className="text-xs text-surface-500 capitalize">{p.status}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
