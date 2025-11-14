import { ChangeDetectionStrategy, Component, OnInit, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms'; // Import ReactiveFormsModule
import { ImportService } from '../../client/services/ImportService';
import { Import } from '../../client/models/Import';
import { Collection } from '../../client/models/Collection';

import { UntilDestroy, untilDestroyed } from '@ngneat/until-destroy';
import { Body_import_file_import__collection_id__post } from '../../client/models/Body_import_file_import__collection_id__post';

@Component({
  selector: 'app-selected-collection-import',
  standalone: true,
  imports: [
    CommonModule,
    MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    MatButtonModule,
    ReactiveFormsModule // Use ReactiveFormsModule for form group
  ],
  templateUrl: './selected-collection-import.component.html',
  styleUrl: './selected-collection-import.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})

@UntilDestroy()
export class SelectedCollectionImportComponent implements OnInit, OnChanges {
  @Input() collection: Collection | undefined;

  importForm!: FormGroup;
  importTypes: Import[] = [];
  selectedFileName: string = '';
  selectedFile: File | null = null;

  constructor(
    private fb: FormBuilder,
  ) {}

  ngOnInit(): void {
    this.importForm = this.fb.group({
      importType: ['', Validators.required],
      model: ['', Validators.required],
      chunkSize: [null, [Validators.required, Validators.min(1)]],
      chunkOverlap: [null, [Validators.required, Validators.min(0)]],
      file: [null, Validators.required] // Add file control
    });

    this.getImportTypes();
    this.updateFormState();

    this.importForm.get('importType')?.valueChanges
      .pipe(untilDestroyed(this))
      .subscribe(() => {
      this.onFormChange();
    });

    this.setControls();
  }

  ngOnChanges(changes: SimpleChanges): void {
    this.setControls();

  }

  onFormChange(): void {
    if (!this.collectionIsSet())
    {
     const importType = this.importForm.get('importType')?.value;
     this.importForm.get('model')?.setValue(importType.embedding_model);
     this.importForm.get('chunkSize')?.setValue(importType.chunk_size);
     this.importForm.get('chunkOverlap')?.setValue(importType.chunk_overlap);
    }
  }

  getImportTypes(): void {
    ImportService.getImportsImportGet().then(
      (data: Import[]) => {
        console.log('got data:', data);
        this.importTypes = data;
      },
      (error: any) => {
        console.error('Error fetching import types:', error);
        // Handle error appropriately
      }
    );
  }

  onFileSelected(event: Event) {
    const element = event.currentTarget as HTMLInputElement;
    let fileList: FileList | null = element.files;
    if (fileList && fileList.length > 0) {
      this.selectedFile = fileList[0];
      this.selectedFileName = fileList[0].name;
      this.importForm.patchValue({ file: this.selectedFile });
      this.importForm.get('file')?.updateValueAndValidity();
    } else {
      this.selectedFile = null;
      this.selectedFileName = '';
      this.importForm.patchValue({ file: null });
      this.importForm.get('file')?.updateValueAndValidity();
    }
  }

  updateFormState(): void {
    // Logic to disable "Import" button
    // This is handled by [disabled]="importForm.invalid" in the template
  }

  onSubmit(): void {
    if (this.importForm.valid && this.collection?.name && this.selectedFile) {
      const formData: Body_import_file_import__collection_id__post = {
        file: this.selectedFile,
        import_params: JSON.stringify({
             name: this.importForm.get('importType')?.value.name,
             embedding_model: this.importForm.get('model')?.value,
             chunk_size: this.importForm.get('chunkSize')?.value,
             chunk_overlap: this.importForm.get('chunkOverlap')?.value
        })
      };

      console.log('save request:',this.collection.name, this.collection.id, formData);
      ImportService.importFileImportCollectionIdPost(
        this.collection.id, 
        formData
      ).then(
        (response: any) => {
          console.log('File imported successfully:', response);
          // TODO: Show success message to user
          // TODO: Refresh collection data or navigate
        },
        (error: any) => {
          console.error('Error importing file:', error);
          // TODO: Show error message to user
        }
      );
    } else {
      console.error('Form is invalid or collection name/file is missing.');
      // TODO: Show validation errors to user
    }
  }

  private setControls(): void{
    console.log('Set Controls', this.collection);
      if (this.collectionIsSet()) {
        
        const importType = this.importTypes.find(i=> i.name === this.collection!.import_type);

        this.importForm.get('importType')?.setValue(importType);
        this.importForm.get('chunkSize')?.setValue(this.collection!.chunk_size);
        this.importForm.get('chunkOverlap')?.setValue(this.collection!.chunk_overlap);
        this.importForm.get('model')?.setValue(this.collection!.model);  

        this.importForm.get('importType')?.disable();
        this.importForm.get('model')?.disable();
    }
    else{
        this.importForm.get('importType')?.enable();
        this.importForm.get('model')?.enable();
    }
  }

  private collectionIsSet(): boolean{
    return (this.collection?.import_type && this.collection.import_type !== 'NONE') ?? false;
  }
}
