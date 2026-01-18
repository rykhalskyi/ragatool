import { ComponentFixture, TestBed } from '@angular/core/testing';
import { InspectDialogComponent } from './inspect-dialog.component';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { CollectionsService } from '../../client';
import { of } from 'rxjs';
import { ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatListModule } from '@angular/material/list';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatTabsModule } from '@angular/material/tabs';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

describe('InspectDialogComponent', () => {
  let component: InspectDialogComponent;
  let fixture: ComponentFixture<InspectDialogComponent>;
  let mockMatDialogRef: jasmine.SpyObj<MatDialogRef<InspectDialogComponent>>;
  let mockCollectionsService: jasmine.SpyObj<CollectionsService>;

  const MOCK_COLLECTION_ID = 'test-collection-id';
  const MOCK_CHUNKS = ['chunk 1', 'chunk 2', 'chunk 3'];

  beforeEach(async () => {
    mockMatDialogRef = jasmine.createSpyObj('MatDialogRef', ['close']);
    mockCollectionsService = jasmine.createSpyObj('CollectionsService', ['getCollectionContentCollectionsCollectionIdContentGet', 'queryCollectionCollectionsCollectionIdQueryGet']);

    await TestBed.configureTestingModule({
      imports: [
        InspectDialogComponent, // standalone component
        CommonModule,
        ReactiveFormsModule,
        MatButtonModule,
        MatListModule,
        MatFormFieldModule,
        MatInputModule,
        MatTabsModule,
        BrowserAnimationsModule, // Required for MatTabsModule
      ],
      providers: [
        { provide: MatDialogRef, useValue: mockMatDialogRef },
        { provide: MAT_DIALOG_DATA, useValue: { collectionId: MOCK_COLLECTION_ID } },
        { provide: CollectionsService, useValue: mockCollectionsService }
      ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    mockCollectionsService.getCollectionContentCollectionsCollectionIdContentGet.and.returnValue(Promise.resolve({
      chunks: MOCK_CHUNKS,
      more_chunks: false
    }));
    fixture = TestBed.createComponent(InspectDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should close the dialog on cancel', () => {
    component.onCancel();
    expect(mockMatDialogRef.close).toHaveBeenCalled();
  });

  it('should load initial chunks on ngOnInit', async () => {
    await fixture.whenStable();
    expect(component.loadedChunks).toEqual(MOCK_CHUNKS);
    expect(component.chunk()).toBe(MOCK_CHUNKS[0]);
    expect(component.isLoading).toBeFalse();
    expect(component.error).toBeNull();
  });

  it('should navigate to the next chunk', async () => {
    await fixture.whenStable();
    component.onNext();
    expect(component.currentChunkIndex).toBe(1);
    expect(component.chunk()).toBe(MOCK_CHUNKS[1]);
  });

  it('should navigate to the previous chunk', async () => {
    await fixture.whenStable();
    component.currentChunkIndex = 1;
    component.chunk.set(MOCK_CHUNKS[1]);
    component.onPrevious();
    expect(component.currentChunkIndex).toBe(0);
    expect(component.chunk()).toBe(MOCK_CHUNKS[0]);
  });

  it('should load more chunks when navigating next and more_chunks is true', async () => {
    mockCollectionsService.getCollectionContentCollectionsCollectionIdContentGet.and.returnValues(
      Promise.resolve({ chunks: ['initial chunk'], more_chunks: true }),
      Promise.resolve({ chunks: ['next chunk'], more_chunks: false })
    );
    fixture = TestBed.createComponent(InspectDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    await fixture.whenStable();
    expect(component.loadedChunks).toEqual(['initial chunk']);
    component.onNext();
    await fixture.whenStable();
    expect(component.loadedChunks).toEqual(['next chunk']);
    expect(component.currentChunkIndex).toBe(0);
    expect(component.chunk()).toBe('next chunk');
  });

  it('should handle query submission and display bot response', async () => {
    const userQuery = 'test query';
    const botResponse = ['response 1', 'response 2'];
    mockCollectionsService.queryCollectionCollectionsCollectionIdQueryGet.and.returnValue(Promise.resolve({ results: botResponse }));

    component.queryForm.get('query')?.setValue(userQuery);
    component.onQuerySubmit();

    expect(component.messages()).toEqual([{ sender: 'user', text: userQuery }]);
    await fixture.whenStable();
    expect(component.messages()).toEqual([
      { sender: 'user', text: userQuery },
      { sender: 'bot', text: botResponse.join('\n') }
    ]);
    expect(component.queryForm.get('query')?.value).toBeNull(); // Form should be reset
  });

  it('should handle query submission error', async () => {
    const userQuery = 'test query';
    mockCollectionsService.queryCollectionCollectionsCollectionIdQueryGet.and.returnValue(Promise.reject('API Error'));

    component.queryForm.get('query')?.setValue(userQuery);
    component.onQuerySubmit();

    expect(component.messages()).toEqual([{ sender: 'user', text: userQuery }]);
    await fixture.whenStable();
    expect(component.messages()).toEqual([
      { sender: 'user', text: userQuery },
      { sender: 'bot', text: 'Error: Failed to get response from the collection.' }
    ]);
  });
});
