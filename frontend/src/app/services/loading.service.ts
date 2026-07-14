import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LoadingService {
  private _isManipulatingData = new BehaviorSubject<boolean>(false);
  isManipulatingData$ = this._isManipulatingData.asObservable();

  constructor() { }

  setLoadingState(isLoading: boolean) {
    this._isManipulatingData.next(isLoading);
  }
  
}
