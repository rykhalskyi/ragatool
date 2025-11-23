import { Injectable, NgZone } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { environment } from '../environments/environment';
import { LogsService } from './client/services/LogsService'; // Import the generated LogsService
import { Message } from './client/models/Message';

@Injectable({
  providedIn: 'root'
})
export class LogStreamService {
  private logSubject: Subject<Message> = new Subject<Message>();
  private eventSource: EventSource | undefined;
  private readonly SSE_URL = `${environment.apiUrl}/logs/stream`;

  private infos: StringDictionary = {};

  public logs$: Observable<Message> = this.logSubject.asObservable();

  constructor(private ngZone: NgZone) { // Inject LogsService
    console.log('Service constructor');
    this.connect();
  }

  private connect(): void {
    if (typeof EventSource !== 'undefined') {
      
      this.eventSource = new EventSource(this.SSE_URL);

      this.eventSource.onmessage = (event) => {
        this.ngZone.run(() => {
          const data = JSON.parse(event.data);
          const message = data as Message;
          console.log('-- Incomming message --', message);

          if (message.topic==='INFO' && message.collectionId)
          {
            this.infos[message.collectionId] = message.message;
          }

          this.logSubject.next(message);
        });
      };

      this.eventSource.onerror = (error) => {
        console.error('EventSource failed:', error);
        this.eventSource?.close();
        setTimeout(() => this.connect(), 5000); // Reconnect after 5 seconds
      };

      this.eventSource.onopen = () => {
        console.log('SSE connection opened.');
      };
      
    } else {
      console.warn('EventSource is not supported in this browser.');
    }

    
  }

  closeConnection(): void {
    this.eventSource?.close();
    console.log('SSE connection closed.');
  }

  getInfo(collectionId: string){
    return this.infos[collectionId];
  }

  async loadInitialLogs(): Promise<Message[]>{
    try{
      const logs = await LogsService.readLogsLogsGet(25);      
      return logs;
    }
    catch (e) {
      console.error('FAIL load logs',e);
      return [];
    }
    
  }

}


interface StringDictionary {
  [key: string]: string;
}