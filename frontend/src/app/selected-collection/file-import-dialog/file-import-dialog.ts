import { Component, Inject, OnInit, signal, ElementRef, ViewChild } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { FileImportSettings } from '../../client';


@Component({
  selector: 'app-file-import-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatDialogModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressBarModule,
    MatSelectModule
  ],
  templateUrl: './file-import-dialog.html',
  styleUrl: './file-import-dialog.scss',
})
export class FileImportDialog implements OnInit {
  @ViewChild('fileInput') fileInput!: ElementRef;

  importForm!: FormGroup;
  selectedFileName: string = '';
  selectedFile: File | null = null;
  showProgressBar = signal(false);
  infoString = signal<string>("");

  constructor(
    public dialogRef: MatDialogRef<FileImportDialog>,
    @Inject(MAT_DIALOG_DATA) public data: { collectionName: string, collectionId: string, model: string, settings: FileImportSettings},
    private fb: FormBuilder,
  ) {}

  ngOnInit(): void {
    this.importForm = this.fb.group({
      model: [this.data.model, Validators.required],
      chunkSize: [this.data.settings.chunk_size, [Validators.required, Validators.min(1)]],
      chunkOverlap: [this.data.settings.chunk_overlap, [Validators.required, Validators.min(0)]],
      file: [null, Validators.required]
    });

    
  }

  onNoClick(): void {
    this.dialogRef.close(false);
  }

  onImportClick(): void {
    if (this.importForm.valid) {
      this.dialogRef.close({
        ...this.importForm.getRawValue(),
        collectionId: this.data.collectionId,
        selectedFile: this.selectedFile
      });
    }
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

  // Placeholder for now, will be updated when service logic is in place
  onImportSubmit(): void {
    this.onImportClick();
  }
}

