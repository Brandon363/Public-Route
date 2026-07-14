import { BaseResponse } from "./shared.interface";

export interface AuditEventDTO {
  id: string;
  actor_user_id?: number | null;
  // Resolved server-side (User.full_name or email) — never a bare ID.
  actor_name?: string | null;
  actor_channel?: string | null;
  action: string;
  object_type: string;
  object_id: string;
  before_hash?: string | null;
  after_hash?: string | null;
  ip_address?: string | null;
  // Human-readable, non-PII summary of what changed (shape depends on
  // `action` — see case-detail.component.ts's describeEventChange()).
  detail?: Record<string, any> | null;
  timestamp: string;
}

export interface AuditEventResponse extends BaseResponse {
  event?: AuditEventDTO;
  events?: AuditEventDTO[];
}
