import { Component, ChangeDetectionStrategy, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { Task } from '../client/models/Task';
import { TaskCenterService } from './task-center.service';
import { Subscription, from } from 'rxjs';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-task-center',
  standalone: true,
  imports: [CommonModule, MatListModule, MatIconModule, MatButtonModule],
  templateUrl: './task-center.component.html',
  styleUrls: ['./task-center.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TaskCenterComponent implements OnDestroy {
  public tasks: Task[] = [];
  private tasksSubscription: Subscription;

  constructor(
    private readonly taskCenterService: TaskCenterService,
    private readonly cdr: ChangeDetectorRef,
    ) {
    this.tasksSubscription = this.taskCenterService.tasks$.subscribe(tasks => {
      this.tasks = tasks;
      this.cdr.markForCheck();
    });
  }

  ngOnDestroy() {
    this.tasksSubscription.unsubscribe();
  }

  public async cancelTask(taskId: string) {
    await this.taskCenterService.cancelTask(taskId);
  }
}
