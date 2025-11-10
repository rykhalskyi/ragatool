import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';
import { CollectionsListComponent } from './collections-list.component';
import { CollectionRefreshService } from '../collection-refresh.service';
import { CollectionsService } from '../client/services/CollectionsService';

describe('CollectionsListComponent', () => {
  let component: CollectionsListComponent;
  let fixture: ComponentFixture<CollectionsListComponent>;
  let collectionRefreshService: CollectionRefreshService;

  beforeEach(async () => {
    const collectionRefreshServiceMock = {
      refreshNeeded$: of(null), // Mock the observable
      triggerRefresh: jasmine.createSpy('triggerRefresh')
    };

    spyOn(CollectionsService, 'readCollectionsCollectionsGet').and.returnValue(Promise.resolve([]));

    await TestBed.configureTestingModule({
      imports: [CollectionsListComponent, RouterTestingModule],
      providers: [
        { provide: CollectionRefreshService, useValue: collectionRefreshServiceMock }
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CollectionsListComponent);
    component = fixture.componentInstance;
    collectionRefreshService = TestBed.inject(CollectionRefreshService);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should fetch collections on init', () => {
    expect(CollectionsService.readCollectionsCollectionsGet).toHaveBeenCalled();
  });

  it('should fetch collections when refresh is triggered', () => {
    (CollectionsService.readCollectionsCollectionsGet as jasmine.Spy).calls.reset();
    // Simulate a refresh
    (collectionRefreshService.refreshNeeded$ as any).next();
    expect(CollectionsService.readCollectionsCollectionsGet).toHaveBeenCalled();
  });
});
