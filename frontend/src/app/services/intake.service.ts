import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';
import { IntakeResponse, SubmissionCreatePayload } from '../models/intake.interface';

@Injectable({ providedIn: 'root' })
export class IntakeService {
  private baseURL = environment.serviceFlowApiUrl;

  constructor(private http: HttpClient) {}

  createSubmission(payload: SubmissionCreatePayload): Observable<IntakeResponse> {
    return this.http.post(`${this.baseURL}/intake/submissions`, payload).pipe(
      map((data: any) => ({
        success: data.success,
        statusCode: data.status_code,
        message: data.message,
        errors: data.errors || null,
        submission: data.submission || null,
        case: data.case || null,
      } as IntakeResponse))
    );
  }

  sendVoiceMessage(audioFile: File, accumulatedDescription: string, accumulatedLocation: string): Observable<any> {
    const formData = new FormData();
    formData.append('audio', audioFile, audioFile.name || 'voice.webm');
    formData.append('accumulated_description', accumulatedDescription);
    formData.append('accumulated_location', accumulatedLocation);

    return this.http.post<any>(`${this.baseURL}/intake/voice-chat`, formData);
  }
}
