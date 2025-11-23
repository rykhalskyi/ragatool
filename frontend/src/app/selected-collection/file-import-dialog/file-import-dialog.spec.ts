import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { FileImportDialog } from './file-import-dialog';

describe('FileImportDialog', () => {
  let component: FileImportDialog;
  let fixture: ComponentFixture<FileImportDialog>;
  let mockMatDialogRef: jasmine.SpyObj<MatDialogRef<FileImportDialog>>;
  let mockMAT_DIALOG_DATA: { collectionName: string, collectionId: string };

  beforeEach(async () => {
    mockMatDialogRef = jasmine.createSpyObj('MatDialogRef', ['close']);
    mockMAT_DIALOG_DATA = { collectionName: 'test-collection', collectionId: 'test-id' };

    await TestBed.configureTestingModule({
      imports: [FileImportDialog, ReactiveFormsModule, NoopAnimationsModule],
      providers: [
        FormBuilder,
        { provide: MatDialogRef, useValue: mockMatDialogRef },
        { provide: MAT_DIALOG_DATA, useValue: mockMAT_DIALOG_DATA }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(FileImportDialog);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize the importForm with correct controls and validators', () => {
    expect(component.importForm).toBeDefined();
    expect(component.importForm.get('model')).toBeDefined();
    expect(component.importForm.get('chunkSize')).toBeDefined();
    expect(component.importForm.get('chunkOverlap')).toBeDefined();
    expect(component.importForm.get('file')).toBeDefined();

    // Check validators
    expect(component.importForm.get('model')?.hasError('required')).toBeTrue();
    expect(component.importForm.get('chunkSize')?.hasError('required')).toBeTrue();
    expect(component.importForm.get('chunkSize')?.hasError('min')).toBeTrue(); // Initial value is null, so min(1) should fail
    expect(component.importForm.get('chunkOverlap')?.hasError('required')).toBeTrue();
    expect(component.importForm.get('chunkOverlap')?.hasError('min')).toBeTrue(); // Initial value is null, so min(0) should fail
    expect(component.importForm.get('file')?.hasError('required')).toBeTrue();
  });

  it('should update selectedFile and selectedFileName on file selection', () => {
    const mockFile = new File([''], 'test.txt', { type: 'text/plain' });
    const mockEvt = { target: { files: [mockFile] } } as unknown as Event;

    component.onFileSelected(mockEvt);

    expect(component.selectedFile).toEqual(mockFile);
    expect(component.selectedFileName).toEqual('test.txt');
    expect(component.importForm.get('file')?.value).toEqual(mockFile);
  });

  it('should call dialogRef.close(false) when onNoClick is called', () => {
    component.onNoClick();
    expect(mockMatDialogRef.close).toHaveBeenCalledWith(false);
  });

  it('should call dialogRef.close with form data when onImportClick is called and form is valid', () => {
    const mockFile = new File([''], 'test.txt', { type: 'text/plain' });
    component.importForm.patchValue({
      model: 'test-model',
      chunkSize: 100,
      chunkOverlap: 10,
      file: mockFile
    });

    component.selectedFile = mockFile; // Manually set selectedFile as onFileSelected is not called in this test

    component.onImportClick();

    expect(mockMatDialogRef.close).toHaveBeenCalledWith({
      model: 'test-model',
      chunkSize: 100,
      chunkOverlap: 10,
      file: mockFile,
      collectionId: 'test-id',
      selectedFile: mockFile
    });
  });

  it('should not call dialogRef.close when onImportClick is called and form is invalid', () => {
    // Form is invalid by default due to required fields
    component.onImportClick();
    expect(mockMatDialogRef.close).not.toHaveBeenCalled();
  });
});
