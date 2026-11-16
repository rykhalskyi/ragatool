import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Subscription } from 'rxjs';
import { Task } from './client';
import { TasksService } from './client';
import { LogStreamService } from './log-stream.service';

@Injectable({
  providedIn: 'root',
})
export class TaskCachingService implements OnDestroy {
  private readonly tasksSubject = new BehaviorSubject<Task[]>([]);
  readonly tasks$ = this.tasksSubject.asObservable();

  private tasks: Task[] = [];
  private readonly logSubscription: Subscription;
  private refreshInFlight: Promise<void> | null = null;
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private readonly pollIntervalMs = 5000;

  private readonly onVisibilityChange = (): void => {
    if (document.visibilityState === 'visible') {
      void this.refresh();
    }
  };

  constructor(private logStreamService: LogStreamService) {
    this.logSubscription = this.logStreamService.logs$.subscribe(message => {
      if (message.topic === 'TASK') {
        void this.refreshAfterTaskEvent();
      }
    });

    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', this.onVisibilityChange);
    }

    void this.refresh();
  }

  /**
   * Refetches the task list from the backend. Concurrent callers share the
   * same request. This is the source of truth when returning from navigation
   * or after an SSE reconnect where events may have been missed.
   */
  refresh(): Promise<void> {
    if (!this.refreshInFlight) {
      this.refreshInFlight = this.fetchTasks().finally(() => {
        this.refreshInFlight = null;
      });
    }
    return this.refreshInFlight;
  }

  getTaskByCollectionId(collectionId: string): Task | undefined {
    return this.tasks.find(task => task.collectionId === collectionId);
  }

  /**
   * A task can start and finish between two polls, leaving the task list
   * unchanged ([] -> []). Views still need a notification so they can refresh
   * prepared files/chunks after the task, so always emit on TASK events.
   */
  private async refreshAfterTaskEvent(): Promise<void> {
    // An in-flight fetch may have started before this event, so its response
    // can be stale. Wait for it, then fetch again so the event is guaranteed
    // to be reflected in the emitted task list.
    await this.refreshInFlight;
    await this.refresh();
    this.tasksSubject.next([...this.tasks]);
  }

  private async fetchTasks(): Promise<void> {
    try {
      const tasks = await TasksService.getTasksTasksTasksGet();
      const changed = this.tasksChanged(tasks);
      this.tasks = tasks;

      if (changed) {
        this.tasksSubject.next(tasks);
      }

      this.updatePolling();
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  }

  private tasksChanged(next: Task[]): boolean {
    if (next.length !== this.tasks.length) {
      return true;
    }

    const previousById = new Map(this.tasks.map(task => [task.id, task]));
    return next.some(task => {
      const previous = previousById.get(task.id);
      return !previous
        || previous.collectionId !== task.collectionId
        || previous.name !== task.name
        || previous.startTime !== task.startTime
        || previous.status !== task.status;
    });
  }

  private updatePolling(): void {
    const shouldPoll = this.tasks.length > 0;

    if (shouldPoll && this.pollTimer === null) {
      this.pollTimer = setInterval(() => {
        void this.refresh();
      }, this.pollIntervalMs);
    } else if (!shouldPoll && this.pollTimer !== null) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  ngOnDestroy(): void {
    this.logSubscription.unsubscribe();

    if (this.pollTimer !== null) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }

    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', this.onVisibilityChange);
    }
  }
}
