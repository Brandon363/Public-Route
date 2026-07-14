import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';
import { ResourceTeamCreateRequest, ResourceTeamResponse, ResourceTeamUpdateRequest } from '../models/resource-team.interface';

@Injectable({ providedIn: 'root' })
export class ResourceTeamService {
  private baseURL = environment.serviceFlowApiUrl;
  private subUrl = 'resource-teams';

  constructor(private http: HttpClient) {}

  private mapToResponse(data: any): ResourceTeamResponse {
    return {
      success: data.success,
      statusCode: data.status_code,
      message: data.message,
      errors: data.errors || null,
      team: data.team || null,
      teams: data.teams || null,
    };
  }

  listTeams(activeOnly = false, districtId?: number): Observable<ResourceTeamResponse> {
    let params = new HttpParams()
      .set('limit', '500')
      .set('active_only', String(activeOnly));
    if (districtId != null) params = params.set('district_id', districtId);
    return this.http.get(`${this.baseURL}/${this.subUrl}/`, { params }).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  getTeam(id: number): Observable<ResourceTeamResponse> {
    return this.http.get(`${this.baseURL}/${this.subUrl}/${id}`).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  createTeam(payload: ResourceTeamCreateRequest): Observable<ResourceTeamResponse> {
    return this.http.post(`${this.baseURL}/${this.subUrl}/`, payload).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  updateTeam(id: number, payload: ResourceTeamUpdateRequest): Observable<ResourceTeamResponse> {
    return this.http.put(`${this.baseURL}/${this.subUrl}/${id}`, payload).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  deactivateTeam(id: number): Observable<ResourceTeamResponse> {
    return this.http.patch(`${this.baseURL}/${this.subUrl}/${id}/deactivate`, {}).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  deleteTeam(id: number): Observable<ResourceTeamResponse> {
    return this.http.delete(`${this.baseURL}/${this.subUrl}/${id}`).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }
}
