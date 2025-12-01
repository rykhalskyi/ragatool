import { ChangeDetectionStrategy, Component, OnInit, Input, OnChanges, SimpleChanges, OnDestroy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule, MatSelectChange } from '@angular/material/select'; // Import MatSelectChange
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ImportService } from '../../client/services/ImportService';
import { Import } from '../../client/models/Import';

import { UntilDestroy, untilDestroyed } from '@ngneat/until-destroy';
import { ExtendedCollection } from '../selected-collection.component';
import { LogStreamService } from '../../log-stream.service';
import { TaskCachingService } from '../../task-caching.service';
import { Message } from '../../client/models/Message';
import { MatDialog } from '@angular/material/dialog';
import { FileImportDialog } from '../file-import-dialog/file-import-dialog';
import { Body_import_file_import__collection_id__post } from '../../client/models/Body_import_file_import__collection_id__post';
import { UrlImportDialog } from '../url-import-dialog/url-import-dialog';
import { Body_import_url_import_url__colletion_id__post } from '../../client/models/Body_import_url_import_url__colletion_id__post';

@Component({
  selector: 'app-selected-collection-import',
  standalone: true,
  imports: [
    CommonModule,
    MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    MatButtonModule,
    ReactiveFormsModule,
    MatProgressBarModule
  ],
  templateUrl: './selected-collection-import.component.html',
  styleUrl: './selected-collection-import.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})

@UntilDestroy()
export class SelectedCollectionImportComponent implements OnInit, OnChanges{
  @Input() collection: ExtendedCollection | undefined;

  importForm!: FormGroup;
  importTypes: Import[] = [];
  showProgressBar = signal(false);
  infoString = signal<string>("");

  constructor(
    private fb: FormBuilder,
    private logStreamService: LogStreamService,
    private taskCachingService: TaskCachingService,
    private dialog: MatDialog
  ) {}

  async ngOnInit(): Promise<void> {

    this.importForm = this.fb.group({
      importType: ['', Validators.required]
    });

    await this.getImportTypes();

    this.logStreamService.logs$
      .pipe(untilDestroyed(this))
      .subscribe((log: Message) => {
        if (log.collectionId === this.collection?.id) {
          this.infoString.set(log.message);
        }
      });

    this.taskCachingService
      .tasks$
      .pipe(untilDestroyed(this))
      .subscribe(tasks => {
        const task = tasks.find(i => i.collectionId === this.collection?.id);
        this.showProgressBar.set(task ? true : false);
      });

     if (this.collection?.saved && this.collection?.import_type)
     {
        const collectionImport: Import = {
          name : this.collection?.import_type,
          model: this.collection?.model!, 
          settings:  JSON.parse(this.collection!.settings!)
        }
        this.importForm.get('importType')?.setValue(collectionImport);
     }

  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['collection'] && this.collection && this.importForm) {
      const collectionId = this.collection.id;

      if (this.collectionIsSaved()) {
        this.importForm?.get('importType')?.disable({ emitEvent: false });
      } else {
        this.importForm.get('importType')?.enable({ emitEvent: false });
      }
     
      if (this.collectionIsSaved()) {
        const importType = this.importTypes.find(i => i.name === this.collection!.import_type);
        const initialState = {
          importType: importType,
          settings: this.collection!.settings
        };

        this.importForm.patchValue(initialState, { emitEvent: false });
      } else {

        this.importForm.reset({
          importType: '',
          settings: {}
        }, { emitEvent: false });

      }

      const task = this.taskCachingService.getTaskByCollectionId(this.collection.id);
      this.showProgressBar.set(task ? true : false);

      const info = this.logStreamService.getInfo(collectionId);
      if (info)
        this.infoString.set(info);

      this.importForm.markAsPristine();
      this.importForm.markAsUntouched();
      this.importForm.updateValueAndValidity({ emitEvent: false });

    }
  }


  async getImportTypes(): Promise<void> {
    try {
      const data = await ImportService.getImportsImportGet();
      this.importTypes = data;
    } 
    catch (e)
    {
        console.error('Error fetching import types:', e);
    }
    
  }

  onImportTypeChange(event: MatSelectChange): void {
    const selectedImportType: Import = event.value;
    this.importForm.get('importType')?.setValue(selectedImportType);
  }

  openSelectedImportDialog(): void {
    const selectedImportType = this.importForm.get('importType')?.value;

    if (selectedImportType && selectedImportType.name === 'FILE') {
      this.dialog.open(FileImportDialog, {
        data: {
          collectionName: this.collection?.name,
          collectionId: this.collection?.id,
          model: this.collectionIsSaved() ? this.collection!.model! : selectedImportType.model,
          settings: this.collectionIsSaved() ? JSON.parse(this.collection!.settings!) : selectedImportType.settings,
          saved: this.collection?.saved
        }
      }).afterClosed().subscribe(result => {
        if (result) {
          const formData: Body_import_file_import__collection_id__post = {
            file: result.selectedFile,
            import_params: JSON.stringify({
              name: selectedImportType.name,
              model: result.model,
              settings: {
                 chunk_size: result.chunkSize,
                 chunk_overlap: result.chunkOverlap,
                 no_chunks: false
              }
            })
          };

          ImportService.importFileImportCollectionIdPost(
            result.collectionId,
            formData
          ).then(
            (response: any) => {
              console.log('File imported successfully:', response);
            },
            (error: any) => {
              console.error('Error importing file:', error);
            }
          );
        }
      });
    }
    else if (selectedImportType && selectedImportType.name === 'URL'){
        this.dialog.open(UrlImportDialog, {
        data: {
          collectionName: this.collection?.name,
          collectionId: this.collection?.id,
          model: this.collectionIsSaved() ? this.collection!.model! : selectedImportType.model,
          settings: this.collectionIsSaved() ? JSON.parse(this.collection!.settings!) : selectedImportType.settings,
          saved: this.collection?.saved
        }}).afterClosed().subscribe(result =>{
          
          if (result) {
            const formData: Body_import_url_import_url__colletion_id__post = {
              import_params: JSON.stringify({
                name: selectedImportType.name,
                model: result.model,
                settings: {
                  chunk_size: result.chunkSize,
                  chunk_overlap: result.chunkOverlap,
                  no_chunks: false
                }
              })
            };
             
            ImportService.importUrlImportUrlColletionIdPost(
              result.collectionId,
              result.url,
              formData).then(
                (response: any) => {
                  console.log('Url imported successfully:', response);
                },
                (error: any) => {
                  console.error('Error importing Url:', error);
                }
              );
          }
        }
         
        );
    }
    else {
      console.log('Other import types are not yet implemented.');
    }
  }

  compareImportTypes(o1: Import, o2: Import): boolean {
    return o1 && o2 ? o1.name === o2.name : o1 === o2;
  }

  trackByImportType(index: number, item: Import): string {
    return item.name;
  }

  private collectionIsSaved(): boolean {
    return (this.collection?.saved) ?? false;
  }
}

