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
import { MatSelectChange, MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatTooltipModule } from '@angular/material/tooltip';

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
    MatLabel,
    MatSelectModule,
    MatCheckboxModule,
    MatTooltipModule
  ],
  templateUrl: './preview-dialog.component.html',
  styleUrls: ['./preview-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PreviewDialogComponent implements OnInit {

  chunkForm!: FormGroup;
  files: File[] = [];
  selectedFiles = new Set<string>();
  isLoading = true;
  error: string | null = null;
  chunk = signal<string>("");
  moreChunks = false;
  currentChunkIndex = 0;
  loadedChunks: string[] = [];
  chunkTypes: string[] = [];

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
    this.chunkForm = this.formBuilder.group({
      model: [this.data.model, Validators.required],
      chunkSize: [500, [Validators.required, Validators.min(1)]],
      chunkOverlap: [50, [Validators.required, Validators.min(0)]],
      chunkType: ['default', Validators.required],
      noChunks: [false]
    });

    this.chunkForm.get('model')?.disable();

    FilesService.readFilesFilesCollectionIdGet(this.data.collectionId)
      .then(files => {
        this.files = files;
        // Initialize all files as selected by default
        this.selectedFiles = new Set(files.map(f => f.id));
        this.isLoading = false;
        this.cdr.markForCheck();
      })
      .catch(error => {
        this.error = 'Failed to load files.';
        this.isLoading = false;
        this.cdr.markForCheck();
      });

    ImportService.getChunkTypesImportChunktypesGet()
      .then(chunkTypes => {
        this.chunkTypes = chunkTypes;
        this.chunkForm.get('chunkType')?.setValue(this.chunkTypes[0]);
        this.cdr.markForCheck();
      })
      .catch(error => {
        console.error('Failed to load chunk types:', error);
      });
  }
  onCancel(): void {
    this.dialogRef.close(false);
  }

  onImport(): void {
    this.dialogRef.close({
        ...this.chunkForm.getRawValue(),
        collectionId: this.data.collectionId,
        selectedFile: this.selectedFile,
        selectedFiles: Array.from(this.selectedFiles)
    });
  }

  selectedFile: File | null = null;

  onFileSelected(file: File): void {
    this.selectedFile = file;
    FilesService.getChunkPreviewFilesContentPost({
      file_id: file.id,
      chunk_type: this.chunkForm.get('chunkType')?.value ?? "default",
      chunk_size: this.chunkForm.get('chunkSize')?.value ?? 500,
      chunk_overlap: this.chunkForm.get('chunkOverlap')?.value ?? 50,
      no_chunks: this.chunkForm.get('noChunks')?.value ?? false,
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

  updateChunks() {
    
 FilesService.getChunkPreviewFilesContentPost({
      file_id: this.selectedFile!.id,
      chunk_type: this.chunkForm.get('chunkType')?.value ?? "default",
      chunk_size: this.chunkForm.get('chunkSize')?.value ?? 500,
      chunk_overlap: this.chunkForm.get('chunkOverlap')?.value ?? 50,
      no_chunks: this.chunkForm.get('noChunks')?.value ?? false,
      take_number: this.take,
      skip_number: this.skip
    }).then(res => {
      
      this.chunk.set(res.chunks[this.currentChunkIndex]);
      this.moreChunks = res.more_chunks;
      this.loadedChunks = res.chunks;
    })

  }

  toggleFileSelection(file: File) {
    if (this.selectedFiles.has(file.id)) {
      this.selectedFiles.delete(file.id);
    } else {
      this.selectedFiles.add(file.id);
    }
  }

  isFileSelected(file: File): boolean {
    return this.selectedFiles.has(file.id);
  }

  onImportSubmit() {
    throw new Error('Method not implemented.');
  }
}
