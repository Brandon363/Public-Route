// error.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';
import { MessageService } from 'primeng/api'; // or ngx-toastr

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const messageService = inject(MessageService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401) {
        // Don't redirect anonymous users away from the public submission page
        if (!router.url.startsWith('/submit')) {
          messageService.add({ severity: 'error', summary: 'Unauthorized', detail: 'Please login again.' });
          router.navigate(['/login']);
        }
      } else if (error.status === 403) {
        messageService.add({ severity: 'warn', summary: 'Forbidden', detail: 'Access denied.' });
      } else if (error.status === 500) {
        messageService.add({ severity: 'error', summary: 'Server Error', detail: 'Something went wrong.' });
      } else {
        messageService.add({ severity: 'error', summary: 'Error', detail: error.message });
      }

      return throwError(() => error);
    })
  );
};
