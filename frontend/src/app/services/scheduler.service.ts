import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class SchedulerService {
  private apiUrl = 'http://localhost:5000/api/schedule';

  constructor(private http: HttpClient) { }

  generateSchedule(requestData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/generate`, { scheduling_request: requestData })
      .pipe(
        catchError(this.handleError)
      );
  }

  getSchedulesList(): Observable<any> {
    return this.http.get(`${this.apiUrl}/list`)
      .pipe(
        catchError(this.handleError)
      );
  }

  downloadSchedule(filename: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/download/${filename}`, { responseType: 'blob' })
      .pipe(
        catchError(this.handleError)
      );
  }

  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'Error desconocido';
    if (error.error instanceof ErrorEvent) {
      errorMessage = `Error: ${error.error.message}`;
    } else {
      errorMessage = `Código de Error: ${error.status}\nMensaje: ${error.message}`;
    }
    return throwError(() => new Error(errorMessage));
  }
}
