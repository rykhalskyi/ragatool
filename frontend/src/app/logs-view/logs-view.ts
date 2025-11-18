import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { MatListModule } from '@angular/material/list';
import { MatCardModule } from '@angular/material/card';
import { CommonModule } from '@angular/common';
import { LogEntry } from './log-entry.interface';
import { LogStreamService } from '../log-stream.service';
import { UntilDestroy, untilDestroyed } from '@ngneat/until-destroy';

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

  private _allLogs: LogEntry[] = [];

  get logs(): LogEntry[] {
    if (this.collectionId) {
      return this._allLogs.filter(log => log.collectionId === this.collectionId);
    }
    return this._allLogs;
  }

  constructor(private logStreamService: LogStreamService) {}

  ngOnInit(): void {
    this.logStreamService.logs$
      .pipe(untilDestroyed(this))
      .subscribe(log => {
        this.addLog(log);
      });
  }

  ngOnDestroy(): void {
    // untilDestroyed handles unsubscription
  }

  addLog(log: LogEntry) {
    this._allLogs.push(log); // Add new log to the beginning of the array
  }
}
