import type { ReactNode } from "react";
import { useAuthStore } from "@/store/authStore";
import type { UserRole } from "@/types";

interface Props {
  roles: UserRole[];
  children: ReactNode;
  fallback?: ReactNode;
}

export default function RoleGate({ roles, children, fallback = null }: Props) {
  const { user } = useAuthStore();
  if (!user) return <>{fallback}</>;
  if (roles.includes(user.role)) return <>{children}</>;
  return <>{fallback}</>;
}
