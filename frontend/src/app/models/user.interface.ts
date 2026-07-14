import { BaseResponse } from "./shared.interface";

export interface UserDTO {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role?: string;
  profile_picture?: string;
  is_active: boolean;
  created_at: Date;
}

export interface UserLoginRequest {
  email: string;
  password: string;
}

export interface UserResponse extends BaseResponse {
  user?: UserDTO;
  users?: UserDTO[];
}
