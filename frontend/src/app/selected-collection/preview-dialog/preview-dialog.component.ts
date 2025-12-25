import { ChangeDetectionStrategy, Component, Inject, OnInit, ChangeDetectorRef, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatListModule } from '@angular/material/list';
import { MatError, MatFormField, MatLabel } from '@angular/material/form-field';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { FilesService, File, FileImportSettings } from '../../client';
import { ImportService } from '../../client';
import { MatInput } from '@angular/material/input';

@Component({
  selector: 'app-preview-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatListModule,
    ReactiveFormsModule,
    MatFormField,
    MatInput,
    MatError,
    MatLabel
  ],
  templateUrl: './preview-dialog.component.html',
  styleUrls: ['./preview-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PreviewDialogComponent implements OnInit {
onImportSubmit() {
throw new Error('Method not implemented.');
}

  importForm!: FormGroup;
  files: File[] = [];
  isLoading = true;
  error: string | null = null;
  chunk = signal<string>("");
  moreChunks = false;
  currentChunkIndex = 0;
  loadedChunks: string[] = [];

  private readonly take = 5;
  private skip = 0;

  constructor(
    public dialogRef: MatDialogRef<PreviewDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { 
        collectionName: string, 
        collectionId: string, 
        model: string, 
        settings: FileImportSettings,
        saved: boolean,
    },
    private formBuilder: FormBuilder,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.importForm = this.formBuilder.group({
      model: [this.data.model, Validators.required],
      chunkSize: [500, [Validators.required, Validators.min(1)]],
      chunkOverlap: [50, [Validators.required, Validators.min(0)]]
    });

    this.importForm.get('model')?.disable();

    FilesService.readFilesFilesCollectionIdGet(this.data.collectionId)
      .then(files => {
        this.files = files;
        this.isLoading = false;
        this.cdr.markForCheck();
      })
      .catch(error => {
        this.error = 'Failed to load files.';
        this.isLoading = false;
        this.cdr.markForCheck();
      });
  }
  onCancel(): void {
    this.dialogRef.close(false);
  }

  onImport(): void {
    // Placeholder for import logic
  }

  selectedFile: File | null = null;

  onFileSelected(file: File): void {
    this.selectedFile = file;
    FilesService.getChunkPreviewFilesContentPost({
      file_id: file.id,
      chunk_size: 500,
      chunk_overlap: 50,
      no_chunks: false,
      take_number: this.take,
      skip_number: this.skip
    }).then(res => {
      console.log("res",res);
      this.currentChunkIndex = 0;
      this.chunk.set(res.chunks[this.currentChunkIndex]);
      this.moreChunks = res.more_chunks;
      this.loadedChunks = res.chunks;
    })
  }

  onNext() {
    if (this.currentChunkIndex < this.take - 1)
    {
        this.currentChunkIndex++;
        this.chunk.set(this.loadedChunks[this.currentChunkIndex]);
    }
  }

  onPrevious() {
    if (this.currentChunkIndex > 0)
    {
        this.currentChunkIndex--;
        this.chunk.set(this.loadedChunks[this.currentChunkIndex]);
    }
  }
}
