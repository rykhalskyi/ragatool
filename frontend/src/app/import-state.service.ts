import { Injectable, OnDestroy, signal } from '@angular/core';
import { Subscription } from 'rxjs';
import { Task } from './client';
import { LogStreamService } from './log-stream.service';
import { TaskCachingService } from './task-caching.service';

export interface ImportProgressState {
  info: string;
  task?: Task;
  updatedAt: number;
}

/**
 * Keeps the latest import progress for every collection at application scope.
 *
 * The selected-collection view is destroyed and re-created while navigating,
 * so progress must not live in the component. This service is fed by the
 * application-wide SSE stream and task cache and survives navigation.
 */
@Injectable({
  providedIn: 'root',
})
export class ImportStateService implements OnDestroy {
  private readonly _states = signal<Record<string, ImportProgressState>>({});
  private readonly subscriptions = new Subscription();

  constructor(
    private readonly logStreamService: LogStreamService,
    private readonly taskCachingService: TaskCachingService,
  ) {
    this.subscriptions.add(
      this.logStreamService.logs$.subscribe(message => {
        if (message.topic === 'INFO' && message.collectionId) {
          this.update(message.collectionId, {
            info: message.message,
            updatedAt: Date.now(),
          });
        }
      })
    );

    this.subscriptions.add(
      this.taskCachingService.tasks$.subscribe(tasks => this.syncTasks(tasks))
    );

    // ImportStateService may be created after some INFO messages have already
    // arrived. Seed from the log stream cache so they are not lost.
    for (const [collectionId, info] of Object.entries(this.logStreamService.getAllInfos())) {
      this.update(collectionId, { info, updatedAt: Date.now() });
    }
  }

  getState(collectionId: string): ImportProgressState | undefined {
    return this._states()[collectionId];
  }

  clearInfo(collectionId: string): void {
    this.logStreamService.clearInfo(collectionId);
    this.update(collectionId, { info: '', updatedAt: Date.now() });
  }

  private syncTasks(tasks: Task[]): void {
    const tasksByCollection = new Map(tasks.map(task => [task.collectionId, task]));
    const removedCollections = Object.entries(this._states())
      .filter(([collectionId, state]) => state.task && !tasksByCollection.has(collectionId))
      .map(([collectionId]) => collectionId);

    this._states.update(states => {
      const next: Record<string, ImportProgressState> = { ...states };

      for (const collectionId of removedCollections) {
        const state = next[collectionId];
        if (state) {
          // The task finished or was removed; drop the last progress line so
          // an in-progress message is not shown after it is no longer true.
          next[collectionId] = {
            ...state,
            info: '',
            task: undefined,
            updatedAt: Date.now(),
          };
        }
      }

      for (const [collectionId, task] of tasksByCollection) {
        const previous = next[collectionId];
        next[collectionId] = {
          info: previous?.info ?? '',
          task,
          updatedAt: Date.now(),
        };
      }

      return next;
    });

    for (const collectionId of removedCollections) {
      this.logStreamService.clearInfo(collectionId);
    }
  }

  private update(collectionId: string, patch: Partial<ImportProgressState>): void {
    this._states.update(states => {
      const previous = states[collectionId];
      return {
        ...states,
        [collectionId]: {
          info: previous?.info ?? '',
          task: previous?.task,
          updatedAt: previous?.updatedAt ?? 0,
          ...patch,
        },
      };
    });
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }
}
