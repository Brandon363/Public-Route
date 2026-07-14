import { BaseResponse } from './shared.interface';

export interface DistrictDTO {
  id: number;
  name: string;
  province: string;
  settlement_type: string;
  latitude?: number | null;
  longitude?: number | null;
}

export interface DistrictCreateRequest {
  name: string;
  province: string;
  settlement_type: string;
  latitude?: number | null;
  longitude?: number | null;
}

export interface DistrictUpdateRequest {
  name?: string;
  province?: string;
  settlement_type?: string;
  latitude?: number | null;
  longitude?: number | null;
}

export interface DistrictResponse extends BaseResponse {
  district?: DistrictDTO;
  districts?: DistrictDTO[];
}
