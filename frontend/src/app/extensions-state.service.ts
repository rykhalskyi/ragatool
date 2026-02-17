import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, catchError, of } from 'rxjs';
import { ExtensionsService } from './client/services/ExtensionsService';
import { ExtensionTool } from './client/models/ExtensionTool';

@Injectable({
  providedIn: 'root',
})
export class ExtensionsStateService {
  private _connectedExtensions = new BehaviorSubject<ExtensionTool[]>([]);
  public readonly connectedExtensions$: Observable<ExtensionTool[]> = this._connectedExtensions.asObservable();

  constructor() {
    this.fetchConnectedExtensions();
  }

  public fetchConnectedExtensions(): void {
    ExtensionsService.getConnectedExtensionToolsExtensionsConnectedToolsGet().then(res => {
      this._connectedExtensions.next(res);
    });
  }

  public updateConnectedExtensions(tools: ExtensionTool[]): void {
    this._connectedExtensions.next(tools);
  }
}
