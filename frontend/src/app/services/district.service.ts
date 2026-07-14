import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';
import { DistrictCreateRequest, DistrictResponse, DistrictUpdateRequest } from '../models/district.interface';

@Injectable({ providedIn: 'root' })
export class DistrictService {
  private baseURL = environment.serviceFlowApiUrl;
  private subUrl = 'districts';

  constructor(private http: HttpClient) {}

  private mapToResponse(data: any): DistrictResponse {
    return {
      success: data.success,
      statusCode: data.status_code,
      message: data.message,
      errors: data.errors || null,
      district: data.district || null,
      districts: data.districts || null,
    };
  }

  listDistricts(province?: string): Observable<DistrictResponse> {
    let params = new HttpParams().set('limit', '500');
    if (province) params = params.set('province', province);
    return this.http.get(`${this.baseURL}/${this.subUrl}/`, { params }).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  getDistrict(id: number): Observable<DistrictResponse> {
    return this.http.get(`${this.baseURL}/${this.subUrl}/${id}`).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  createDistrict(payload: DistrictCreateRequest): Observable<DistrictResponse> {
    return this.http.post(`${this.baseURL}/${this.subUrl}/`, payload).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  updateDistrict(id: number, payload: DistrictUpdateRequest): Observable<DistrictResponse> {
    return this.http.put(`${this.baseURL}/${this.subUrl}/${id}`, payload).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  deleteDistrict(id: number): Observable<DistrictResponse> {
    return this.http.delete(`${this.baseURL}/${this.subUrl}/${id}`).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }
}
