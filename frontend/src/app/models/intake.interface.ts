import { BaseResponse } from './shared.interface';
import { CaseDTO } from './case.interface';

export type ConsentStatus = 'granted' | 'declined' | 'not_required';

export interface SubmissionCreatePayload {
  channel: 'web';
  received_at: string;          // ISO datetime string
  service_description: string;
  location_text?: string | null;
  consent_status: ConsentStatus;
  district_id?: number | null;
  contact_email?: string | null;
  contact_phone?: string | null;
}

export interface SubmissionDTO {
  id: string;
  channel: string;
  received_at: string;
  service_description: string;
  location_text?: string | null;
  consent_status: string;
  district_id?: number | null;
}

export interface IntakeResponse extends BaseResponse {
  submission?: SubmissionDTO;
  case?: CaseDTO;
}
