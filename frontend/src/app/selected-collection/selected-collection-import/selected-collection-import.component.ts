import { ChangeDetectionStrategy, Component, OnInit, Input, OnChanges, SimpleChanges, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ImportService } from '../../client/services/ImportService';
import { Import } from '../../client/models/Import';
import { ImportFormStateService } from '../../import-form-state.service';


import { UntilDestroy, untilDestroyed } from '@ngneat/until-destroy';
import { Body_import_file_import__collection_id__post } from '../../client/models/Body_import_file_import__collection_id__post';
import { ExtendedCollection } from '../selected-collection.component';

@Component({
  selector: 'app-selected-collection-import',
  standalone: true,
  imports: [
    CommonModule,
    MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    MatButtonModule,
    ReactiveFormsModule
  ],
  templateUrl: './selected-collection-import.component.html',
  styleUrl: './selected-collection-import.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})

@UntilDestroy()
export class SelectedCollectionImportComponent implements OnInit, OnChanges {
  @Input() collection: ExtendedCollection | undefined;
  @ViewChild('fileInput') fileInput!: ElementRef;

  importForm!: FormGroup;
  importTypes: Import[] = [];
  selectedFileName: string = '';
  selectedFile: File | null = null;


  constructor(
    private fb: FormBuilder,
    private importFormStateService: ImportFormStateService,
  ) {}

  ngOnInit(): void {
    this.importForm = this.fb.group({
      importType: ['', Validators.required],
      model: ['', Validators.required],
      chunkSize: [null, [Validators.required, Validators.min(1)]],
      chunkOverlap: [null, [Validators.required, Validators.min(0)]],
      file: [null, Validators.required]
    });

    this.getImportTypes();

    this.importForm.get('importType')?.valueChanges
      .pipe(untilDestroyed(this))
      .subscribe(() => {
        this.onFormChange();
      });

    this.importForm.valueChanges
      .pipe(untilDestroyed(this))
      .subscribe((a) => {
        console.log('for changed. saving state');
        this.importFormStateService.setState(this.collection!.id, this.importForm.getRawValue());
      });

  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['collection'] && this.collection) {
      const collectionId = this.collection.id;
      const state = this.importFormStateService.getState(collectionId);
      console.log('**on changes', state, this.collection);
      
     

      //Enable/Disable controls
      if (this.collectionIsSet()){
        this.importForm.get('importType')?.disable({ emitEvent: false });
        this.importForm.get('model')?.disable({ emitEvent: false });
      }
      else{
        this.importForm.get('importType')?.enable({ emitEvent: false });
        this.importForm.get('model')?.enable({ emitEvent: false });
      }

      //Set or create state
      if (state) {
        console.log('patch state:',collectionId, state);
        this.importForm.patchValue(state, { emitEvent: false });
      }
      else if (this.collectionIsSet()) {
        const importType = this.importTypes.find(i => i.name === this.collection!.import_type);
        const initialState = {
          importType: importType,
          model: this.collection!.model,
          chunkSize: this.collection!.chunk_size,
          chunkOverlap: this.collection!.chunk_overlap,
          file: null
        };

        this.importForm.patchValue(initialState, { emitEvent: false });
        this.importFormStateService.setState(collectionId, this.importForm.getRawValue());

      }
      else {
        this.importForm.reset({
          importType: '',
          model: '',
          chunkSize: null,
          chunkOverlap: null,
          file: null,
        }, { emitEvent: false });
        this.importFormStateService.clearState(collectionId);
      }

       //Clean selected file
      this.selectedFile = null;
      this.selectedFileName = '';
      this.fileInput.nativeElement.value = '';
      this.importForm.get('file')?.setValue('', {emitEvent: false});
      //this.importForm.get('file')?.updateValueAndValidity();

    }
  }

  onFormChange(): void {
    if (!this.collectionIsSet())
    {
     const importType = this.importForm.get('importType')?.value;
     if (importType) {
       this.importForm.get('model')?.setValue(importType.embedding_model);
       this.importForm.get('chunkSize')?.setValue(importType.chunk_size);
       this.importForm.get('chunkOverlap')?.setValue(importType.chunk_overlap);
     }
    }
  }

  getImportTypes(): void {
    ImportService.getImportsImportGet().then(
      (data: Import[]) => {
        this.importTypes = data;
        // After getting import types, re-evaluate the form state
        if (this.collection) {
          this.ngOnChanges({
            collection: {
              currentValue: this.collection,
              previousValue: undefined,
              firstChange: true,
              isFirstChange: () => true
            }
          });
        }
      },
      (error: any) => {
        console.error('Error fetching import types:', error);
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

  onSubmit(): void {
    if (this.importForm.valid && this.collection?.name && this.selectedFile) {
      const formValue = this.importForm.getRawValue();
      const formData: Body_import_file_import__collection_id__post = {
        file: this.selectedFile,
        import_params: JSON.stringify({
             name: formValue.importType.name,
             embedding_model: formValue.model,
             chunk_size: formValue.chunkSize,
             chunk_overlap: formValue.chunkOverlap
        })
      };

      ImportService.importFileImportCollectionIdPost(
        this.collection.id,
        formData
      ).then(
        (response: any) => {
          console.log('File imported successfully:', response);
        },
        (error: any) => {
          console.error('Error importing file:', error);
        }
      );
    } else {
      console.error('Form is invalid or collection name/file is missing.');
    }
  }

  compareImportTypes(o1: Import, o2: Import): boolean {
    return o1 && o2 ? o1.name === o2.name : o1 === o2;
  }

  trackByImportType(index: number, item: Import): string {
    return item.name;
  }

  protected canOpenfile():boolean {
    return this.importForm.get('importType')?.value.name !== 'FILE';
  }

  private collectionIsSet(): boolean {
    return (this.collection?.saved) ?? false;
  }
}
