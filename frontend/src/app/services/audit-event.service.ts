import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';
import { AuditEventResponse } from '../models/audit-event.interface';

@Injectable({
  providedIn: 'root'
})
export class AuditEventService {
  private baseURL = environment.serviceFlowApiUrl;
  private subUrl = 'audit-events';

  constructor(private httpclient: HttpClient) {}

  mapToResponse(data: any): AuditEventResponse {
    return {
      success: data.success,
      statusCode: data.status_code,
      message: data.message,
      errors: data.errors || null,
      event: data.event || null,
      events: data.events || null
    };
  }

  /**
   * Restricted to auditor/administrator roles on the backend (CAN_VIEW_AUDIT).
   * Callers should subscribe with an error handler that degrades gracefully
   * (e.g. hide the audit section) rather than surfacing a 403 as an error.
   */
  listForObject(objectType: string, objectId: string): Observable<AuditEventResponse> {
    const params = new HttpParams()
      .set('object_type', objectType)
      .set('object_id', objectId);
    return this.httpclient.get(`${this.baseURL}/${this.subUrl}/`, { params }).pipe(
      map((response: any) => this.mapToResponse(response))
    );
  }
}
