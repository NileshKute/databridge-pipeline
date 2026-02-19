import { useEffect } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useNotificationStore } from "@/store/notificationStore";
import { useApprovalStore } from "@/store/approvalStore";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import Sidebar from "./Sidebar";

export default function AppLayout() {
  const { isAuthenticated, isLoading, user } = useAuthStore();
  const { fetchUnreadCount } = useNotificationStore();
  const { fetchPendingCount } = useApprovalStore();

  useEffect(() => {
    if (!user) return;
    fetchUnreadCount();
    fetchPendingCount();

    const interval = setInterval(() => {
      fetchUnreadCount();
      fetchPendingCount();
    }, 30_000);

    return () => clearInterval(interval);
  }, [user, fetchUnreadCount, fetchPendingCount]);

  if (isLoading && !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-primary">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-text-muted text-sm">Loading DataBridge...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-bg-primary">
      <Sidebar />
      <main className="ml-[260px] p-8 min-h-screen">
        <Outlet />
      </main>
    </div>
  );
}
