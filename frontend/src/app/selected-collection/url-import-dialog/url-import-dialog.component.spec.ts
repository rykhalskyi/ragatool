import { ComponentFixture, TestBed } from '@angular/core/testing';
import { UrlImportDialog } from './url-import-dialog';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

describe('UrlImportDialog', () => {
  let mockMatDialogRef: jasmine.SpyObj<MatDialogRef<UrlImportDialog>>;

  const baseData = {
    collectionName: 'Test Collection',
    collectionId: '123',
    model: 'test-model',
    settings: {
      chunk_size: 100,
      chunk_overlap: 20,
      no_chunks: false,
    },
    saved: false,
    twoStepImport: false,
    recentFilters: ['^https://docs\\.example\\.com'],
  };

  function createComponent(data: any = baseData) {
    mockMatDialogRef = jasmine.createSpyObj('MatDialogRef', ['close']);

    TestBed.configureTestingModule({
      imports: [
        UrlImportDialog,
        ReactiveFormsModule,
        MatCheckboxModule,
        MatFormFieldModule,
        MatInputModule,
        MatAutocompleteModule,
        NoopAnimationsModule,
      ],
      providers: [
        FormBuilder,
        { provide: MatDialogRef, useValue: mockMatDialogRef },
        { provide: MAT_DIALOG_DATA, useValue: data },
      ],
    });

    const fixture: ComponentFixture<UrlImportDialog> = TestBed.createComponent(UrlImportDialog);
    fixture.detectChanges();
    return { fixture, component: fixture.componentInstance };
  }

  it('should create', () => {
    const { component } = createComponent();
    expect(component).toBeTruthy();
  });

  it('should initialize form with defaults when there is no saved filter', () => {
    const { component } = createComponent();

    expect(component.importForm.get('model')?.value).toBe(baseData.model);
    expect(component.importForm.get('chunkSize')?.value).toBe(baseData.settings.chunk_size);
    expect(component.importForm.get('chunkOverlap')?.value).toBe(baseData.settings.chunk_overlap);
    expect(component.importForm.get('url')?.value).toBe('');
    expect(component.importForm.get('no_chunks')?.value).toBe(false);
    expect(component.filterEnabled.value).toBe(false);
    expect(component.urlFilterRegex.value).toBe('');
    expect(component.urlFilterRegex.disabled).toBe(true);
  });

  it('should prefill and enable the filter from saved collection settings', () => {
    const { component } = createComponent({
      ...baseData,
      settings: { ...baseData.settings, filter: '^https://docs\\.example\\.com' },
    });

    expect(component.filterEnabled.value).toBe(true);
    expect(component.urlFilterRegex.value).toBe('^https://docs\\.example\\.com');
    expect(component.urlFilterRegex.enabled).toBe(true);
    expect(component.urlFilterRegex.hasError('required')).toBe(false);
  });

  it('should enable urlFilterRegex when filterEnabled is checked', () => {
    const { fixture, component } = createComponent();
    component.filterEnabled.setValue(true);
    fixture.detectChanges();

    expect(component.urlFilterRegex.enabled).toBe(true);
    expect(component.urlFilterRegex.hasValidator(component.regexValidator)).toBe(true);
  });

  it('should disable and clear urlFilterRegex when filterEnabled is unchecked', () => {
    const { fixture, component } = createComponent();
    component.filterEnabled.setValue(true);
    fixture.detectChanges();
    component.urlFilterRegex.setValue('^test');

    component.filterEnabled.setValue(false);
    fixture.detectChanges();

    expect(component.urlFilterRegex.disabled).toBe(true);
    expect(component.urlFilterRegex.value).toBe('');
    expect(component.urlFilterRegex.hasValidator(component.regexValidator)).toBe(false);
  });

  it('should validate regex patterns', () => {
    const { fixture, component } = createComponent();
    component.filterEnabled.setValue(true);
    fixture.detectChanges();

    component.urlFilterRegex.setValue('^test.*$');
    expect(component.urlFilterRegex.hasError('invalidRegex')).toBe(false);

    component.urlFilterRegex.setValue('[abc');
    expect(component.urlFilterRegex.hasError('invalidRegex')).toBe(true);
  });

  it('should require urlFilterRegex when filterEnabled is true', () => {
    const { fixture, component } = createComponent();
    component.filterEnabled.setValue(true);
    fixture.detectChanges();

    component.urlFilterRegex.setValue('');
    expect(component.urlFilterRegex.hasError('required')).toBe(true);
  });

  it('should close with the raw form value when the filter is disabled', () => {
    const { component } = createComponent();

    component.importForm.patchValue({
      url: 'http://example.com',
      chunkSize: 200,
      chunkOverlap: 50,
      no_chunks: true,
      filterEnabled: false,
    });

    component.onImportClick();

    expect(mockMatDialogRef.close).toHaveBeenCalledWith(jasmine.objectContaining({
      url: 'http://example.com',
      chunkSize: 200,
      chunkOverlap: 50,
      no_chunks: true,
      filterEnabled: false,
      urlFilterRegex: '',
      collectionId: baseData.collectionId,
    }));
  });

  it('should close with the filter when it is enabled', () => {
    const testRegex = '.*\\.pdf$';
    const { component } = createComponent();

    component.importForm.patchValue({
      url: 'http://example.com/data.pdf',
      chunkSize: 200,
      chunkOverlap: 50,
      no_chunks: false,
      filterEnabled: true,
      urlFilterRegex: testRegex,
    });

    component.onImportClick();

    expect(mockMatDialogRef.close).toHaveBeenCalledWith(jasmine.objectContaining({
      url: 'http://example.com/data.pdf',
      filterEnabled: true,
      urlFilterRegex: testRegex,
      collectionId: baseData.collectionId,
    }));
  });
});
