import { NavLink } from "react-router-dom";
import {
  Bell,
  CheckCircle,
  FolderSync,
  LayoutDashboard,
  LogOut,
  ScrollText,
  Upload,
} from "lucide-react";
import { clsx } from "clsx";
import { useAuthStore } from "@/store/authStore";
import { useNotificationStore } from "@/store/notificationStore";
import { useApprovalStore } from "@/store/approvalStore";
import { useRole } from "@/hooks/useAuth";
import { ROLE_CONFIG } from "@/utils/constants";

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
  visible: boolean;
}

export default function Sidebar() {
  const { user, logout } = useAuthStore();
  const { unreadCount } = useNotificationStore();
  const { pendingCount } = useApprovalStore();
  const { role, isArtist, isAdmin } = useRole();

  const showApprovals =
    !isArtist ||
    isAdmin;

  const navItems: NavItem[] = [
    {
      to: "/dashboard",
      label: "Dashboard",
      icon: LayoutDashboard,
      visible: true,
    },
    {
      to: "/transfers",
      label: "Transfers",
      icon: FolderSync,
      visible: true,
    },
    {
      to: "/upload",
      label: "Upload",
      icon: Upload,
      visible: isArtist || isAdmin,
    },
    {
      to: "/approvals",
      label: "Approvals",
      icon: CheckCircle,
      badge: pendingCount,
      visible: showApprovals,
    },
    {
      to: "/notifications",
      label: "Notifications",
      icon: Bell,
      badge: unreadCount,
      visible: true,
    },
    {
      to: "/activity",
      label: "Activity Log",
      icon: ScrollText,
      visible: true,
    },
  ];

  const initials = user?.display_name
    ? user.display_name
        .split(" ")
        .map((w) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "??";

  const roleConfig = ROLE_CONFIG[role] ?? { label: role, color: "cyan" };

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-[260px] bg-bg-secondary border-r border-surface-700 flex flex-col z-40">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-surface-700">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-white font-bold text-sm font-mono shrink-0">
          D
        </div>
        <span className="text-lg font-bold text-text-primary tracking-tight">
          Data<span className="text-accent-cyan">Bridge</span>
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems
          .filter((item) => item.visible)
          .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150",
                  isActive
                    ? "bg-cyan-950/60 text-accent-cyan"
                    : "text-text-secondary hover:text-text-primary hover:bg-surface-800/50",
                )
              }
            >
              <item.icon className="w-5 h-5 shrink-0" />
              <span className="flex-1">{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="bg-accent-cyan/20 text-accent-cyan text-xs font-bold px-2 py-0.5 rounded-full min-w-[20px] text-center">
                  {item.badge > 99 ? "99+" : item.badge}
                </span>
              )}
            </NavLink>
          ))}
      </nav>

      {/* User section */}
      <div className="border-t border-surface-700 p-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-cyan-400 to-violet-500 flex items-center justify-center text-white text-xs font-bold shrink-0">
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-text-primary truncate">
              {user?.display_name ?? "Loading..."}
            </p>
            <p className="text-xs text-text-muted truncate">{roleConfig.label}</p>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-text-muted hover:text-accent-rose hover:bg-rose-950/30 transition-colors"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
