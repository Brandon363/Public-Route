import { BaseResponse } from './shared.interface';

export interface QueueDTO {
  id: number;
  unit_id: number;
  name: string;
  priority_rules?: any;
  capacity?: number | null;
  is_active: boolean;
}

export interface QueueCreateRequest {
  unit_id: number;
  name: string;
  capacity?: number | null;
  is_active?: boolean;
}

export interface QueueUpdateRequest {
  name?: string;
  capacity?: number | null;
  is_active?: boolean;
}

export interface QueueResponse extends BaseResponse {
  queue?: QueueDTO;
  queues?: QueueDTO[];
}
