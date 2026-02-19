import { useEffect, useState } from "react";
import { Shield } from "lucide-react";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import EmptyState from "@/components/common/EmptyState";
import apiClient from "@/api/client";
import { formatDate } from "@/utils/format";

interface AuditEntry {
  id: number;
  user_id: number;
  action: string;
  resource_type: string;
  resource_id: number | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const { data } = await apiClient.get<AuditEntry[]>("/audit/", {
          params: { limit: 100 },
        });
        setEntries(data);
      } catch {
        /* audit endpoint may not exist yet */
      } finally {
        setIsLoading(false);
      }
    };
    fetchLogs();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-surface-100">Audit Log</h1>
        <p className="text-surface-400 mt-1">Track all actions performed within DataBridge.</p>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : entries.length === 0 ? (
        <EmptyState title="No audit entries" description="Actions will appear here once users start using the system." icon={Shield} />
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-700 text-surface-400">
                <th className="text-left py-3 px-4 font-medium">Time</th>
                <th className="text-left py-3 px-4 font-medium">Action</th>
                <th className="text-left py-3 px-4 font-medium">Resource</th>
                <th className="text-left py-3 px-4 font-medium">User</th>
                <th className="text-left py-3 px-4 font-medium">IP</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id} className="border-b border-surface-800">
                  <td className="py-3 px-4 text-surface-400 text-xs whitespace-nowrap">
                    {formatDate(entry.created_at)}
                  </td>
                  <td className="py-3 px-4 text-brand-400 font-mono text-xs">{entry.action}</td>
                  <td className="py-3 px-4 text-surface-300 text-xs">
                    {entry.resource_type}
                    {entry.resource_id ? ` #${entry.resource_id}` : ""}
                  </td>
                  <td className="py-3 px-4 text-surface-300 text-xs">User #{entry.user_id}</td>
                  <td className="py-3 px-4 text-surface-500 text-xs">{entry.ip_address ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
