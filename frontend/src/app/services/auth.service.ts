import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment.development';
import { BehaviorSubject, catchError, map, Observable, of, Subject } from 'rxjs';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';
import { UserDTO, UserLoginRequest, UserResponse } from '../models/user.interface';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private serviceFlowApiUrl = environment.serviceFlowApiUrl;
  private subUrl = "auth";

  private currentUser = new BehaviorSubject<UserDTO | null>(null);
  public authStatus = new Subject<boolean>();

  constructor(
    private httpClient: HttpClient,
    private router: Router,
    private messageService: MessageService
  ) { }

  getAuthStatus() {
    return this.authStatus.asObservable();
  }

  getCurrentUser(): UserDTO {
    const cached = sessionStorage.getItem('currentUser')
    if (cached) {
      const token_data = JSON.parse(cached) as UserDTO;
      const user: UserDTO = {
        id: token_data.id,
        first_name: token_data.first_name || '',
        last_name: token_data.last_name || '',
        email: token_data.email,
        role: token_data.role,
        profile_picture: token_data.profile_picture,
        is_active: token_data.is_active ?? true,
        created_at: token_data.created_at
      }
      return user;
    }
    else {
      this.messageService.add({ severity: 'warn', summary: 'Logged Out', detail: `User details not found, login again` });
      this.router.navigate(['/login']);
      sessionStorage.clear();
      this.authStatus.next(false);
      return {} as UserDTO
    }
  }

  /**
   * Decode a JWT's payload without verifying its signature (verification is
   * the backend's job — this is purely to read the sub/role claims client-side).
   */
  private decodeJwtPayload(token: string): any {
    const payload = token.split('.')[1];
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64.padEnd(base64.length + (4 - (base64.length % 4)) % 4, '=');
    return JSON.parse(atob(padded));
  }

  /**
   * Logs in against the ServiceFlow AI backend (POST /auth/token), which is
   * OAuth2 form-encoded and returns only {access_token, token_type} — no
   * user object. A UserDTO-shaped object is synthesized from the JWT's
   * sub/role claims and cached, so getCurrentUser() and the navbar work
   * without needing a separate "current user" endpoint.
   */
  login(data: UserLoginRequest): Observable<UserResponse> {
    const body = new HttpParams()
      .set('username', data.email)
      .set('password', data.password);

    return this.httpClient.post<{ access_token: string; token_type: string }>(
      `${this.serviceFlowApiUrl}/${this.subUrl}/token`,
      body.toString(),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    ).pipe(
      map((response) => {
        const claims = this.decodeJwtPayload(response.access_token);
        const emailPrefix = (claims.sub as string || '').split('@')[0];

        const user: UserDTO = {
          id: 0,
          email: claims.sub,
          first_name: emailPrefix.charAt(0).toUpperCase() + emailPrefix.slice(1),
          last_name: '',
          role: claims.role,
          is_active: true,
          created_at: new Date()
        };

        this.currentUser.next(user);
        sessionStorage.setItem('currentUser', JSON.stringify(user));
        sessionStorage.setItem('token', response.access_token);
        this.authStatus.next(true);

        const loginResponse: UserResponse = {
          success: true,
          statusCode: 200,
          message: 'Logged in successfully.',
          user
        };
        return loginResponse;
      }),
      catchError((error) => {
        const loginResponse: UserResponse = {
          success: false,
          statusCode: error.status || 500,
          message: error.error?.detail || 'Invalid email address or password.'
        };
        return of(loginResponse);
      })
    );
  }

  logout(): Observable<UserResponse> {
    this.currentUser.next(null);
    this.authStatus.next(false);
    sessionStorage.clear();
    this.router.navigate(['/login']);
    return of({
      success: true,
      statusCode: 200,
      message: 'Logged out successfully'
    });
  }

  clearLocalStorage() {
    localStorage.clear()
    sessionStorage.clear()
  }

  getToken() {
    return sessionStorage.getItem('token')
  }
}
