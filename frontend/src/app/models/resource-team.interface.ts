import { BaseResponse } from './shared.interface';

export interface ResourceTeamDTO {
  id: number;
  name: string;
  skills?: string[] | null;
  service_categories?: string[] | null;
  capacity: number;
  base_district_id?: number | null;
  availability_schedule?: any;
  is_active: boolean;
}

export interface ResourceTeamCreateRequest {
  name: string;
  skills?: string[];
  service_categories?: string[];
  capacity?: number;
  base_district_id?: number | null;
  is_active?: boolean;
}

export interface ResourceTeamUpdateRequest {
  name?: string;
  skills?: string[];
  service_categories?: string[];
  capacity?: number;
  base_district_id?: number | null;
  is_active?: boolean;
}

export interface ResourceTeamResponse extends BaseResponse {
  team?: ResourceTeamDTO;
  teams?: ResourceTeamDTO[];
}
