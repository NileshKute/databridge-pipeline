import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";
import TransferTable from "@/components/transfers/TransferTable";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import EmptyState from "@/components/common/EmptyState";
import { useTransferStore } from "@/store/transferStore";

export default function TransfersPage() {
  const { transfers, isLoading, fetchTransfers, page, totalPages } = useTransferStore();

  useEffect(() => {
    fetchTransfers();
  }, [fetchTransfers]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-100">Transfers</h1>
          <p className="text-surface-400 mt-1">Manage data transfers between staging and production.</p>
        </div>
        <Link to="/transfers/new" className="btn-primary flex items-center gap-2">
          <Plus className="h-4 w-4" />
          New Transfer
        </Link>
      </div>

      <div className="card">
        {isLoading ? (
          <LoadingSpinner />
        ) : transfers.length === 0 ? (
          <EmptyState
            title="No transfers found"
            description="Create a new transfer to move data between networks."
            action={
              <Link to="/transfers/new" className="btn-primary text-sm">
                Create Transfer
              </Link>
            }
          />
        ) : (
          <>
            <TransferTable transfers={transfers} />
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-surface-700">
                <p className="text-sm text-surface-400">
                  Page {page} of {totalPages}
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => fetchTransfers({ page: page - 1 })}
                    disabled={page <= 1}
                    className="btn-secondary text-sm"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => fetchTransfers({ page: page + 1 })}
                    disabled={page >= totalPages}
                    className="btn-secondary text-sm"
                  >
                    Next
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
