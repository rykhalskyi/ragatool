
import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, Subscription, switchMap } from 'rxjs';
import { Task } from './client';
import { TasksService } from './client';
import { LogStreamService } from './log-stream.service';

@Injectable({
  providedIn: 'root',
})

export class TaskCachingService implements OnDestroy {
  private tasksSubject = new BehaviorSubject<Task[]>([]);
  tasks$ = this.tasksSubject.asObservable();
  private logSubscription: Subscription;
  private tasks: Task[] = [];

  constructor(
    private logStreamService: LogStreamService
  ) {
    
    this.logSubscription = this.logStreamService.logs$
      .pipe(
        switchMap(async (message) => {
          if (message.topic === 'TASK') {
            const tasks = await TasksService.getTasksTasksTasksGet();
            this.tasks = tasks;
            this.tasksSubject.next(this.tasks);
          }
        })
      )
      .subscribe(() => {
      });

    this.fetchTasks();
  }

  private async fetchTasks(): Promise<void> {
    this.tasks = await TasksService.getTasksTasksTasksGet();
    this.tasksSubject.next(this.tasks);
  }

  getTaskByCollectionId(collectionId: string): Task | undefined {
    console.log('getTask', collectionId);
    console.log('all tasks', this.tasksSubject.getValue(), this.tasks);
    return this.tasksSubject.getValue().find(task => task.collectionId === collectionId);
  }

  ngOnDestroy(): void {
    this.logSubscription.unsubscribe();
  }
}
