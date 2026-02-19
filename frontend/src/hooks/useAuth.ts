import { useAuthStore } from "@/store/authStore";
import type { TransferStatus, UserRole } from "@/types";

export function useAuth() {
  const { user, isAuthenticated, isLoading, login, logout } = useAuthStore();
  return { user, isAuthenticated, isLoading, login, logout };
}

const APPROVAL_ROLES: Record<string, UserRole> = {
  pending_team_lead: "team_lead",
  pending_supervisor: "supervisor",
  pending_line_producer: "line_producer",
};

const PROCESS_ROLES: Record<string, UserRole[]> = {
  approved: ["data_team", "admin"],
  scanning: ["data_team", "admin"],
  scan_passed: ["data_team", "admin"],
  ready_for_transfer: ["it_team", "admin"],
  transferring: ["it_team", "admin"],
  verifying: ["it_team", "admin"],
};

export function useRole() {
  const { user } = useAuthStore();
  const role = user?.role ?? "artist";

  return {
    role,
    isArtist: role === "artist",
    isTeamLead: role === "team_lead",
    isSupervisor: role === "supervisor",
    isLineProducer: role === "line_producer",
    isDataTeam: role === "data_team",
    isIT: role === "it_team",
    isAdmin: role === "admin",

    canApprove: (status: TransferStatus) => {
      if (role === "admin") return true;
      const required = APPROVAL_ROLES[status];
      return required === role;
    },

    canProcess: (status: TransferStatus) => {
      if (role === "admin") return true;
      const allowed = PROCESS_ROLES[status];
      return allowed ? allowed.includes(role as UserRole) : false;
    },
  };
}
