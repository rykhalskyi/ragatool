import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Task }from '../client/models/Task';
import { TaskCachingService } from '../task-caching.service';
import { TasksService } from '../client/services/TasksService';

@Injectable({
  providedIn: 'root'
})
export class TaskCenterService {
  private readonly _tasks = new BehaviorSubject<Task[]>([]);
  public readonly tasks$ = this._tasks.asObservable();

  constructor(
    private readonly taskCachingService: TaskCachingService
  ) {
    this.taskCachingService.tasks$.subscribe(tasks => this._tasks.next(tasks));
  }

  public cancelTask(taskId: string) {
    return TasksService.deleteTaskTasksTasksTaskIdDelete(taskId);
  }
}
