export interface BaseResponse {
  statusCode: number;
  success: boolean;
  message: string;
  errors?: ErrorDetail[] | null;
}

export interface ErrorDetail {
  field: string;
  message: string;
}
