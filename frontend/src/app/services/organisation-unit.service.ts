import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';
import { OrganisationUnitCreateRequest, OrganisationUnitResponse, OrganisationUnitUpdateRequest } from '../models/organisation-unit.interface';

@Injectable({ providedIn: 'root' })
export class OrganisationUnitService {
  private baseURL = environment.serviceFlowApiUrl;
  private subUrl = 'organisation-units';

  constructor(private http: HttpClient) {}

  private mapToResponse(data: any): OrganisationUnitResponse {
    return {
      success: data.success,
      statusCode: data.status_code,
      message: data.message,
      errors: data.errors || null,
      unit: data.unit || null,
      units: data.units || null,
    };
  }

  listUnits(activeOnly = false): Observable<OrganisationUnitResponse> {
    const params = new HttpParams()
      .set('limit', '500')
      .set('active_only', String(activeOnly));
    return this.http.get(`${this.baseURL}/${this.subUrl}/`, { params }).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  getUnit(id: number): Observable<OrganisationUnitResponse> {
    return this.http.get(`${this.baseURL}/${this.subUrl}/${id}`).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  createUnit(payload: OrganisationUnitCreateRequest): Observable<OrganisationUnitResponse> {
    return this.http.post(`${this.baseURL}/${this.subUrl}/`, payload).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  updateUnit(id: number, payload: OrganisationUnitUpdateRequest): Observable<OrganisationUnitResponse> {
    return this.http.put(`${this.baseURL}/${this.subUrl}/${id}`, payload).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  deactivateUnit(id: number): Observable<OrganisationUnitResponse> {
    return this.http.patch(`${this.baseURL}/${this.subUrl}/${id}/deactivate`, {}).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  deleteUnit(id: number): Observable<OrganisationUnitResponse> {
    return this.http.delete(`${this.baseURL}/${this.subUrl}/${id}`).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }
}
