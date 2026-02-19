import { useEffect } from "react";
import { CheckCheck } from "lucide-react";
import PageHeader from "@/components/common/PageHeader";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import EmptyState from "@/components/common/EmptyState";
import NotificationItem from "@/components/notifications/NotificationItem";
import { useNotificationStore } from "@/store/notificationStore";

export default function NotificationsPage() {
  const {
    notifications,
    unreadCount,
    isLoading,
    fetchNotifications,
    markAsRead,
    markAllRead,
  } = useNotificationStore();

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  return (
    <div>
      <PageHeader
        title="Notifications"
        subtitle={
          unreadCount > 0 ? `${unreadCount} unread` : "All caught up"
        }
      >
        {unreadCount > 0 && (
          <button
            onClick={markAllRead}
            className="btn-secondary flex items-center gap-1.5 text-sm"
          >
            <CheckCheck className="w-4 h-4" />
            Mark all read
          </button>
        )}
      </PageHeader>

      {isLoading ? (
        <div className="py-16">
          <LoadingSpinner />
        </div>
      ) : notifications.length === 0 ? (
        <EmptyState
          title="No notifications"
          description="You're all caught up!"
        />
      ) : (
        <div className="space-y-2 max-w-2xl">
          {notifications.map((n) => (
            <NotificationItem
              key={n.id}
              notification={n}
              onMarkRead={markAsRead}
            />
          ))}
        </div>
      )}
    </div>
  );
}
