import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';
import { QueueCreateRequest, QueueResponse, QueueUpdateRequest } from '../models/queue.interface';

@Injectable({ providedIn: 'root' })
export class QueueService {
  private baseURL = environment.serviceFlowApiUrl;
  private subUrl = 'queues';

  constructor(private http: HttpClient) {}

  private mapToResponse(data: any): QueueResponse {
    return {
      success: data.success,
      statusCode: data.status_code,
      message: data.message,
      errors: data.errors || null,
      queue: data.queue || null,
      queues: data.queues || null,
    };
  }

  listQueues(activeOnly = false, unitId?: number): Observable<QueueResponse> {
    let params = new HttpParams()
      .set('limit', '500')
      .set('active_only', String(activeOnly));
    if (unitId != null) params = params.set('unit_id', unitId);
    return this.http.get(`${this.baseURL}/${this.subUrl}/`, { params }).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  getQueue(id: number): Observable<QueueResponse> {
    return this.http.get(`${this.baseURL}/${this.subUrl}/${id}`).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  createQueue(payload: QueueCreateRequest): Observable<QueueResponse> {
    return this.http.post(`${this.baseURL}/${this.subUrl}/`, payload).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  updateQueue(id: number, payload: QueueUpdateRequest): Observable<QueueResponse> {
    return this.http.put(`${this.baseURL}/${this.subUrl}/${id}`, payload).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  deactivateQueue(id: number): Observable<QueueResponse> {
    return this.http.patch(`${this.baseURL}/${this.subUrl}/${id}/deactivate`, {}).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }

  deleteQueue(id: number): Observable<QueueResponse> {
    return this.http.delete(`${this.baseURL}/${this.subUrl}/${id}`).pipe(
      map((data: any) => this.mapToResponse(data))
    );
  }
}
