import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TaskCenterComponent } from './task-center.component';
import { TaskCenterService } from './task-center.service';
import { of } from 'rxjs';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

describe('TaskCenterComponent', () => {
  let component: TaskCenterComponent;
  let fixture: ComponentFixture<TaskCenterComponent>;
  let taskCenterServiceSpy: jasmine.SpyObj<TaskCenterService>;

  beforeEach(async () => {
    const spy = jasmine.createSpyObj('TaskCenterService', ['tasks$', 'cancelTask']);

    await TestBed.configureTestingModule({
      imports: [ TaskCenterComponent, NoopAnimationsModule ],
      providers: [
        { provide: TaskCenterService, useValue: spy }
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TaskCenterComponent);
    component = fixture.componentInstance;
    taskCenterServiceSpy = TestBed.inject(TaskCenterService) as jasmine.SpyObj<TaskCenterService>;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display tasks', () => {
    const tasks = [{ id: '1', name: 'test', status: 'running' }];
    (Object.getOwnPropertyDescriptor(taskCenterServiceSpy, 'tasks$')?.get as jasmine.Spy).and.returnValue(of(tasks));
    fixture.detectChanges();
    const taskElements = fixture.nativeElement.querySelectorAll('mat-list-item');
    expect(taskElements.length).toBe(1);
    expect(taskElements[0].textContent).toContain('test');
  });

  it('should call cancelTask when cancel button is clicked', () => {
    const tasks = [{ id: '1', name: 'test', status: 'running', collectionId: '1' }];
    (Object.getOwnPropertyDescriptor(taskCenterServiceSpy, 'tasks$')?.get as jasmine.Spy).and.returnValue(of(tasks));
    taskCenterServiceSpy.cancelTask.and.returnValue(of(null));
    fixture.detectChanges();
    const cancelButton = fixture.nativeElement.querySelector('button');
    cancelButton.click();
    expect(taskCenterServiceSpy.cancelTask).toHaveBeenCalledWith('1');
  });
});
