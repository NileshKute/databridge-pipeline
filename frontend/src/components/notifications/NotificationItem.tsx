import { useNavigate } from "react-router-dom";
import {
  Bell,
  CheckCircle,
  XCircle,
  ShieldCheck,
  Send,
  AlertTriangle,
  Info,
} from "lucide-react";
import { clsx } from "clsx";
import { formatRelativeTime } from "@/utils/formatters";
import type { Notification } from "@/types";

interface Props {
  notification: Notification;
  onMarkRead: (id: number) => void;
}

const TYPE_ICONS: Record<
  string,
  { icon: typeof Bell; color: string }
> = {
  transfer_submitted: { icon: Send, color: "text-accent-cyan" },
  transfer_approved: { icon: CheckCircle, color: "text-emerald-400" },
  transfer_rejected: { icon: XCircle, color: "text-accent-rose" },
  scan_complete: { icon: ShieldCheck, color: "text-blue-400" },
  scan_failed: { icon: AlertTriangle, color: "text-accent-rose" },
  transfer_complete: { icon: CheckCircle, color: "text-accent-violet" },
  approval_needed: { icon: Bell, color: "text-accent-amber" },
  info: { icon: Info, color: "text-blue-400" },
};

export default function NotificationItem({ notification, onMarkRead }: Props) {
  const navigate = useNavigate();
  const typeConfig =
    TYPE_ICONS[notification.type] ?? { icon: Bell, color: "text-text-muted" };
  const Icon = typeConfig.icon;

  const handleClick = () => {
    if (!notification.is_read) onMarkRead(notification.id);
    if (notification.transfer_id) {
      navigate(`/transfers/${notification.transfer_id}`);
    }
  };

  return (
    <div
      onClick={handleClick}
      className={clsx(
        "flex items-start gap-3 p-4 rounded-xl border transition-colors cursor-pointer",
        notification.is_read
          ? "bg-bg-card border-surface-700 hover:bg-bg-card-hover"
          : "bg-bg-card border-l-2 border-l-accent-cyan border-t-surface-700 border-r-surface-700 border-b-surface-700 hover:bg-bg-card-hover",
      )}
    >
      <div
        className={clsx(
          "w-9 h-9 rounded-lg flex items-center justify-center shrink-0",
          notification.is_read ? "bg-surface-800" : "bg-cyan-950/40",
        )}
      >
        <Icon className={clsx("w-4.5 h-4.5", typeConfig.color)} />
      </div>
      <div className="flex-1 min-w-0">
        <p
          className={clsx(
            "text-sm",
            notification.is_read
              ? "text-text-secondary"
              : "text-text-primary font-medium",
          )}
        >
          {notification.title}
        </p>
        {notification.message && (
          <p className="text-xs text-text-muted mt-0.5 line-clamp-2">
            {notification.message}
          </p>
        )}
        <p className="text-xs text-text-muted mt-1">
          {formatRelativeTime(notification.created_at)}
        </p>
      </div>
      {!notification.is_read && (
        <div className="w-2 h-2 rounded-full bg-accent-cyan shrink-0 mt-2" />
      )}
    </div>
  );
}
