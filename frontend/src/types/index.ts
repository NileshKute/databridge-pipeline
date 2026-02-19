export type UserRole =
  | "artist"
  | "team_lead"
  | "supervisor"
  | "line_producer"
  | "data_team"
  | "it_team"
  | "admin";

export interface User {
  id: number;
  username: string;
  display_name: string;
  email: string;
  role: UserRole;
  department: string | null;
  title: string | null;
  is_active: boolean;
  shotgrid_user_id: number | null;
  last_login: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export type TransferStatus =
  | "uploaded"
  | "pending_team_lead"
  | "pending_supervisor"
  | "pending_line_producer"
  | "approved"
  | "scanning"
  | "scan_passed"
  | "scan_failed"
  | "copying"
  | "ready_for_transfer"
  | "transferring"
  | "verifying"
  | "transferred"
  | "rejected"
  | "cancelled";

export type TransferPriority = "low" | "normal" | "high" | "urgent";

export type TransferCategory =
  | "vfx_assets"
  | "animation"
  | "textures"
  | "lighting"
  | "compositing"
  | "audio"
  | "editorial"
  | "matchmove"
  | "fx"
  | "other";

export type ApprovalStatus = "pending" | "approved" | "rejected" | "skipped";

export interface TransferFile {
  id: number;
  filename: string;
  size_bytes: number;
  checksum_sha256: string | null;
  virus_scan_status: string;
  uploaded_at: string;
}

export interface ApprovalChainItem {
  role: UserRole;
  status: ApprovalStatus;
  approver_name: string | null;
  comment: string | null;
  decided_at: string | null;
}

export interface Transfer {
  id: number;
  reference: string;
  name: string;
  description: string | null;
  category: TransferCategory | null;
  status: TransferStatus;
  priority: TransferPriority;
  artist_id: number;
  artist_name: string;
  total_files: number;
  total_size_bytes: number;
  staging_path: string | null;
  production_path: string | null;
  shotgrid_project_id: number | null;
  shotgrid_entity_type: string | null;
  shotgrid_entity_id: number | null;
  shotgrid_entity_name: string | null;
  shotgrid_task_id: number | null;
  shotgrid_version_id: number | null;
  scan_started_at: string | null;
  scan_completed_at: string | null;
  scan_result: Record<string, unknown> | null;
  scan_passed: boolean | null;
  transfer_started_at: string | null;
  transfer_completed_at: string | null;
  transfer_verified: boolean | null;
  transfer_method: string | null;
  notes: string | null;
  rejection_reason: string | null;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
  files: TransferFile[];
  approval_chain: ApprovalChainItem[];
  size_display: string;
}

export interface TransferListResponse {
  items: Transfer[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface TransferStats {
  total: number;
  pending: number;
  approved: number;
  scanning: number;
  transferred: number;
  rejected: number;
  avg_time_hours: number | null;
}

export interface Notification {
  id: number;
  transfer_id: number | null;
  type: string;
  title: string;
  message: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
  unread_count: number;
}

export interface HistoryEntry {
  id: number;
  transfer_id: number;
  user_id: number | null;
  action: string;
  description: string | null;
  metadata_json: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}
