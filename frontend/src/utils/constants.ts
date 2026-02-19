export const STATUS_CONFIG = {
  uploaded: { label: "Uploaded", color: "cyan", dotPulse: false },
  pending_team_lead: { label: "Pending Team Lead", color: "amber", dotPulse: false },
  pending_supervisor: { label: "Pending Supervisor", color: "amber", dotPulse: false },
  pending_line_producer: { label: "Pending Line Producer", color: "amber", dotPulse: false },
  approved: { label: "Approved", color: "emerald", dotPulse: false },
  scanning: { label: "Scanning", color: "blue", dotPulse: true },
  scan_passed: { label: "Scan Passed", color: "emerald", dotPulse: false },
  scan_failed: { label: "Scan Failed", color: "rose", dotPulse: false },
  copying: { label: "Copying", color: "blue", dotPulse: true },
  ready_for_transfer: { label: "Ready for Transfer", color: "cyan", dotPulse: false },
  transferring: { label: "Transferring", color: "blue", dotPulse: true },
  verifying: { label: "Verifying", color: "blue", dotPulse: true },
  transferred: { label: "Transferred", color: "violet", dotPulse: false },
  rejected: { label: "Rejected", color: "rose", dotPulse: false },
  cancelled: { label: "Cancelled", color: "gray", dotPulse: false },
} as const;

export const ROLE_CONFIG: Record<string, { label: string; color: string }> = {
  artist: { label: "Artist", color: "cyan" },
  team_lead: { label: "Team Lead", color: "amber" },
  supervisor: { label: "Supervisor", color: "emerald" },
  line_producer: { label: "Line Producer", color: "violet" },
  data_team: { label: "Data Team", color: "blue" },
  it_team: { label: "IT Team", color: "rose" },
  admin: { label: "Admin", color: "amber" },
};

export const CATEGORY_OPTIONS = [
  { value: "vfx_assets", label: "VFX Assets" },
  { value: "animation", label: "Animation" },
  { value: "textures", label: "Textures" },
  { value: "lighting", label: "Lighting" },
  { value: "compositing", label: "Compositing" },
  { value: "audio", label: "Audio" },
  { value: "editorial", label: "Editorial" },
  { value: "matchmove", label: "Matchmove" },
  { value: "fx", label: "FX" },
  { value: "other", label: "Other" },
];

export const PRIORITY_OPTIONS = [
  { value: "low", label: "Low" },
  { value: "normal", label: "Normal" },
  { value: "high", label: "High" },
  { value: "urgent", label: "Urgent" },
];
