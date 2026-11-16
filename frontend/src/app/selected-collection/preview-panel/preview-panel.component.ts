import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output,
  computed,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { File, FileImportSettings, FilesService, ImportService } from '../../client';
import { TestIds } from '../../testing/test-ids';
import { UrlPartsPipe } from './url-parts.pipe';

@Component({
  selector: 'app-preview-panel',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatCheckboxModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSelectModule,
    MatTooltipModule,
    UrlPartsPipe,
  ],
  templateUrl: './preview-panel.component.html',
  styleUrl: './preview-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PreviewPanelComponent implements OnInit {
  protected readonly TestIds = TestIds;

  @Input({ required: true }) collectionId!: string;
  @Input() collectionName: string | undefined;
  @Input() model: string | undefined;
  @Input() settings: FileImportSettings | undefined;

  @Output() importRequest = new EventEmitter<any>();
  @Output() cancel = new EventEmitter<void>();

  chunkForm!: FormGroup;
  chunkTypes = signal<string[]>([]);

  files = signal<File[]>([]);
  selectedFiles = signal<Set<string>>(new Set<string>());
  selectedFile = signal<File | null>(null);
  searchTerm = signal('');
  isLoading = signal(true);
  error = signal<string | null>(null);
  chunk = signal('');
  moreChunks = false;
  currentChunkIndex = 0;
  loadedChunks: string[] = [];

  selectedCount = computed(() => this.selectedFiles().size);

  filteredFiles = computed(() => {
    const term = this.searchTerm().trim().toLowerCase();
    if (!term) {
      return this.files();
    }
    return this.files().filter(file => file.source.toLowerCase().includes(term));
  });

  allFilteredSelected = computed(() => {
    const filtered = this.filteredFiles();
    return filtered.length > 0 && filtered.every(file => this.selectedFiles().has(file.id));
  });

  someFilteredSelected = computed(() => {
    const filtered = this.filteredFiles();
    return filtered.some(file => this.selectedFiles().has(file.id)) && !this.allFilteredSelected();
  });

  private readonly take = 5;
  private skip = 0;

  constructor(private formBuilder: FormBuilder) {}

  ngOnInit(): void {
    this.chunkForm = this.formBuilder.group({
      model: [this.model ?? '', Validators.required],
      chunkSize: [this.settings?.chunk_size ?? 500, [Validators.required, Validators.min(1)]],
      chunkOverlap: [this.settings?.chunk_overlap ?? 50, [Validators.required, Validators.min(0)]],
      chunkType: ['RECURSIVE_CHARACTER', Validators.required],
      noChunks: [this.settings?.no_chunks ?? false],
    });

    this.chunkForm.get('model')?.disable();

    FilesService.readFilesFilesCollectionIdGet(this.collectionId)
      .then(files => {
        this.files.set(files);
        this.selectedFiles.set(new Set(files.map(file => file.id)));
        this.isLoading.set(false);
      })
      .catch(() => {
        this.error.set('Failed to load files.');
        this.isLoading.set(false);
      });

    ImportService.getChunkTypesImportChunktypesGet()
      .then(chunkTypes => {
        this.chunkTypes.set(chunkTypes);
        const currentType = this.chunkForm.get('chunkType')?.value;
        if (!chunkTypes.includes(currentType)) {
          this.chunkForm.get('chunkType')?.setValue(chunkTypes[0] ?? currentType);
        }
      })
      .catch(error => {
        console.error('Failed to load chunk types:', error);
      });
  }

  onCancel(): void {
    this.cancel.emit();
  }

  onImport(): void {
    if (this.selectedCount() === 0) {
      return;
    }

    this.importRequest.emit({
      ...this.chunkForm.getRawValue(),
      collectionId: this.collectionId,
      selectedFile: this.selectedFile(),
      selectedFiles: Array.from(this.selectedFiles()),
    });
  }

  onSearch(event: Event): void {
    this.searchTerm.set((event.target as HTMLInputElement).value);
  }

  clearSearch(): void {
    this.searchTerm.set('');
  }

  toggleFileSelection(file: File): void {
    this.selectedFiles.update(selected => {
      const next = new Set(selected);
      if (next.has(file.id)) {
        next.delete(file.id);
      } else {
        next.add(file.id);
      }
      return next;
    });
  }

  toggleSelectAll(checked: boolean): void {
    this.selectedFiles.update(selected => {
      const next = new Set(selected);
      for (const file of this.filteredFiles()) {
        if (checked) {
          next.add(file.id);
        } else {
          next.delete(file.id);
        }
      }
      return next;
    });
  }

  isFileSelected(file: File): boolean {
    return this.selectedFiles().has(file.id);
  }

  onFileSelected(file: File): void {
    this.selectedFile.set(file);
    this.skip = 0;
    this.updateChunks().then(() => {
      this.currentChunkIndex = 0;
      this.chunk.set(
        this.loadedChunks.length > 0
          ? this.loadedChunks[this.currentChunkIndex]
          : 'No chunks found.'
      );
    });
  }

  onNext(): void {
    if (this.currentChunkIndex < this.loadedChunks.length - 1) {
      this.currentChunkIndex++;
      this.chunk.set(this.loadedChunks[this.currentChunkIndex]);
    } else if (this.moreChunks) {
      this.skip += this.take;
      this.updateChunks().then(() => {
        this.currentChunkIndex = 0;
        if (this.loadedChunks.length > 0) {
          this.chunk.set(this.loadedChunks[this.currentChunkIndex]);
        }
      });
    }
  }

  onPrevious(): void {
    if (this.currentChunkIndex > 0) {
      this.currentChunkIndex--;
      this.chunk.set(this.loadedChunks[this.currentChunkIndex]);
    } else if (this.skip > 0) {
      this.skip -= this.take;
      this.updateChunks().then(() => {
        this.currentChunkIndex = this.loadedChunks.length - 1;
        if (this.loadedChunks.length > 0) {
          this.chunk.set(this.loadedChunks[this.currentChunkIndex]);
        }
      });
    }
  }

  onUpdateChunks(): void {
    if (!this.selectedFile()) {
      return;
    }
    this.skip = 0;
    this.updateChunks().then(() => {
      this.currentChunkIndex = 0;
      this.chunk.set(
        this.loadedChunks.length > 0
          ? this.loadedChunks[this.currentChunkIndex]
          : 'No chunks found.'
      );
    });
  }

  updateChunks(): Promise<void> {
    const file = this.selectedFile();
    if (!file) {
      return Promise.resolve();
    }

    return FilesService.getChunkPreviewFilesContentPost({
      file_id: file.id,
      chunk_type: this.chunkForm.get('chunkType')?.value ?? 'default',
      chunk_size: this.chunkForm.get('chunkSize')?.value ?? 500,
      chunk_overlap: this.chunkForm.get('chunkOverlap')?.value ?? 50,
      no_chunks: this.chunkForm.get('noChunks')?.value ?? false,
      take_number: this.take,
      skip_number: this.skip,
    }).then(res => {
      this.moreChunks = res.more_chunks;
      this.loadedChunks = res.chunks;
    });
  }
}
