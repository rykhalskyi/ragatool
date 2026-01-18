import { ChangeDetectionStrategy, Component, Inject, signal, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatListModule } from '@angular/material/list';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatTabsModule } from '@angular/material/tabs';
import { MatIconModule } from '@angular/material/icon';
import { CollectionsService, CollectionContentResponse, CollectionContentRequest, CollectionQueryResponse } from '../../client'; // Import CollectionsService and CollectionContentRequest

interface ChatMessage {
  sender: 'user' | 'bot';
  text: string;
}

@Component({
  selector: 'app-inspect-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatListModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatTabsModule,
    MatIconModule
  ],
  templateUrl: './inspect-dialog.component.html',
  styleUrls: ['./inspect-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InspectDialogComponent implements OnInit {

  chunk_id = signal<string>("");
  chunk = signal<string>("");
  totalPages = 0;
  loadedChunks: any[] = [];
  isLoading = true;
  error: string | null = null;
  
  queryForm!: FormGroup;
  messages = signal<ChatMessage[]>([]);
  botResponse = signal<string | null>(null);
  manyResponseDocuments = signal<boolean>(false);
  queryDocuments: any[] = [];
  currentDocumentIndex = 0;

  private page = 1; // Display one chunk at a time

  constructor(
    public dialogRef: MatDialogRef<InspectDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { collectionId: string },
    private cdr: ChangeDetectorRef,
    private formBuilder: FormBuilder // Inject FormBuilder
  ) {}

  ngOnInit(): void {
    this.updateChunks().then(() => {
      this.isLoading = false;
      this.setCurrentChunk(this.page - 1);
    }).catch((error: any) => {
       console.error(error);
        this.error = 'Failed to load chunks.';
        this.isLoading = false;
        this.cdr.markForCheck();
    });

    this.queryForm = this.formBuilder.group({
      query: ['', Validators.required]
    });
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  onNext() {
    if (this.page < this.loadedChunks.length) {
      this.page++;
      this.setCurrentChunk(this.page - 1);
    } else if (this.totalPages > this.page) {
      this.page ++;
      this.updateChunks().then(() => {
        this.setCurrentChunk(this.page - 1);
      });
    }
  }

  onPrevious() {
    if (this.page > 1) {
      this.page--;
      this.setCurrentChunk(this.page - 1);
    } 
  }

  private setCurrentChunk(index: number): void {
    const chunkObject = this.loadedChunks[index];
    if (chunkObject) {
      this.chunk.set(chunkObject.document);
      this.chunk_id.set(chunkObject.id);
    } else {
      this.chunk.set('No chunks found.');
    }
    this.cdr.markForCheck();
  }

  // Public getters for template access
  get currentPage(): number {
    return this.page;
  }

  get isFirstPage(): boolean {
    return this.page <= 1;
  }

  get isLastPageLoaded(): boolean {
    return this.page >= this.loadedChunks.length && this.totalPages <= this.page;
  }

  updateChunks(): Promise<void> {
    this.isLoading = true;
    this.error = null;
    const requestBody: CollectionContentRequest = {
        page: this.page,
        page_size: 1
    };
    return CollectionsService.readCollectionContentCollectionsCollectionIdContentPost(this.data.collectionId, requestBody)
      .then((res: CollectionContentResponse) => {
        this.totalPages = res.total_chunks;
        this.loadedChunks[this.page-1] = res.chunks[0];
      }).catch((error: any) => {
        this.error = 'Failed to load chunks.';
        console.error('Failed to load chunks:', error);
      }).finally(() => {
        this.isLoading = false;
        this.cdr.markForCheck();
      });
  }

  onQuerySubmit(): void {
    if (this.queryForm.invalid) {
      return;
    }

    const userQuery = this.queryForm.get('query')?.value;
    this.messages.set([{ sender: 'user', text: userQuery }]);
    this.botResponse.set(null);
    this.queryDocuments = [];
    this.currentDocumentIndex = 0;
    this.queryForm.reset();

    CollectionsService.queryCollectionEndpointCollectionsCollectionIdQueryGet(this.data.collectionId, userQuery)
      .then((response: CollectionQueryResponse) => {

        this.queryDocuments = response.results['documents'][0] || [];
        console.log('query res', this.queryDocuments, this.queryDocuments.length, this.queryDocuments[0], this.queryDocuments[1]);
        this.manyResponseDocuments.set(this.queryDocuments.length > 1);
        if (this.queryDocuments.length > 0) {
          this.currentDocumentIndex = 0;
          this.botResponse.set(this.queryDocuments[this.currentDocumentIndex]);
          console.log('bot', this.botResponse(), this.queryDocuments, this.manyResponseDocuments());
        } else {
          this.botResponse.set('No documents found in the response.');
        }
        this.cdr.markForCheck();
      })
      .catch((error: any) => {
        this.botResponse.set('Error: Failed to get response from the collection.');
        console.error('Query failed:', error);
        this.cdr.markForCheck();
      });
  }

  nextDocument(): void {
    if (this.currentDocumentIndex < this.queryDocuments.length - 1) {
      this.currentDocumentIndex++;
      this.botResponse.set(this.queryDocuments[this.currentDocumentIndex]);
    }
  }

  previousDocument(): void {
    if (this.currentDocumentIndex > 0) {
      this.currentDocumentIndex--;
      this.botResponse.set(this.queryDocuments[this.currentDocumentIndex]);
    }
  }
}
