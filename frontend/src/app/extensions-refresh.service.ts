import { Injectable } from '@angular/core';
import { LogStreamService } from './log-stream.service';
import { ExtensionsStateService } from './extensions-state.service';
import { UntilDestroy, untilDestroyed } from '@ngneat/until-destroy';
import { filter } from 'rxjs/operators';
import { Message } from './client/models/Message'; // Assuming Message model is available

@UntilDestroy()
@Injectable({
  providedIn: 'root',
})
export class ExtensionsRefreshService {
  constructor(
    private logStreamService: LogStreamService,
    private extensionsStateService: ExtensionsStateService
  ) {
    this.logStreamService.logs$
      .pipe(
        untilDestroyed(this),
        filter((message: Message) => {
          // Filter messages relevant to extension tool connections/disconnections
          // This needs to be refined based on actual backend message format
          // Assuming messages related to extensions have a specific structure or content like "ExtensionTool connected" or "ExtensionTool disconnected"
          return message.message.includes('ExtensionTool') &&
                 (message.message.includes('connected') || message.message.includes('disconnected'));
        })
      )
      .subscribe((message: Message) => {
        console.log('SSE Message for Extensions:', message);
        // Trigger a re-fetch of the connected extensions from the ExtensionsStateService
        // In a real-world scenario, the SSE message might carry the updated list or the specific tool that changed,
        // which would allow for a more precise update using extensionsStateService.updateConnectedExtensions()
        // For now, we trigger a full re-fetch to ensure data consistency.
        this.extensionsStateService.fetchConnectedExtensions();
      });
  }
}
