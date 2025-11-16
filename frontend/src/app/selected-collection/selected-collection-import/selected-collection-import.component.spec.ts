import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { SelectedCollectionImportComponent } from './selected-collection-import.component';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ImportService } from '../../client/services/ImportService';
import { of, throwError } from 'rxjs';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { Collection } from '../../client/models/Collection';
import { Import } from '../../client/models/Import';
import { ImportType } from '../../client/models/ImportType';
import { ExtendedCollection } from '../../selected-collection/selected-collection.component';
import { CancelablePromise } from '../../client/core/CancelablePromise';

function createCancelablePromise<T>(value: T): CancelablePromise<T> {
  return new CancelablePromise((resolve) => resolve(value));
}

describe('SelectedCollectionImportComponent', () => {
  let component: SelectedCollectionImportComponent;
  let fixture: ComponentFixture<SelectedCollectionImportComponent>;

  const mockImportTypes: Import[] = [
    { name: 'PDF', embedding_model: 'model1', chunk_size: 100, chunk_overlap: 10 },
    { name: 'TXT', embedding_model: 'model2', chunk_size: 200, chunk_overlap: 20 },
  ];

  const mockCollection: ExtendedCollection = {
    name: 'test-collection',
    id: '123',
    description: 'A test collection',
    import_type: ImportType.NONE,
    saved: false,
  };

  beforeEach(async () => {
    spyOn(ImportService, 'getImportsImportGet').and.returnValue(createCancelablePromise(mockImportTypes));
    spyOn(ImportService, 'importFileImportCollectionIdPost').and.returnValue(createCancelablePromise({ message: 'Import successful' }));

    await TestBed.configureTestingModule({
      imports: [
        SelectedCollectionImportComponent,
        ReactiveFormsModule,
        MatFormFieldModule,
        MatSelectModule,
        MatInputModule,
        MatButtonModule,
        BrowserAnimationsModule // Required for MatSelect to work in tests
      ],
      providers: [
        FormBuilder,
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SelectedCollectionImportComponent);
    component = fixture.componentInstance;
    component.collection = { ...mockCollection }; // Assign a copy to avoid direct modification
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize the form with default values and validators', () => {
    expect(component.importForm).toBeDefined();
    expect(component.importForm.get('importType')).toBeDefined();
    expect(component.importForm.get('model')).toBeDefined();
    expect(component.importForm.get('chunkSize')).toBeDefined();
    expect(component.importForm.get('chunkOverlap')).toBeDefined();
    expect(component.importForm.get('file')).toBeDefined();

    expect(component.importForm.get('importType')?.value).toBe('');
    expect(component.importForm.get('model')?.value).toBe('');
    expect(component.importForm.get('chunkSize')?.value).toBeNull();
    expect(component.importForm.get('chunkOverlap')?.value).toBeNull();
    expect(component.importForm.get('file')?.value).toBeNull();

    expect(component.importForm.get('importType')?.valid).toBeFalse();
    expect(component.importForm.get('model')?.valid).toBeFalse();
    expect(component.importForm.get('chunkSize')?.valid).toBeFalse();
    expect(component.importForm.get('chunkOverlap')?.valid).toBeFalse();
    expect(component.importForm.get('file')?.valid).toBeFalse();
  });

  it('should load import types on initialization', fakeAsync(() => {
    expect(ImportService.getImportsImportGet).toHaveBeenCalled();
    tick(); // Resolve the promise
    expect(component.importTypes).toEqual(mockImportTypes);
  }));

  it('should disable the Import button initially', () => {
    const importButton = fixture.nativeElement.querySelector('button[type="submit"]');
    expect(importButton.disabled).toBeTrue();
  });

  it('should enable the Import button when the form is valid', fakeAsync(() => {
    component.importForm.get('importType')?.setValue('PDF');
    component.importForm.get('model')?.setValue('test-model');
    component.importForm.get('chunkSize')?.setValue(100);
    component.importForm.get('chunkOverlap')?.setValue(10);

    const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    component.selectedFile = mockFile;
    component.importForm.get('file')?.setValue(mockFile);

    fixture.detectChanges();
    tick();

    const importButton = fixture.nativeElement.querySelector('button[type="submit"]');
    expect(importButton.disabled).toBeFalse();
  }));

  it('should update selectedFileName and file form control on file selection', () => {
    const mockFile = new File(['content'], 'test.txt', { type: 'text/plain' });
    const event = { target: { files: [mockFile] } } as unknown as Event;
    component.onFileSelected(event);

    expect(component.selectedFileName).toBe('test.txt');
    expect(component.selectedFile).toBe(mockFile);
    expect(component.importForm.get('file')?.value).toBe(mockFile);
    expect(component.importForm.get('file')?.valid).toBeTrue();
  });

  it('should call importFileImportCollectionIdPost on form submission with valid data', fakeAsync(() => {
    component.importForm.get('importType')?.setValue('PDF');
    component.importForm.get('model')?.setValue('test-model');
    component.importForm.get('chunkSize')?.setValue(100);
    component.importForm.get('chunkOverlap')?.setValue(10);

    const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    component.selectedFile = mockFile;
    component.importForm.get('file')?.setValue(mockFile);

    fixture.detectChanges();
    tick();

    component.onSubmit();

    expect(ImportService.importFileImportCollectionIdPost).toHaveBeenCalledWith(
      mockCollection.id,
      jasmine.any(Object)
    );
  }));

  it('should disable importType and model fields if collection.import_type is not NONE', fakeAsync(() => {
    component.collection = { ...mockCollection, import_type: ImportType.FILE };
    component.ngOnInit(); // Re-initialize component with new input
    fixture.detectChanges();
    tick();

    expect(component.importForm.get('importType')?.disabled).toBeTrue();
    expect(component.importForm.get('model')?.disabled).toBeTrue();
  }));

  it('should not disable importType and model fields if collection.import_type is NONE', fakeAsync(() => {
    component.collection = { ...mockCollection, import_type: ImportType.NONE };
    component.ngOnInit(); // Re-initialize component with new input
    fixture.detectChanges();
    tick();

    expect(component.importForm.get('importType')?.enabled).toBeTrue();
    expect(component.importForm.get('model')?.enabled).toBeTrue();
  }));

  it('should show error for required importType when touched', fakeAsync(() => {
    const importTypeControl = component.importForm.get('importType');
    importTypeControl?.markAsTouched();
    fixture.detectChanges();
    tick();
    const errorElement = fixture.nativeElement.querySelector('mat-error');
    expect(errorElement).toBeTruthy();
    expect(errorElement.textContent).toContain('Import type is required.');
  }));

  it('should show error for required file when touched', fakeAsync(() => {
    const fileControl = component.importForm.get('file');
    fileControl?.markAsTouched();
    fixture.detectChanges();
    tick();
    const errorElement = fixture.nativeElement.querySelectorAll('mat-error')[1]; // Assuming it's the second error
    expect(errorElement).toBeTruthy();
    expect(errorElement.textContent).toContain('File is required.');
  }));

  it('should show error for required model when touched', fakeAsync(() => {
    const modelControl = component.importForm.get('model');
    modelControl?.markAsTouched();
    fixture.detectChanges();
    tick();
    const errorElement = fixture.nativeElement.querySelectorAll('mat-error')[2]; // Assuming it's the third error
    expect(errorElement).toBeTruthy();
    expect(errorElement.textContent).toContain('Model is required.');
  }));

  it('should show error for required chunkSize when touched', fakeAsync(() => {
    const chunkSizeControl = component.importForm.get('chunkSize');
    chunkSizeControl?.markAsTouched();
    fixture.detectChanges();
    tick();
    const errorElement = fixture.nativeElement.querySelectorAll('mat-error')[3]; // Assuming it's the fourth error
    expect(errorElement).toBeTruthy();
    expect(errorElement.textContent).toContain('Chunk size is required.');
  }));

  it('should show error for min chunkSize when invalid', fakeAsync(() => {
    component.importForm.get('chunkSize')?.setValue(0);
    const chunkSizeControl = component.importForm.get('chunkSize');
    chunkSizeControl?.markAsTouched();
    fixture.detectChanges();
    tick();
    const errorElement = fixture.nativeElement.querySelectorAll('mat-error')[4]; // Assuming it's the fifth error
    expect(errorElement).toBeTruthy();
    expect(errorElement.textContent).toContain('Chunk size must be at least 1.');
  }));

  it('should show error for required chunkOverlap when touched', fakeAsync(() => {
    const chunkOverlapControl = component.importForm.get('chunkOverlap');
    chunkOverlapControl?.markAsTouched();
    fixture.detectChanges();
    tick();
    const errorElement = fixture.nativeElement.querySelectorAll('mat-error')[5]; // Assuming it's the sixth error
    expect(errorElement).toBeTruthy();
    expect(errorElement.textContent).toContain('Chunk overlap is required.');
  }));

  it('should show error for min chunkOverlap when invalid', fakeAsync(() => {
    component.importForm.get('chunkOverlap')?.setValue(-1);
    const chunkOverlapControl = component.importForm.get('chunkOverlap');
    chunkOverlapControl?.markAsTouched();
    fixture.detectChanges();
    tick();
    const errorElement = fixture.nativeElement.querySelectorAll('mat-error')[6]; // Assuming it's the seventh error
    expect(errorElement).toBeTruthy();
    expect(errorElement.textContent).toContain('Chunk overlap must be at least 0.');
  }));
});

