import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';
import { CaseFilters, CaseResponse, CaseSummaryResponse, ClassificationCorrectionPayload, RouteCasePayload, StatusUpdatePayload } from '../models/case.interface';

@Injectable({
  providedIn: 'root'
})
export class CaseService {
  private baseURL = environment.serviceFlowApiUrl;
  private subUrl = 'cases';

  constructor(private httpclient: HttpClient) {}

  mapToResponse(data: any): CaseResponse {
    return {
      success: data.success,
      statusCode: data.status_code,
      message: data.message,
      errors: data.errors || null,
      case: data.case || null,
      cases: data.cases || null
    };
  }

  mapToSummaryResponse(data: any): CaseSummaryResponse {
    return {
      success: data.success,
      statusCode: data.status_code,
      message: data.message,
      errors: data.errors || null,
      counts: data.counts || null
    };
  }

  private buildFilterParams(filters?: CaseFilters): HttpParams {
    let params = new HttpParams();
    if (!filters) {
      return params;
    }
    if (filters.status) {
      params = params.set('status', filters.status);
    }
    if (filters.category) {
      params = params.set('category', filters.category);
    }
    if (filters.district_id != null) {
      params = params.set('district_id', filters.district_id);
    }
    if (filters.queue_id != null) {
      params = params.set('queue_id', filters.queue_id);
    }
    return params;
  }

  getAllCases(filters?: CaseFilters): Observable<CaseResponse> {
    return this.httpclient.get(`${this.baseURL}/${this.subUrl}/`, {
      params: this.buildFilterParams(filters)
    }).pipe(
      map((response: any) => this.mapToResponse(response))
    );
  }

  getMyCases(filters?: Pick<CaseFilters, 'status' | 'category'>): Observable<CaseResponse> {
    return this.httpclient.get(`${this.baseURL}/${this.subUrl}/mine`, {
      params: this.buildFilterParams(filters)
    }).pipe(
      map((response: any) => this.mapToResponse(response))
    );
  }

  getCaseById(id: string): Observable<CaseResponse> {
    return this.httpclient.get(`${this.baseURL}/${this.subUrl}/${id}`).pipe(
      map((response: any) => this.mapToResponse(response))
    );
  }

  getCaseSummary(groupBy: string = 'status', filters?: CaseFilters): Observable<CaseSummaryResponse> {
    const params = this.buildFilterParams(filters).set('group_by', groupBy);
    return this.httpclient.get(`${this.baseURL}/${this.subUrl}/summary`, { params }).pipe(
      map((response: any) => this.mapToSummaryResponse(response))
    );
  }

  correctClassification(caseId: string, payload: ClassificationCorrectionPayload): Observable<CaseResponse> {
    return this.httpclient.patch(`${this.baseURL}/${this.subUrl}/${caseId}/classification`, payload).pipe(
      map((response: any) => this.mapToResponse(response))
    );
  }

  routeCase(caseId: string, payload: RouteCasePayload): Observable<CaseResponse> {
    return this.httpclient.post(`${this.baseURL}/${this.subUrl}/${caseId}/route`, payload).pipe(
      map((response: any) => this.mapToResponse(response))
    );
  }

  updateCaseStatus(caseId: string, payload: StatusUpdatePayload): Observable<CaseResponse> {
    return this.httpclient.patch(`${this.baseURL}/${this.subUrl}/${caseId}/status`, payload).pipe(
      map((response: any) => this.mapToResponse(response))
    );
  }
}
