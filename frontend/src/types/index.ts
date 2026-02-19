export interface User {
  id: number;
  username: string;
  email: string;
  display_name: string;
  role: UserRole;
  department: string | null;
  is_active: boolean;
  is_ldap_user: boolean;
  last_login: string | null;
  created_at: string;
}

export type UserRole = "artist" | "lead" | "supervisor" | "producer" | "admin";

export interface Project {
  id: number;
  name: string;
  code: string;
  description: string | null;
  status: ProjectStatus;
  shotgrid_id: number | null;
  staging_path: string;
  production_path: string;
  created_at: string;
  updated_at: string;
}

export type ProjectStatus = "active" | "on_hold" | "completed" | "archived";

export interface Transfer {
  id: number;
  reference_id: string;
  project_id: number;
  created_by: number;
  approved_by: number | null;
  title: string;
  description: string | null;
  status: TransferStatus;
  priority: TransferPriority;
  source_path: string;
  destination_path: string;
  total_size_bytes: number;
  transferred_bytes: number;
  file_count: number;
  progress_percent: number;
  shotgrid_task_id: number | null;
  shotgrid_version_id: number | null;
  error_message: string | null;
  celery_task_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  files: TransferFile[];
}

export type TransferStatus =
  | "pending"
  | "validating"
  | "approved"
  | "in_progress"
  | "checksumming"
  | "completed"
  | "failed"
  | "cancelled"
  | "rejected";

export type TransferPriority = "low" | "normal" | "high" | "urgent";

export interface TransferFile {
  id: number;
  relative_path: string;
  file_size_bytes: number;
  checksum_source: string | null;
  checksum_destination: string | null;
  checksum_verified: boolean | null;
  transferred: boolean;
}

export interface TransferListItem {
  id: number;
  reference_id: string;
  project_id: number;
  created_by: number;
  title: string;
  status: TransferStatus;
  priority: TransferPriority;
  total_size_bytes: number;
  progress_percent: number;
  file_count: number;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginCredentials {
  username: string;
  password: string;
}
