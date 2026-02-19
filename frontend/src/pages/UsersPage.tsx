import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import EmptyState from "@/components/common/EmptyState";
import apiClient from "@/api/client";
import type { User } from "@/types";
import { formatDate } from "@/utils/format";

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const { data } = await apiClient.get<User[]>("/users/");
        setUsers(data);
      } catch {
        /* empty */
      } finally {
        setIsLoading(false);
      }
    };
    fetchUsers();
  }, []);

  const roleColors: Record<string, string> = {
    admin: "bg-red-500/20 text-red-400",
    supervisor: "bg-purple-500/20 text-purple-400",
    producer: "bg-blue-500/20 text-blue-400",
    lead: "bg-amber-500/20 text-amber-400",
    artist: "bg-surface-500/20 text-surface-400",
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-surface-100">Users</h1>
        <p className="text-surface-400 mt-1">Studio users with access to DataBridge.</p>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : users.length === 0 ? (
        <EmptyState title="No users" description="Users are created automatically on first LDAP login." icon={Users} />
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-700 text-surface-400">
                <th className="text-left py-3 px-4 font-medium">User</th>
                <th className="text-left py-3 px-4 font-medium">Role</th>
                <th className="text-left py-3 px-4 font-medium">Department</th>
                <th className="text-left py-3 px-4 font-medium">Status</th>
                <th className="text-left py-3 px-4 font-medium">Last Login</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-surface-800 hover:bg-surface-800/50 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-full bg-brand-700 flex items-center justify-center text-xs font-bold text-white">
                        {u.display_name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="text-surface-200 font-medium">{u.display_name}</p>
                        <p className="text-surface-400 text-xs">{u.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`badge ${roleColors[u.role] ?? roleColors.artist}`}>{u.role}</span>
                  </td>
                  <td className="py-3 px-4 text-surface-300">{u.department ?? "—"}</td>
                  <td className="py-3 px-4">
                    {u.is_active ? (
                      <span className="badge bg-emerald-500/20 text-emerald-400">Active</span>
                    ) : (
                      <span className="badge bg-surface-500/20 text-surface-400">Inactive</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-surface-400 text-xs">
                    {u.last_login ? formatDate(u.last_login) : "Never"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
