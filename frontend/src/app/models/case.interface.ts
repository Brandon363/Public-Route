import { BaseResponse } from "./shared.interface";

export interface CaseDTO {
  id: string;
  reference_number: string;
  category: string;
  subcategory?: string | null;
  urgency: string;
  status: string;
  description: string;
  english_description?: string | null;
  classification_confidence?: number | null;
  sla_deadline?: string | null;
  opened_at?: string | null;
  closed_at?: string | null;
  submission_id?: string | null;
  district_id?: number | null;
  queue_id?: number | null;
  incident_cluster_id?: string | null;
}

export interface CaseFilters {
  status?: string;
  district_id?: number;
  queue_id?: number;
  category?: string;
}

export interface CaseResponse extends BaseResponse {
  case?: CaseDTO;
  cases?: CaseDTO[];
}

export interface CaseSummaryRow {
  key: any;
  count: number;
}

export interface CaseSummaryResponse extends BaseResponse {
  counts?: CaseSummaryRow[];
}

// ── Officer action payloads ──────────────────────────────────────────────────

export interface ClassificationCorrectionPayload {
  category: string;
  subcategory?: string | null;
  urgency: 'low' | 'medium' | 'high' | 'critical';
}

export interface RouteCasePayload {
  queue_id?: number | null;
}

export interface StatusUpdatePayload {
  status: string;
  reason: string;
}

