import { BaseResponse } from './shared.interface';

export interface OrganisationUnitDTO {
  id: number;
  name: string;
  jurisdiction: any[];
  service_categories: string[];
  escalation_path?: number[] | null;
  is_active: boolean;
}

export interface OrganisationUnitCreateRequest {
  name: string;
  jurisdiction?: any[];
  service_categories?: string[];
  escalation_path?: number[];
  is_active?: boolean;
}

export interface OrganisationUnitUpdateRequest {
  name?: string;
  jurisdiction?: any[];
  service_categories?: string[];
  escalation_path?: number[];
  is_active?: boolean;
}

export interface OrganisationUnitResponse extends BaseResponse {
  unit?: OrganisationUnitDTO;
  units?: OrganisationUnitDTO[];
}
