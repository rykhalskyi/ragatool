import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { MatListModule } from '@angular/material/list';
import { MatCardModule } from '@angular/material/card';
import { CommonModule } from '@angular/common';
import { LogStreamService } from '../log-stream.service';
import { UntilDestroy, untilDestroyed } from '@ngneat/until-destroy';
import { Message } from '../client/models/Message';

@UntilDestroy()
@Component({
  selector: 'app-logs-view',
  standalone: true,
  imports: [CommonModule, MatListModule, MatCardModule],
  templateUrl: './logs-view.html',
  styleUrl: './logs-view.scss'
})
export class LogsViewComponent implements OnInit, OnDestroy {
  @Input() collectionId: string | undefined;

  private _allLogs: Message[] = [];

  get logs(): Message[] {
    if (this.collectionId) {
      return this._allLogs.filter(log => log.collectionId === this.collectionId && log.topic === 'LOG');
    }
    return this._allLogs;
  }

  constructor(private logStreamService: LogStreamService) {}

  async ngOnInit(): Promise<void> {

    const inititalLogs = await this.logStreamService.loadInitialLogs()
    inititalLogs.forEach(element => {
      this._allLogs.push(element);
    });

    this.logStreamService.logs$
      .pipe(untilDestroyed(this))
      .subscribe(log => {
        this.addLog(log);
      });
  }

  ngOnDestroy(): void {
    // untilDestroyed handles unsubscription
  }

  addLog(log: Message) {
    this._allLogs.push(log); // Add new log to the beginning of the array
  }
}
