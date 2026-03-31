import { ChangeDetectionStrategy, Component, Inject, OnInit, ChangeDetectorRef, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatListModule } from '@angular/material/list';
import { MatError, MatFormField, MatLabel } from '@angular/material/form-field';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { SummariesService, Summary, SummaryType } from '../../client';
import { MatInput } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatIconModule } from '@angular/material/icon';
import { UntilDestroy, untilDestroyed } from '@ngneat/until-destroy';
import { TestIds } from '../../testing/test-ids';

@UntilDestroy()
@Component({
  selector: 'app-summary-dialog',
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
    MatTooltipModule,
    MatIconModule
  ],
  templateUrl: './summary-dialog.component.html',
  styleUrls: ['./summary-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SummaryDialogComponent implements OnInit {
  protected readonly TestIds = TestIds;

  summaries: Summary[] = [];
  selectedSummary = signal<Summary | null>(null);
  isLoading = true;
  error: string | null = null;
  
  summaryForm!: FormGroup;
  isEditing = false;
  isAdding = false;

  constructor(
    public dialogRef: MatDialogRef<SummaryDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { 
        collectionName: string, 
        collectionId: string 
    },
    private formBuilder: FormBuilder,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.initForm();
    this.loadSummaries();
  }

  initForm(): void {
    this.summaryForm = this.formBuilder.group({
      type: [0, Validators.required],
      summary: ['', Validators.required],
      title: ['']
    });
  }

  loadSummaries(): void {
    this.isLoading = true;
    this.error = null;
    SummariesService.listSummariesByCollectionSummariesCollectionCollectionIdGet(this.data.collectionId)
      .then((summaries: Summary[]) => {
        this.summaries = summaries;
        this.isLoading = false;
        if (this.summaries.length > 0 && !this.selectedSummary()) {
          this.onSummarySelected(this.summaries[0]);
        }
        this.cdr.markForCheck();
      })
      .catch((err: any) => {
        this.error = 'Failed to load summaries.';
        this.isLoading = false;
        this.cdr.markForCheck();
      });
  }

  onSummarySelected(summary: Summary): void {
    this.selectedSummary.set(summary);
    this.isEditing = false;
    this.isAdding = false;
  }

  onAdd(): void {
    this.isAdding = true;
    this.isEditing = false;
    this.selectedSummary.set(null);
    this.summaryForm.reset({ type: 0, summary: '', title: '' });
  }

  onEdit(): void {
    const current = this.selectedSummary();
    if (!current) return;

    this.isEditing = true;
    this.isAdding = false;
    
    let title = '';
    try {
      if (current.metadata) {
        const meta = JSON.parse(current.metadata);
        title = meta.title || '';
      }
    } catch (e) {
      title = current.metadata || '';
    }

    this.summaryForm.patchValue({
      type: current.type,
      summary: current.summary,
      title: title
    });
  }

  onDelete(): void {
    const current = this.selectedSummary();
    if (!current) return;

    if (confirm('Are you sure you want to delete this summary?')) {
      SummariesService.deleteExistingSummarySummariesSummaryIdDelete(current.id)
        .then(() => {
          this.selectedSummary.set(null);
          this.loadSummaries();
        })
        .catch((err: any) => {
          alert('Failed to delete summary.');
        });
    }
  }

  onSave(): void {
    if (this.summaryForm.invalid) return;

    const formValue = this.summaryForm.value;
    const metadata = JSON.stringify({ title: formValue.title });

    if (this.isAdding) {
      SummariesService.createNewSummarySummariesPost({
        collection_id: this.data.collectionId,
        type: formValue.type,
        summary: formValue.summary,
        metadata: metadata
      })
        .then((newSummary: Summary) => {
          this.isAdding = false;
          this.loadSummaries();
        })
        .catch((err: any) => {
          alert('Failed to add summary.');
        });
    } else if (this.isEditing && this.selectedSummary()) {
      SummariesService.updateExistingSummarySummariesSummaryIdPut(this.selectedSummary()!.id, {
        type: formValue.type,
        summary: formValue.summary,
        metadata: metadata
      })
        .then((updatedSummary: Summary) => {
          this.isEditing = false;
          this.loadSummaries();
        })
        .catch((err: any) => {
          alert('Failed to update summary.');
        });
    }
  }

  onCancelEdit(): void {
    this.isEditing = false;
    this.isAdding = false;
    if (this.summaries.length > 0) {
        this.onSummarySelected(this.summaries[0]);
    }
  }

  getLevelName(type: number): string {
    switch (type) {
      case 0: return 'CHUNK';
      case 1: return 'CHAPTER';
      case 2: return 'BOOK';
      case 3: return 'TOC';
      default: return 'LEVEL ' + type;
    }
  }

  getSummaryTitle(summary: Summary): string {
    try {
      if (summary.metadata) {
        const meta = JSON.parse(summary.metadata);
        return meta.title || 'Summary ' + summary.id;
      }
    } catch (e) {}
    return summary.metadata || 'Summary ' + summary.id;
  }

  onClose(): void {
    this.dialogRef.close();
  }
}
