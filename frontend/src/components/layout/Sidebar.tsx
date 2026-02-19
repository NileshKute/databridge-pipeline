import { NavLink } from "react-router-dom";
import { clsx } from "clsx";
import {
  LayoutDashboard,
  ArrowRightLeft,
  FolderKanban,
  Users,
  Shield,
  LogOut,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Transfers", href: "/transfers", icon: ArrowRightLeft },
  { name: "Projects", href: "/projects", icon: FolderKanban },
  { name: "Users", href: "/users", icon: Users },
  { name: "Audit Log", href: "/audit", icon: Shield },
];

export default function Sidebar() {
  const { user, logout } = useAuthStore();

  return (
    <aside className="flex flex-col w-64 bg-surface-900 border-r border-surface-700 min-h-screen">
      <div className="flex items-center gap-3 px-5 py-5 border-b border-surface-700">
        <div className="h-9 w-9 rounded-lg bg-brand-600 flex items-center justify-center">
          <ArrowRightLeft className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-sm font-semibold text-surface-100">DataBridge</h1>
          <p className="text-xs text-surface-400">Pipeline</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            end={item.href === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-brand-600/20 text-brand-400"
                  : "text-surface-400 hover:text-surface-100 hover:bg-surface-800",
              )
            }
          >
            <item.icon className="h-5 w-5" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 py-4 border-t border-surface-700">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="h-8 w-8 rounded-full bg-brand-700 flex items-center justify-center text-xs font-bold text-white">
            {user?.display_name?.charAt(0).toUpperCase() ?? "?"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-surface-200 truncate">{user?.display_name}</p>
            <p className="text-xs text-surface-400 truncate">{user?.role}</p>
          </div>
          <button
            onClick={logout}
            className="p-1.5 text-surface-400 hover:text-red-400 rounded transition-colors"
            title="Sign out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
