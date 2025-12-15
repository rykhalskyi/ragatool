import { TestBed } from '@angular/core/testing';
import { TaskCenterService } from './task-center.service';
import { TaskCachingService } from '../task-caching.service';
import { TasksService } from '../client/services/TasksService';
import { of } from 'rxjs';

describe('TaskCenterService', () => {
  let service: TaskCenterService;
  let taskCachingServiceSpy: jasmine.SpyObj<TaskCachingService>;

  beforeEach(() => {
    const cachingSpy = jasmine.createSpyObj('TaskCachingService', ['tasks$']);

    TestBed.configureTestingModule({
      providers: [
        TaskCenterService,
        { provide: TaskCachingService, useValue: cachingSpy },
      ]
    });

    service = TestBed.inject(TaskCenterService);
    taskCachingServiceSpy = TestBed.inject(TaskCachingService) as jasmine.SpyObj<TaskCachingService>;
    spyOn(TasksService, 'deleteTaskTasksTaskIdDelete').and.returnValue(of(null) as any);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get tasks from TaskCachingService', (done) => {
    const tasks = [{ id: '1', name: 'test', status: 'running', collectionId: '1' }];
    (Object.getOwnPropertyDescriptor(taskCachingServiceSpy, 'tasks$')?.get as jasmine.Spy).and.returnValue(of(tasks));

    service.tasks$.subscribe(result => {
      expect(result).toEqual(tasks);
      done();
    });
  });

  it('should cancel a task', () => {
    const taskId = '1';
    service.cancelTask(taskId);
    expect(TasksService.deleteTaskTasksTasksTaskIdDelete).toHaveBeenCalledWith(taskId);
  });
});
